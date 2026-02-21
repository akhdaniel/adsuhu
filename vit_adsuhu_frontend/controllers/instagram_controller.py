import json
import logging
import re
import secrets
import time
from urllib.parse import urlencode

import requests
from odoo import http
from odoo.http import request

from .social_base import SocialControllerBase

_logger = logging.getLogger(__name__)


class InstagramController(SocialControllerBase):
    INSTAGRAM_TIMEOUT = 20
    INSTAGRAM_GRAPH_VERSION = "v19.0"

    def _instagram_config(self):
        params = request.env["ir.config_parameter"].sudo()
        base_url = (params.get_param("web.base.url") or "").rstrip("/")
        redirect_uri = params.get_param("instagram_redirect_uri")
        if not redirect_uri and base_url:
            redirect_uri = f"{base_url}/instagram/oauth/callback"
        return {
            "client_id": params.get_param("instagram_client_id") or params.get_param("facebook_client_id"),
            "client_secret": params.get_param("instagram_client_secret") or params.get_param("facebook_client_secret"),
            "redirect_uri": redirect_uri,
            "graph_version": params.get_param("instagram_graph_version") or self.INSTAGRAM_GRAPH_VERSION,
        }

    def _instagram_user_token_key(self, uid):
        return f"instagram_user_access_token_{uid}"

    def _instagram_user_token_expiry_key(self, uid):
        return f"instagram_user_access_token_expiry_{uid}"

    def _clear_user_instagram_token(self, uid):
        params = request.env["ir.config_parameter"].sudo()
        params.set_param(self._instagram_user_token_key(uid), "")
        params.set_param(self._instagram_user_token_expiry_key(uid), "")

    def _get_user_instagram_token(self, uid):
        params = request.env["ir.config_parameter"].sudo()
        token = params.get_param(self._instagram_user_token_key(uid))
        if not token:
            return None
        expiry_raw = params.get_param(self._instagram_user_token_expiry_key(uid))
        if expiry_raw:
            try:
                if int(expiry_raw) <= int(time.time()):
                    self._clear_user_instagram_token(uid)
                    return None
            except Exception:
                pass
        return token

    def _instagram_graph_get(self, path, query=None):
        cfg = self._instagram_config()
        url = f"https://graph.facebook.com/{cfg['graph_version']}/{path.lstrip('/')}"
        response = requests.get(url, params=query or {}, timeout=self.INSTAGRAM_TIMEOUT)
        try:
            data = response.json()
        except Exception:
            data = {"error": {"message": response.text or "Unknown Instagram error"}}
        return response, data

    def _instagram_graph_post(self, path, payload=None):
        cfg = self._instagram_config()
        url = f"https://graph.facebook.com/{cfg['graph_version']}/{path.lstrip('/')}"
        response = requests.post(url, data=payload or {}, timeout=self.INSTAGRAM_TIMEOUT)
        try:
            data = response.json()
        except Exception:
            data = {"error": {"message": response.text or "Unknown Instagram error"}}
        return response, data

    def _instagram_error_message(self, data, fallback="Instagram request failed."):
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                return err.get("message") or fallback
        return fallback

    def _is_instagram_token_invalid(self, data):
        if not isinstance(data, dict):
            return False
        err = data.get("error")
        if not isinstance(err, dict):
            return False
        code = err.get("code")
        subcode = err.get("error_subcode")
        return code in (190, 102) or subcode in (463, 467)

    def _instagram_auth_required_payload(self, return_url, force_login=False, reason=None):
        safe_return = self._safe_local_url(return_url, "/product_analysis")
        auth_url = self._append_query_params(
            "/instagram/oauth/start",
            {
                "next": safe_return,
                "force_login": "1" if force_login else None,
            },
        )
        payload = {"auth_required": True, "auth_url": auth_url}
        if reason:
            payload["reason"] = reason
        return payload

    def _instagram_accounts_payload(self, user_token):
        response, data = self._instagram_graph_get(
            "/me/accounts",
            {
                "access_token": user_token,
                "fields": "id,name,access_token,instagram_business_account{id,username,name}",
            },
        )
        if response.status_code >= 400 or data.get("error"):
            raise ValueError(self._instagram_error_message(data, "Failed to fetch Instagram accounts."))
        accounts = []
        for page in data.get("data") or []:
            ig = page.get("instagram_business_account") or {}
            ig_user_id = str(ig.get("id") or "").strip()
            if not ig_user_id:
                continue
            accounts.append(
                {
                    "page_id": str(page.get("id") or "").strip(),
                    "page_name": page.get("name") or "",
                    "ig_user_id": ig_user_id,
                    "ig_username": ig.get("username") or ig.get("name") or ig_user_id,
                }
            )
        return accounts

    def _get_instagram_page_token(self, user_token, page_id):
        response, data = self._instagram_graph_get(
            "/me/accounts",
            {"access_token": user_token, "fields": "id,access_token"},
        )
        if response.status_code >= 400 or data.get("error"):
            raise ValueError(self._instagram_error_message(data, "Failed to get page token for Instagram."))
        for page in data.get("data") or []:
            if str(page.get("id")) == str(page_id):
                token = page.get("access_token")
                if token:
                    return token
        raise ValueError("Page token not found for selected Instagram account.")

    @http.route("/instagram/oauth/start", type="http", auth="user", website=True)
    def instagram_oauth_start(self, **kwargs):
        cfg = self._instagram_config()
        if not cfg["client_id"] or not cfg["client_secret"] or not cfg["redirect_uri"]:
            return request.make_response("Instagram OAuth is not configured.", status=500)

        next_url = self._safe_local_url(kwargs.get("next"), "/product_analysis")
        force_login = str(kwargs.get("force_login") or "").lower() in ("1", "true", "yes")
        popup_mode = str(kwargs.get("popup") or "").lower() in ("1", "true", "yes")
        if force_login:
            self._clear_user_instagram_token(request.env.uid)

        state = secrets.token_urlsafe(24)
        request.session["instagram_oauth_state"] = state
        request.session["instagram_oauth_next"] = next_url
        request.session["instagram_oauth_popup"] = popup_mode

        auth_params = {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "state": state,
            "scope": "pages_show_list,instagram_basic,instagram_content_publish,business_management",
            "response_type": "code",
        }
        if force_login:
            auth_params["auth_type"] = "rerequest"
        auth_url = f"https://www.facebook.com/{cfg['graph_version']}/dialog/oauth?{urlencode(auth_params)}"
        return request.redirect(auth_url, local=False)

    @http.route("/instagram/oauth/callback", type="http", auth="user", website=True, csrf=False)
    def instagram_oauth_callback(self, **kwargs):
        cfg = self._instagram_config()
        redirect_target = self._safe_local_url(request.session.pop("instagram_oauth_next", "/product_analysis"))
        popup_mode = bool(request.session.pop("instagram_oauth_popup", False))
        received_state = kwargs.get("state") or request.params.get("state") or request.httprequest.args.get("state")
        expected_state = request.session.pop("instagram_oauth_state", None)

        def _popup_response(success, error_message=""):
            payload = {"type": "instagram_oauth_result", "success": bool(success), "error": error_message or ""}
            html = f"""
<!doctype html>
<html><body>
<script>
try {{
    if (window.opener && !window.opener.closed) {{
        window.opener.postMessage({json.dumps(payload)}, window.location.origin);
    }}
}} catch (e) {{}}
window.close();
</script>
</body></html>
"""
            return request.make_response(html, headers=[("Content-Type", "text/html; charset=utf-8")])

        if not expected_state:
            if popup_mode:
                return _popup_response(False, "missing_expected_state")
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": "missing_expected_state"}))
        if not received_state:
            if popup_mode:
                return _popup_response(False, "missing_state")
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": "missing_state"}))
        if expected_state != received_state:
            if popup_mode:
                return _popup_response(False, "invalid_state")
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": "invalid_state"}))
        if kwargs.get("error"):
            message = kwargs.get("error_description") or kwargs.get("error")
            if popup_mode:
                return _popup_response(False, message)
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": message}))

        code = kwargs.get("code")
        if not code:
            if popup_mode:
                return _popup_response(False, "missing_code")
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": "missing_code"}))

        try:
            response = requests.get(
                f"https://graph.facebook.com/{cfg['graph_version']}/oauth/access_token",
                params={
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                    "redirect_uri": cfg["redirect_uri"],
                    "code": code,
                },
                timeout=self.INSTAGRAM_TIMEOUT,
            )
            data = response.json()
        except Exception as exc:
            _logger.exception("Instagram token exchange failed")
            if popup_mode:
                return _popup_response(False, str(exc))
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": str(exc)}))

        if response.status_code >= 400 or data.get("error"):
            message = self._instagram_error_message(data, "Instagram token exchange failed.")
            if popup_mode:
                return _popup_response(False, message)
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": message}))

        access_token = data.get("access_token")
        if not access_token:
            if popup_mode:
                return _popup_response(False, "missing_access_token")
            return request.redirect(self._append_query_params(redirect_target, {"ig_error": "missing_access_token"}))

        params = request.env["ir.config_parameter"].sudo()
        uid = request.env.uid
        params.set_param(self._instagram_user_token_key(uid), access_token)
        expires_in = int(data.get("expires_in") or 0)
        if expires_in > 0:
            params.set_param(self._instagram_user_token_expiry_key(uid), str(int(time.time()) + expires_in))
        else:
            params.set_param(self._instagram_user_token_expiry_key(uid), "")

        if popup_mode:
            return _popup_response(True, "")
        return request.redirect(self._append_query_params(redirect_target, {"ig_connected": "1"}))

    @http.route("/instagram/accounts", type="json", auth="user", website=True, methods=["POST"])
    def instagram_accounts(self, return_url=None, **kwargs):
        user_token = self._get_user_instagram_token(request.env.uid)
        if not user_token:
            return self._instagram_auth_required_payload(return_url, reason="missing_token")
        try:
            accounts = self._instagram_accounts_payload(user_token)
            if not accounts:
                return {"auth_required": False, "accounts": [], "error": "No Instagram Business account linked to this Facebook account/page."}
            return {"auth_required": False, "accounts": accounts}
        except Exception as exc:
            message = str(exc) or "Failed to fetch Instagram accounts."
            if "error validating access token" in message.lower() or "session has expired" in message.lower():
                self._clear_user_instagram_token(request.env.uid)
                return self._instagram_auth_required_payload(return_url, force_login=True, reason="token_invalid")
            return {"auth_required": False, "accounts": [], "error": message}

    @http.route("/instagram/disconnect", type="json", auth="user", website=True, methods=["POST"])
    def instagram_disconnect(self, **kwargs):
        try:
            self._clear_user_instagram_token(request.env.uid)
            return {"success": True, "connected": False}
        except Exception as exc:
            return {"success": False, "error": str(exc) or "Failed to disconnect Instagram account."}

    @http.route("/instagram/post_image", type="json", auth="user", website=True, methods=["POST"])
    def instagram_post_image(self, image_url=None, ig_user_id=None, page_id=None, caption=None, return_url=None, **kwargs):
        json_payload = request.httprequest.get_json(silent=True) or {}
        if not isinstance(json_payload, dict):
            json_payload = {}
        nested_params = json_payload.get("params") if isinstance(json_payload.get("params"), dict) else {}

        image_url = (image_url or kwargs.get("image_url") or json_payload.get("image_url") or nested_params.get("image_url") or "").strip()
        ig_user_id = (ig_user_id or kwargs.get("ig_user_id") or json_payload.get("ig_user_id") or nested_params.get("ig_user_id") or "").strip()
        page_id = (page_id or kwargs.get("page_id") or json_payload.get("page_id") or nested_params.get("page_id") or "").strip()
        caption = (caption or kwargs.get("caption") or json_payload.get("caption") or nested_params.get("caption") or "").strip()
        caption = re.sub(r"<[^>]+>", "", caption or "").strip()
        return_url = return_url or kwargs.get("return_url") or json_payload.get("return_url") or nested_params.get("return_url") or ""

        if not image_url:
            return {"error": "Image URL is required."}
        if not ig_user_id:
            return {"error": "Instagram account is required."}
        if not page_id:
            return {"error": "Facebook page is required for Instagram publishing."}

        user_token = self._get_user_instagram_token(request.env.uid)
        if not user_token:
            return self._instagram_auth_required_payload(return_url)

        try:
            page_token = self._get_instagram_page_token(user_token, page_id)
            resp_create, data_create = self._instagram_graph_post(
                f"/{ig_user_id}/media",
                {"access_token": page_token, "image_url": image_url, "caption": caption},
            )
            if resp_create.status_code >= 400 or data_create.get("error"):
                if self._is_instagram_token_invalid(data_create):
                    self._clear_user_instagram_token(request.env.uid)
                    return self._instagram_auth_required_payload(return_url, force_login=True, reason="token_invalid")
                return {"error": self._instagram_error_message(data_create, "Failed to create Instagram media container.")}

            creation_id = data_create.get("id")
            if not creation_id:
                return {"error": "Instagram container creation failed."}

            resp_publish, data_publish = self._instagram_graph_post(
                f"/{ig_user_id}/media_publish",
                {"access_token": page_token, "creation_id": creation_id},
            )
            if resp_publish.status_code >= 400 or data_publish.get("error"):
                if self._is_instagram_token_invalid(data_publish):
                    self._clear_user_instagram_token(request.env.uid)
                    return self._instagram_auth_required_payload(return_url, force_login=True, reason="token_invalid")
                return {"error": self._instagram_error_message(data_publish, "Failed to publish Instagram post.")}
            return {"success": True, "post_id": data_publish.get("id")}
        except Exception as exc:
            _logger.exception("Instagram publish failed")
            return {"error": str(exc) or "Failed to post image to Instagram."}
