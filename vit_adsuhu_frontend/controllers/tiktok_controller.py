import json
import logging
import re
import secrets
import time
import base64
from io import BytesIO
from urllib.parse import urlparse

import requests
from odoo import http
from odoo.http import request
from PIL import Image

from .social_base import SocialControllerBase

_logger = logging.getLogger(__name__)


class TikTokController(SocialControllerBase):
    TIKTOK_TIMEOUT = 20

    def _tiktok_config(self):
        params = request.env["ir.config_parameter"].sudo()
        base_url = (params.get_param("web.base.url") or "").rstrip("/")
        redirect_uri = params.get_param("tiktok_redirect_uri")
        if not redirect_uri and base_url:
            redirect_uri = f"{base_url}/tiktok/oauth/callback"
        return {
            "client_key": params.get_param("tiktok_client_key"),
            "client_secret": params.get_param("tiktok_client_secret"),
            "redirect_uri": redirect_uri,
            "scope": params.get_param("tiktok_scope") or "user.info.basic,video.publish",
            "api_base": (params.get_param("tiktok_api_base") or "https://open.tiktokapis.com").rstrip("/"),
        }

    def _tiktok_user_token_key(self, uid):
        return f"tiktok_user_access_token_{uid}"

    def _tiktok_user_token_expiry_key(self, uid):
        return f"tiktok_user_access_token_expiry_{uid}"

    def _clear_user_tiktok_token(self, uid):
        params = request.env["ir.config_parameter"].sudo()
        params.set_param(self._tiktok_user_token_key(uid), "")
        params.set_param(self._tiktok_user_token_expiry_key(uid), "")

    def _get_user_tiktok_token(self, uid):
        params = request.env["ir.config_parameter"].sudo()
        token = params.get_param(self._tiktok_user_token_key(uid))
        if not token:
            return None
        expiry_raw = params.get_param(self._tiktok_user_token_expiry_key(uid))
        if expiry_raw:
            try:
                if int(expiry_raw) <= int(time.time()):
                    self._clear_user_tiktok_token(uid)
                    return None
            except Exception:
                pass
        return token

    def _tiktok_parse_response(self, response, default_error="TikTok request failed."):
        try:
            data = response.json()
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}
        if response.status_code >= 400:
            err_payload = data.get("error") if isinstance(data.get("error"), dict) else {}
            message = (
                data.get("error_description")
                or err_payload.get("message")
                or data.get("message")
                or response.text
                or default_error
            )
            log_id = err_payload.get("log_id") or data.get("log_id")
            if log_id:
                message = f"{message} (log_id: {log_id})"
            return data, False, message
        error_payload = data.get("error")
        if isinstance(error_payload, dict):
            code = str(error_payload.get("code") or "").lower()
            if code in ("", "ok", "success", "0"):
                return data, True, ""
            message = error_payload.get("message") or error_payload.get("code") or default_error
            return data, False, str(message)
        raw_error_code = data.get("error_code")
        if raw_error_code not in (None, "", 0, "0", "ok", "OK"):
            message = data.get("error_message") or data.get("description") or default_error
            return data, False, str(message)
        return data, True, ""

    def _tiktok_api_post(self, path, access_token=None, payload=None):
        cfg = self._tiktok_config()
        url = f"{cfg['api_base']}/{path.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        response = requests.post(url, json=payload or {}, headers=headers, timeout=self.TIKTOK_TIMEOUT)
        data, ok, error = self._tiktok_parse_response(response)
        return response, data, ok, error

    def _tiktok_creator_info(self, access_token):
        _, data, ok, error = self._tiktok_api_post("/v2/post/publish/creator_info/query/", access_token, {})
        if not ok:
            raise ValueError(error or "Failed to fetch TikTok creator info.")
        info = data.get("data") or {}
        _logger.error(f"info={info}")
        return {
            "creator_username": info.get("creator_username"),
            "privacy_level_options": info.get("privacy_level_options") or [],
        }

    def _tiktok_allowed_media_hosts(self):
        params = request.env["ir.config_parameter"].sudo()
        configured = (params.get_param("tiktok_allowed_media_hosts") or "").strip()
        hosts = [h.strip().lower() for h in configured.split(",") if h.strip()]
        if hosts:
            return hosts

        base_url = (params.get_param("web.base.url") or "").strip()
        host = (urlparse(base_url).hostname or "").strip().lower()
        return [host] if host else []

    def _tiktok_validate_media_url(self, media_url, expected_media_kind="image"):
        parsed = urlparse((media_url or "").strip())
        if parsed.scheme != "https":
            return False, "TikTok media URL must use HTTPS."
        host = (parsed.hostname or "").lower()
        if not host:
            return False, "TikTok media URL host is invalid."

        allowed_hosts = self._tiktok_allowed_media_hosts()
        if not allowed_hosts:
            return False, "TikTok media host allowlist is empty. Set tiktok_allowed_media_hosts."

        def _match_allowed(candidate, allowed):
            return candidate == allowed or candidate.endswith("." + allowed)

        if not any(_match_allowed(host, allowed) for allowed in allowed_hosts):
            return False, (
                f"Media host '{host}' is not allowed for TikTok pull posting. "
                f"Allowed hosts: {', '.join(allowed_hosts)}"
            )

        try:
            response = requests.get(media_url, timeout=self.TIKTOK_TIMEOUT, allow_redirects=True, stream=True)
            status = response.status_code
            content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            response.close()
        except Exception:
            return False, "TikTok media URL is not publicly reachable from server."

        if status >= 400:
            return False, f"TikTok media URL returned HTTP {status}. Ensure it is publicly accessible."
        prefix = f"{(expected_media_kind or 'image').strip().lower()}/"
        if not content_type.startswith(prefix):
            return False, (
                f"TikTok media URL must return {prefix}* content type without authentication "
                f"(got '{content_type or 'unknown'}')."
            )

        return True, ""

    def _truncate_utf16_units(self, text, max_units):
        value = str(text or "")
        if max_units <= 0:
            return ""
        units = 0
        out = []
        for ch in value:
            codepoint = ord(ch)
            ch_units = 2 if codepoint > 0xFFFF else 1
            if units + ch_units > max_units:
                break
            out.append(ch)
            units += ch_units
        return "".join(out)

    def _convert_png_url_to_jpg(self, media_url):
        """
        If source media is PNG, convert it to JPG and return a public /web/content URL.
        Returns (final_url, converted_flag).
        """
        parsed = urlparse((media_url or "").strip())
        looks_like_png = (parsed.path or "").lower().endswith(".png")

        try:
            response = requests.get(media_url, timeout=self.TIKTOK_TIMEOUT, allow_redirects=True)
        except Exception:
            return media_url, False
        if response.status_code >= 400:
            return media_url, False

        content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        is_png = looks_like_png or content_type == "image/png"
        if not is_png:
            return media_url, False

        try:
            img = Image.open(BytesIO(response.content))
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            out = BytesIO()
            img.save(out, format="JPEG", quality=92, optimize=True)
            jpg_bytes = out.getvalue()
        except Exception:
            return media_url, False

        attachment = request.env["ir.attachment"].sudo().create({
            "name": f"tiktok_media_{int(time.time())}.jpg",
            "type": "binary",
            "datas": base64.b64encode(jpg_bytes).decode(),
            "mimetype": "image/jpeg",
            "public": True,
        })
        # Ensure the converted attachment is visible to HTTP fetchers immediately.
        request.env.cr.commit()
        base_url = (request.env["ir.config_parameter"].sudo().get_param("web.base.url") or "").rstrip("/")
        if not base_url:
            return media_url, False
        return f"{base_url}/web/content/{attachment.id}?download=1", True

    def _tiktok_auth_required_payload(self, return_url, force_login=False, reason=None):
        safe_return = self._safe_local_url(return_url, "/product_analysis")
        auth_url = self._append_query_params(
            "/tiktok/oauth/start",
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

    @http.route('/tiktok/oauth/start', type='http', auth='user', website=True)
    def tiktok_oauth_start(self, **kwargs):
        cfg = self._tiktok_config()
        if not cfg["client_key"] or not cfg["client_secret"] or not cfg["redirect_uri"]:
            return request.make_response("TikTok OAuth is not configured.", status=500)

        next_url = self._safe_local_url(kwargs.get("next"), "/product_analysis")
        force_login = str(kwargs.get("force_login") or "").lower() in ("1", "true", "yes")
        popup_mode = str(kwargs.get("popup") or "").lower() in ("1", "true", "yes")
        if force_login:
            self._clear_user_tiktok_token(request.env.uid)

        state = secrets.token_urlsafe(24)
        request.session["tiktok_oauth_state"] = state
        request.session["tiktok_oauth_next"] = next_url
        request.session["tiktok_oauth_popup"] = popup_mode

        auth_params = {
            "client_key": cfg["client_key"],
            "redirect_uri": cfg["redirect_uri"],
            "state": state,
            "scope": cfg["scope"],
            "response_type": "code",
        }
        if force_login:
            auth_params["disable_auto_auth"] = "1"
        auth_url = self._append_query_params("https://www.tiktok.com/v2/auth/authorize/", auth_params)
        return request.redirect(auth_url, local=False)

    @http.route('/tiktok/oauth/callback', type='http', auth='user', website=True, csrf=False)
    def tiktok_oauth_callback(self, **kwargs):
        cfg = self._tiktok_config()
        redirect_target = self._safe_local_url(request.session.pop("tiktok_oauth_next", "/product_analysis"))
        popup_mode = bool(request.session.pop("tiktok_oauth_popup", False))
        received_state = kwargs.get("state")
        expected_state = request.session.pop("tiktok_oauth_state", None)

        def _popup_response(success, error_message=""):
            payload = {"type": "tiktok_oauth_result", "success": bool(success), "error": error_message or ""}
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
            return request.redirect(self._append_query_params(redirect_target, {"tt_error": "invalid_state"}))

        if kwargs.get("error"):
            error_message = kwargs.get("error_description") or kwargs.get("error")
            if popup_mode:
                return _popup_response(False, error_message)
            return request.redirect(self._append_query_params(redirect_target, {"tt_error": error_message}))

        code = kwargs.get("code")
        if not code:
            if popup_mode:
                return _popup_response(False, "missing_code")
            return request.redirect(self._append_query_params(redirect_target, {"tt_error": "missing_code"}))

        try:
            response = requests.post(
                f"{cfg['api_base']}/v2/oauth/token/",
                data={
                    "client_key": cfg["client_key"],
                    "client_secret": cfg["client_secret"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": cfg["redirect_uri"],
                },
                timeout=self.TIKTOK_TIMEOUT,
            )
            data, ok, error = self._tiktok_parse_response(response, "TikTok token exchange failed.")
        except Exception as exc:
            _logger.exception("TikTok token exchange failed")
            if popup_mode:
                return _popup_response(False, str(exc))
            return request.redirect(self._append_query_params(redirect_target, {"tt_error": str(exc)}))

        if not ok:
            if popup_mode:
                return _popup_response(False, error)
            return request.redirect(self._append_query_params(redirect_target, {"tt_error": error}))

        access_token = data.get("access_token") or (data.get("data") or {}).get("access_token")
        if not access_token:
            if popup_mode:
                return _popup_response(False, "missing_access_token")
            return request.redirect(self._append_query_params(redirect_target, {"tt_error": "missing_access_token"}))

        expires_in = data.get("expires_in") or (data.get("data") or {}).get("expires_in") or 0
        params = request.env["ir.config_parameter"].sudo()
        uid = request.env.uid
        params.set_param(self._tiktok_user_token_key(uid), access_token)
        if int(expires_in or 0) > 0:
            params.set_param(self._tiktok_user_token_expiry_key(uid), str(int(time.time()) + int(expires_in)))
        else:
            params.set_param(self._tiktok_user_token_expiry_key(uid), "")

        if popup_mode:
            return _popup_response(True, "")
        return request.redirect(self._append_query_params(redirect_target, {"tt_connected": "1"}))

    @http.route('/tiktok/status', type='json', auth='user', website=True, methods=['POST'])
    def tiktok_status(self, return_url=None, **kwargs):
        access_token = self._get_user_tiktok_token(request.env.uid)
        if not access_token:
            return self._tiktok_auth_required_payload(return_url, reason="missing_token")

        try:
            creator_info = self._tiktok_creator_info(access_token)
            privacy_options = creator_info.get("privacy_level_options") or []
            posting_ready = bool(privacy_options)
            default_privacy = "SELF_ONLY" if "SELF_ONLY" in privacy_options else (privacy_options[0] if privacy_options else "")
            posting_message = ""
            if not posting_ready:
                posting_message = (
                    "Akun TikTok ini belum siap untuk Direct Post (privacy options kosong). "
                    "Cek app review/compliance di TikTok Developer Portal."
                )
            return {
                "auth_required": False,
                "connected": True,
                "creator": creator_info.get("creator_username"),
                "privacy_level_options": privacy_options,
                "default_privacy_level": default_privacy,
                "posting_ready": posting_ready,
                "posting_message": posting_message,
            }
        except Exception as exc:
            lowered = (str(exc) or "").lower()
            if "access token" in lowered or "unauthorized" in lowered:
                self._clear_user_tiktok_token(request.env.uid)
                return self._tiktok_auth_required_payload(return_url, force_login=True, reason="token_invalid")
            return {"auth_required": False, "connected": False, "error": str(exc) or "Failed to get TikTok status."}

    @http.route('/tiktok/disconnect', type='json', auth='user', website=True, methods=['POST'])
    def tiktok_disconnect(self, **kwargs):
        try:
            self._clear_user_tiktok_token(request.env.uid)
            return {"success": True, "connected": False}
        except Exception as exc:
            return {"success": False, "error": str(exc) or "Failed to disconnect TikTok account."}

    @http.route('/tiktok/post_image', type='json', auth='user', website=True, methods=['POST'])
    def tiktok_post_image(self, image_url=None, caption=None, image_variant_id=None, privacy_level=None, return_url=None, **kwargs):
        json_payload = request.httprequest.get_json(silent=True) or {}
        if not isinstance(json_payload, dict):
            json_payload = {}
        nested_params = json_payload.get("params") if isinstance(json_payload.get("params"), dict) else {}

        image_url = (
            image_url
            or kwargs.get("image_url")
            or json_payload.get("image_url")
            or nested_params.get("image_url")
            or ""
        ).strip()
        caption = (
            caption
            or kwargs.get("caption")
            or json_payload.get("caption")
            or nested_params.get("caption")
            or ""
        ).strip()
        image_variant_id = (
            image_variant_id
            or kwargs.get("image_variant_id")
            or json_payload.get("image_variant_id")
            or nested_params.get("image_variant_id")
            or ""
        )
        privacy_level = (
            privacy_level
            or kwargs.get("privacy_level")
            or json_payload.get("privacy_level")
            or nested_params.get("privacy_level")
            or ""
        ).strip()
        return_url = (
            return_url
            or kwargs.get("return_url")
            or json_payload.get("return_url")
            or nested_params.get("return_url")
            or ""
        )

        if not image_url and image_variant_id:
            try:
                variant = request.env["vit.image_variant"].sudo().browse(int(image_variant_id))
                if variant.exists():
                    image_url = (variant.image_url or "").strip()
            except Exception:
                image_url = ""
        if not image_url:
            return {"error": "Image URL is required."}

        access_token = self._get_user_tiktok_token(request.env.uid)
        if not access_token:
            return self._tiktok_auth_required_payload(return_url, reason="missing_token")

        try:
            media_url = image_url
            media_url, converted = self._convert_png_url_to_jpg(media_url)
            _logger.error(f"converted media_url {media_url}")

            creator_info = self._tiktok_creator_info(access_token)
            privacy_options = creator_info.get("privacy_level_options") or []
            if not privacy_options:
                return {
                    "error": (
                        "TikTok Direct Post belum diizinkan untuk akun/app ini "
                        "(privacy options tidak tersedia)."
                    )
                }
            if converted:
                is_allowed_media, media_error = True, ""
            else:
                is_allowed_media, media_error = self._tiktok_validate_media_url(media_url, expected_media_kind="image")
                if not is_allowed_media:
                    return {"error": media_error}
            selected_privacy = privacy_level or ("SELF_ONLY" if "SELF_ONLY" in privacy_options else privacy_options[0])
            if selected_privacy not in privacy_options:
                return {
                    "error": (
                        f"Privacy level '{selected_privacy}' tidak diizinkan. "
                        f"Opsi tersedia: {', '.join(privacy_options)}"
                    )
                }
            caption_clean = re.sub(r"\s+", " ", (caption or "")).strip()
            title = self._truncate_utf16_units(caption_clean, 90)
            post_info = {
                "privacy_level": selected_privacy,
                "auto_add_music": True,
            }
            if title:
                post_info["title"] = title

            payload = {
                "post_info": post_info,
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "photo_images": [media_url],
                    "photo_cover_index": 0,
                },
                "post_mode": "DIRECT_POST",
                "media_type": "PHOTO",
            }
            _, data, ok, error = self._tiktok_api_post("/v2/post/publish/content/init/", access_token, payload)
            if (not ok) and isinstance(data, dict):
                err = data.get("error") if isinstance(data.get("error"), dict) else {}
                err_code = str(err.get("code") or "").lower()
                err_msg = str(err.get("message") or error or "").lower()
                if err_code == "invalid_params" and ("post info" in err_msg or "post_info" in err_msg):
                    fallback_payload = {
                        "post_info": {
                            "privacy_level": selected_privacy,
                            "auto_add_music": True,
                        },
                        "source_info": {
                            "source": "PULL_FROM_URL",
                            "photo_images": [media_url],
                            "photo_cover_index": 0,
                        },
                        "post_mode": "DIRECT_POST",
                        "media_type": "PHOTO",
                    }
                    _, data, ok, error = self._tiktok_api_post("/v2/post/publish/content/init/", access_token, fallback_payload)
            if not ok:
                lowered = (error or "").lower()
                if "access token" in lowered or "unauthorized" in lowered:
                    self._clear_user_tiktok_token(request.env.uid)
                    return self._tiktok_auth_required_payload(return_url, force_login=True, reason="token_invalid")
                return {"error": error or "Failed to post image to TikTok."}
            publish_id = data.get("data", {}).get("publish_id")
            return {"success": True, "publish_id": publish_id}
        except Exception as exc:
            _logger.exception("TikTok post failed")
            return {"error": str(exc) or "Failed to post image to TikTok."}
