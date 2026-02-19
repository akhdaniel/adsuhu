import json
import logging
import secrets
import time
from urllib.parse import urlencode

import requests
from odoo import http
from odoo.http import request

from .social_base import SocialControllerBase

_logger = logging.getLogger(__name__)


class FacebookController(SocialControllerBase):
    FACEBOOK_TIMEOUT = 20
    FACEBOOK_GRAPH_VERSION = "v19.0"

    def _facebook_config(self):
        params = request.env["ir.config_parameter"].sudo()
        base_url = (params.get_param("web.base.url") or "").rstrip("/")
        redirect_uri = params.get_param("facebook_redirect_uri")
        if not redirect_uri and base_url:
            redirect_uri = f"{base_url}/facebook/oauth/callback"
        return {
            "client_id": params.get_param("facebook_client_id"),
            "client_secret": params.get_param("facebook_client_secret"),
            "redirect_uri": redirect_uri,
            "graph_version": params.get_param("facebook_graph_version") or self.FACEBOOK_GRAPH_VERSION,
        }

    def _facebook_user_token_key(self, uid):
        return f"facebook_user_access_token_{uid}"

    def _facebook_user_token_expiry_key(self, uid):
        return f"facebook_user_access_token_expiry_{uid}"

    def _clear_user_facebook_token(self, uid):
        params = request.env["ir.config_parameter"].sudo()
        params.set_param(self._facebook_user_token_key(uid), "")
        params.set_param(self._facebook_user_token_expiry_key(uid), "")

    def _get_user_facebook_token(self, uid):
        params = request.env["ir.config_parameter"].sudo()
        token = params.get_param(self._facebook_user_token_key(uid))
        if not token:
            return None
        expiry_raw = params.get_param(self._facebook_user_token_expiry_key(uid))
        if expiry_raw:
            try:
                if int(expiry_raw) <= int(time.time()):
                    self._clear_user_facebook_token(uid)
                    return None
            except Exception:
                pass
        return token

    def _facebook_graph_get(self, path, query=None):
        cfg = self._facebook_config()
        graph_version = cfg["graph_version"]
        url = f"https://graph.facebook.com/{graph_version}/{path.lstrip('/')}"
        response = requests.get(url, params=query or {}, timeout=self.FACEBOOK_TIMEOUT)
        try:
            data = response.json()
        except Exception:
            data = {"error": {"message": response.text or "Unknown Facebook error"}}
        return response, data

    def _facebook_graph_post(self, path, payload=None):
        cfg = self._facebook_config()
        graph_version = cfg["graph_version"]
        url = f"https://graph.facebook.com/{graph_version}/{path.lstrip('/')}"
        response = requests.post(url, data=payload or {}, timeout=self.FACEBOOK_TIMEOUT)
        try:
            data = response.json()
        except Exception:
            data = {"error": {"message": response.text or "Unknown Facebook error"}}
        return response, data

    def _facebook_error_message(self, data, fallback="Facebook request failed."):
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                return err.get("message") or fallback
        return fallback

    def _is_facebook_token_invalid(self, data):
        if not isinstance(data, dict):
            return False
        err = data.get("error")
        if not isinstance(err, dict):
            return False
        code = err.get("code")
        subcode = err.get("error_subcode")
        return code in (190, 102) or subcode in (463, 467)

    def _facebook_pages_payload(self, user_token):
        response, data = self._facebook_graph_get(
            "/me/accounts",
            {
                "access_token": user_token,
                "fields": "id,name,category",
            },
        )
        if response.status_code >= 400 or data.get("error"):
            raise ValueError(self._facebook_error_message(data, "Failed to fetch Facebook pages."))
        pages = data.get("data") or []
        return [{"id": p.get("id"), "name": p.get("name"), "category": p.get("category")} for p in pages if p.get("id")]

    def _facebook_permissions_payload(self, user_token):
        response, data = self._facebook_graph_get(
            "/me/permissions",
            {
                "access_token": user_token,
            },
        )
        if response.status_code >= 400 or data.get("error"):
            return {}
        granted = {
            item.get("permission")
            for item in (data.get("data") or [])
            if item.get("status") == "granted" and item.get("permission")
        }
        required = {"pages_show_list", "pages_manage_posts", "pages_read_engagement", "pages_manage_metadata"}
        missing = sorted(required - granted)
        return {
            "granted": sorted(granted),
            "missing": missing,
        }

    def _facebook_me_payload(self, user_token):
        response, data = self._facebook_graph_get(
            "/me",
            {
                "access_token": user_token,
                "fields": "id,name",
            },
        )
        if response.status_code >= 400 or data.get("error"):
            return {}
        return {"id": data.get("id"), "name": data.get("name")}

    def _get_facebook_page_token(self, user_token, page_id):
        response, data = self._facebook_graph_get(
            "/me/accounts",
            {
                "access_token": user_token,
                "fields": "id,access_token",
            },
        )
        if response.status_code >= 400 or data.get("error"):
            raise ValueError(self._facebook_error_message(data, "Failed to get Facebook page token."))
        token = None
        for page in data.get("data") or []:
            if str(page.get("id")) == str(page_id):
                token = page.get("access_token")
                break
        if not token:
            raise ValueError("Facebook page token not found.")
        return token

    def _facebook_auth_required_payload(self, return_url, force_login=False, reason=None):
        safe_return = self._safe_local_url(return_url, "/product_analysis")
        auth_url = self._append_query_params(
            "/facebook/oauth/start",
            {
                "next": safe_return,
                "force_login": "1" if force_login else None,
            },
        )
        payload = {
            "auth_required": True,
            "auth_url": auth_url,
        }
        if reason:
            payload["reason"] = reason
        return payload

    @http.route('/facebook/oauth/start', type='http', auth='user', website=True)
    def facebook_oauth_start(self, **kwargs):
        cfg = self._facebook_config()
        if not cfg["client_id"] or not cfg["client_secret"] or not cfg["redirect_uri"]:
            return request.make_response("Facebook OAuth is not configured.", status=500)

        next_url = self._safe_local_url(kwargs.get("next"), "/product_analysis")
        force_login = str(kwargs.get("force_login") or "").lower() in ("1", "true", "yes")
        popup_mode = str(kwargs.get("popup") or "").lower() in ("1", "true", "yes")
        if force_login:
            self._clear_user_facebook_token(request.env.uid)

        state = secrets.token_urlsafe(24)
        request.session["facebook_oauth_state"] = state
        request.session["facebook_oauth_next"] = next_url
        request.session["facebook_oauth_popup"] = popup_mode

        auth_params = {
            "client_id": cfg["client_id"],
            "redirect_uri": cfg["redirect_uri"],
            "state": state,
            "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,pages_manage_metadata",
            "response_type": "code",
        }
        if force_login:
            auth_params["auth_type"] = "rerequest"
        auth_url = f"https://www.facebook.com/{cfg['graph_version']}/dialog/oauth?{urlencode(auth_params)}"
        return request.redirect(auth_url, local=False)

    @http.route('/facebook/oauth/callback', type='http', auth='user', website=True, csrf=False)
    def facebook_oauth_callback(self, **kwargs):
        _logger.error(f"/facebook/oauth/callback >> kwargs={kwargs}")
        cfg = self._facebook_config()
        redirect_target = self._safe_local_url(request.session.pop("facebook_oauth_next", "/product_analysis"))
        popup_mode = bool(request.session.pop("facebook_oauth_popup", False))
        received_state = kwargs.get("state")
        expected_state = request.session.pop("facebook_oauth_state", None)

        def _popup_response(success, error_message=""):
            payload = {"type": "facebook_oauth_result", "success": bool(success), "error": error_message or ""}
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
            return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])

        if not expected_state or expected_state != received_state:
            if popup_mode:
                return _popup_response(False, "invalid_state")
            return request.redirect(self._append_query_params(redirect_target, {"fb_error": "invalid_state"}))

        if kwargs.get("error"):
            if popup_mode:
                return _popup_response(False, kwargs.get("error_description") or kwargs.get("error"))
            return request.redirect(
                self._append_query_params(
                    redirect_target,
                    {"fb_error": kwargs.get("error_description") or kwargs.get("error")},
                )
            )

        code = kwargs.get("code")
        if not code:
            if popup_mode:
                return _popup_response(False, "missing_code")
            return request.redirect(self._append_query_params(redirect_target, {"fb_error": "missing_code"}))

        try:
            response = requests.get(
                f"https://graph.facebook.com/{cfg['graph_version']}/oauth/access_token",
                params={
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                    "redirect_uri": cfg["redirect_uri"],
                    "code": code,
                },
                timeout=self.FACEBOOK_TIMEOUT,
            )
            data = response.json()
            _logger.info(f"/facebook/oauth/callback => data={data}")
        except Exception as exc:
            _logger.exception("Facebook token exchange failed")
            if popup_mode:
                return _popup_response(False, str(exc))
            return request.redirect(self._append_query_params(redirect_target, {"fb_error": str(exc)}))

        if response.status_code >= 400 or data.get("error"):
            message = self._facebook_error_message(data, "Facebook token exchange failed.")
            if popup_mode:
                return _popup_response(False, message)
            return request.redirect(self._append_query_params(redirect_target, {"fb_error": message}))

        access_token = data.get("access_token")
        if not access_token:
            if popup_mode:
                return _popup_response(False, "missing_access_token")
            return request.redirect(self._append_query_params(redirect_target, {"fb_error": "missing_access_token"}))

        params = request.env["ir.config_parameter"].sudo()
        uid = request.env.uid
        params.set_param(self._facebook_user_token_key(uid), access_token)
        expires_in = int(data.get("expires_in") or 0)
        if expires_in > 0:
            params.set_param(self._facebook_user_token_expiry_key(uid), str(int(time.time()) + expires_in))
        else:
            params.set_param(self._facebook_user_token_expiry_key(uid), "")

        if popup_mode:
            return _popup_response(True, "")
        return request.redirect(self._append_query_params(redirect_target, {"fb_connected": "1"}))

    @http.route('/facebook/pages', type='json', auth='user', website=True, methods=['POST'])
    def facebook_pages(self, return_url=None, **kwargs):
        user_token = self._get_user_facebook_token(request.env.uid)
        if not user_token:
            return self._facebook_auth_required_payload(return_url, reason="missing_token")
        try:
            pages = self._facebook_pages_payload(user_token)
            if not pages:
                permission_info = self._facebook_permissions_payload(user_token)
                me_info = self._facebook_me_payload(user_token)
                missing = permission_info.get("missing") or []
                message = "Tidak ada Facebook Page yang bisa diakses akun ini."
                if missing:
                    message = f"{message} Missing permissions: {', '.join(missing)}"
                elif permission_info.get("granted"):
                    message = (
                        f"{message} Granted permissions: {', '.join(permission_info.get('granted') or [])}. "
                        "Cek apakah akun ini punya akses task/admin ke Page di Business Suite."
                    )
                if me_info.get("id"):
                    message = f"{message} (Logged as: {me_info.get('name') or '-'} / {me_info.get('id')})"
                return {
                    "auth_required": False,
                    "pages": [],
                    "error": message,
                    "permission_info": permission_info,
                    "me": me_info,
                }
            return {"auth_required": False, "pages": pages}
        except Exception as exc:
            _logger.warning("Failed to fetch Facebook pages: %s", exc)
            message = str(exc) or "Failed to fetch Facebook pages."
            lowered = message.lower()
            if "error validating access token" in lowered or "session has expired" in lowered:
                self._clear_user_facebook_token(request.env.uid)
                return self._facebook_auth_required_payload(return_url, force_login=True, reason="token_invalid")
            return {"auth_required": False, "pages": [], "error": message}

    @http.route('/facebook/post_image', type='json', auth='user', website=True, methods=['POST'])
    def facebook_post_image(self, image_url=None, page_id=None, message=None, return_url=None, **kwargs):
        image_url = (image_url or "").strip()
        page_id = (page_id or "").strip()
        message = (message or "").strip()
        if not image_url:
            return {"error": "Image URL is required."}
        if not page_id:
            return {"error": "Facebook Page is required."}

        user_token = self._get_user_facebook_token(request.env.uid)
        if not user_token:
            return self._facebook_auth_required_payload(return_url)

        try:
            page_token = self._get_facebook_page_token(user_token, page_id)
            response, data = self._facebook_graph_post(
                f"/{page_id}/photos",
                {
                    "access_token": page_token,
                    "url": image_url,
                    "caption": message,
                },
            )
            if response.status_code >= 400 or data.get("error"):
                if self._is_facebook_token_invalid(data):
                    self._clear_user_facebook_token(request.env.uid)
                    return self._facebook_auth_required_payload(return_url)
                return {"error": self._facebook_error_message(data, "Failed to post image to Facebook.")}
            return {"success": True, "post_id": data.get("post_id") or data.get("id")}
        except Exception as exc:
            _logger.exception("Facebook page post failed")
            return {"error": str(exc) or "Failed to post image to Facebook."}

    @http.route('/facebook/debug_accounts', type='json', auth='user', website=True, methods=['POST'])
    def facebook_debug_accounts(self, **kwargs):
        user_token = self._get_user_facebook_token(request.env.uid)
        if not user_token:
            return {"error": "Facebook token not found for this user.", "auth_required": True}

        me_resp, me_data = self._facebook_graph_get(
            "/me",
            {
                "access_token": user_token,
                "fields": "id,name",
            },
        )
        perm_resp, perm_data = self._facebook_graph_get(
            "/me/permissions",
            {
                "access_token": user_token,
            },
        )
        accounts_resp, accounts_data = self._facebook_graph_get(
            "/me/accounts",
            {
                "access_token": user_token,
                "fields": "id,name,category,tasks,access_token",
            },
        )

        def _mask_token(token_value):
            if not token_value:
                return ""
            token_value = str(token_value)
            if len(token_value) <= 8:
                return "****"
            return f"{token_value[:4]}...{token_value[-4:]}"

        for page in (accounts_data.get("data") or []):
            if page.get("access_token"):
                page["access_token"] = _mask_token(page["access_token"])

        return {
            "token_present": True,
            "token_preview": _mask_token(user_token),
            "me_status": me_resp.status_code,
            "me": me_data,
            "permissions_status": perm_resp.status_code,
            "permissions": perm_data,
            "accounts_status": accounts_resp.status_code,
            "accounts": accounts_data,
        }
