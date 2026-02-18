from odoo import http, api, fields
from odoo.http import request
from markupsafe import Markup
import markdown
import re
import threading
import odoo
import logging
import time
import json
import base64
import psycopg2
import requests
import secrets
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
simulation = True
_logger = logging.getLogger(__name__)

class ProductValueAnalysisController(http.Controller):
    FACEBOOK_TIMEOUT = 20
    FACEBOOK_GRAPH_VERSION = "v19.0"

    def _append_query_params(self, url, params):
        parsed = urlparse(url or "")
        existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
        existing.update({k: v for k, v in (params or {}).items() if v is not None})
        new_query = urlencode(existing)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    def _safe_local_url(self, value, fallback="/product_analysis"):
        if not value:
            return fallback
        parsed = urlparse(value)
        if parsed.scheme or parsed.netloc:
            return fallback
        path = parsed.path or fallback
        if not path.startswith("/"):
            path = f"/{path}"
        return urlunparse(("", "", path, "", parsed.query, parsed.fragment))

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

    def _clear_record_output(self, record, fieldname=None):
        vals = {}

        _logger.info(record._name) 
        
        if record._name == 'vit.audience_profiler':
            record.unlink()        
        elif record._name == 'vit.angle_hook':
            record.unlink()
        elif record._name == 'vit.product_value_analysis':
            if fieldname == "features":
                vals["features"] = False
            elif fieldname == "description":
                vals["description"] = False

        if "output" in record._fields:
            vals["output"] = False
        if "output_html" in record._fields:
            vals["output_html"] = False
                           
        if vals:
            record.sudo().write(vals)

    def _run_background(self, model_name, record_id, action):
        dbname = request.env.cr.dbname
        uid = request.env.uid
        context = dict(request.env.context)

        _logger.info("Background thread spawn: %s(%s) action=%s", model_name, record_id, action)

        def _target():
            _logger.info("Background thread started: %s(%s)", model_name, record_id)
            try:
                _logger.info("Background thread entering Odoo env: %s(%s)", model_name, record_id)
                registry = odoo.registry(dbname)
                _logger.info("Background thread got registry: %s(%s)", model_name, record_id)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    try:
                        with registry.cursor() as cr:
                            _logger.info("Background thread got cursor: %s(%s)", model_name, record_id)
                            env = api.Environment(cr, uid, context)
                            rec = env[model_name].sudo().browse(record_id)
                            try:
                                _logger.info("Background job start: %s(%s) action=%s", model_name, record_id, action)
                                action(rec)
                                _logger.info("Background job done: %s(%s)", model_name, record_id)
                                rec.write({"status": "done", "error_message": False})
                                cr.commit()
                            except Exception as e:
                                _logger.exception("Background job failed for %s(%s)", model_name, record_id)
                                rec.write({"status": "failed", "error_message": str(e)})
                                cr.commit()
                        break
                    except psycopg2.errors.SerializationFailure:
                        _logger.warning(
                            "Serialization failure for %s(%s) attempt %s/%s",
                            model_name,
                            record_id,
                            attempt,
                            max_attempts,
                        )
                        if attempt >= max_attempts:
                            raise
                        time.sleep(0.2 * attempt)
            except Exception:
                _logger.exception("Background thread crashed before job execution for %s(%s)", model_name, record_id)

        threading.Thread(target=_target, daemon=True).start()

    # Write features & desriptopn
    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/write_with_ai', type='json', auth='user', website=True, methods=['POST'])
    def write_with_ai(self, analysis, **kwargs):
        
        analysis.write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.product_value_analysis", analysis.id, lambda rec: rec.action_write_with_ai())
        return {"status": "processing"}

        '''
        analysis.write({"status": "processing", "error_message": False})
        try:
            analysis.action_write_with_ai()
            analysis.write({"status": "done", "error_message": False})
        except Exception as e:
            analysis.write({"status": "failed", "error_message": str(e)})
            raise

        result = analysis.read(['initial_description', 'description', 'features', 'lang_id'])[0]

        return [{
            'id': result.get('id'),
            'name':'Description',
            'output_html': result.get('description', ''),
            'with_next_button': False,
            'target_section':'description'

        },{
            'id': result.get('id'),
            'name':'Features',
            'output_html': result.get('features', ''),
            'target_section':'features',
            'next_step':'product_value_analysis'
        }]
        '''

    def _build_result(self, regenerate_type, record):
        _logger.info(f"regenerate_type={regenerate_type} record={record}")
        if regenerate_type == "write_with_ai":
            return [{
                "id": record.id,
                "name": "Product Value Analysis",
                "description": record.description or "",
                "features":record.features or "",
                "clear_url": f"/product_analysis/{record.id}/clear",
                "next_step":"product_value_analysis",
                "back_title": None,
                "show_view_button": True
            }]
        if regenerate_type == "product_value_analysis":
            return [{
                "id": record.id,
                "name": "Product Value Analysis",
                "output_html": record.output_html or "",
                "current_step":"product_value_analysis",
                "clear_url": f"/product_analysis/{record.id}/clear",
                "next_step":"market_map_analysis",
                "back_title": None,
                "show_view_button": True
            }]
        if regenerate_type == "market_map_analysis":
            return [{
                "id": mm.id,
                "name": mm.name,
                "output_html": mm.output_html or "",
                "prev_step":"product_value_analysis",
                "current_step":"market_map_analysis",
                "next_step":"audience_profile_analysis",
                "clear_url": f"/market_mapper/{mm.id}/clear",
                "back_title": f"Product {record.name}",      
                "show_view_button": True          
            } for mm in record.market_mapper_ids]
        if regenerate_type == "audience_profile_analysis":
            return [{
                "id": ap.id,
                "name": ap.name,
                "output_html": ap.output_html or "",
                "clear_url": f"/audience_profiler/{ap.id}/clear",
                "record_id": record.id,
                "prev_step": "market_map_analysis",
                "current_step":"audience_profile_analysis",
                "next_step":"angle_hook",
                "back_title": f"Market Map {record.name}",       
                "show_view_button": True         
            } for ap in record.audience_profiler_ids]
            # } for ap in record.audience_profiler_ids.sorted(key=lambda rec: rec.audience_profile_no or "")]
        if regenerate_type == "angle_hook":
            return [{
                "id": an.id,
                "name": f"AP {record.audience_profile_no} - Angle {an.angle_no}",
                "output_html": an.output_html or "",
                "clear_url": f"/angle_hook/{an.id}/clear",
                "record_id": record.id,
                "prev_step": "audience_profile_analysis",
                "current_step":"angle_hook",
                "back_title": f"AP {record.audience_profile_no}",
                "next_step": "hook",
                "hooks":[{
                    "id": hook.id,
                    "name": f"AP {record.audience_profile_no} - Angle {an.angle_no} - Hook {hook.hook_no}",
                    "output_html": hook.output_html,
                    "clear_url": f"/hook/{hook.id}/clear",
                    "prev_step": "angle_hook",
                    "current_step":"hook",
                    "next_step":"ads_copy",
                    "back_title": f"Angle {an.angle_no}",
                    "record_id": an.id,

                } for hook in an.hook_ids]
            } for an in record.angle_hook_ids.sorted(key=lambda rec: rec.angle_no or "")]
        if regenerate_type == "hook":
            
            return [{
                "id": ads.id,
                "name": f"Ads Copy: {ads.name}",
                "prev_step": "angle_hook",
                "current_step":"ads_copy",
                "record_id": record.id,                
                "images":[
                    {
                        "id": im.id,
                        "name": im.name,
                        "output_html": im.output_html,
                        "clear_url": f"/image_generator/{im.id}/clear",
                        "next_step":"generate_variants",
                        "back_title": f"Ads Copy {ads.name}",
                        "record_id": ads.id
                    } for im in ads.image_generator_ids
                ],
                "lps":[
                    {
                        "id": lp.id,
                        "name": lp.name,
                        "output_html": lp.output_html,
                        "clear_url": f"/landing_page/{lp.id}/clear",
                        "next_step":"generate_landing_pages",
                        "back_title": f"Ads Copy {ads.name}",
                        "record_id": ads.id
                    } for lp in ads.landing_page_builder_ids
                ],
                "videos":[
                    {
                        "id": vid.id,
                        "name": vid.name,
                        "output_html": vid.output_html,
                        "clear_url": f"/video_director/{vid.id}/clear",
                        "next_step":"generate_videos",
                        "back_title": f"Ads Copy {ads.name}",                        
                        "record_id": ads.id
                    } for vid in ads.video_director_ids
                ],
                "output_html": f"""{ads.output_html_trimmed}
<div class="d-flex align-items-center justify-content-center">
    <a class="btn btn-primary" href="#section-hook-{record.id}"> <i class="fa fa-arrow-left me-1"></i> Back to Hook {record.hook_no}</a>
    <a class="btn btn-primary" href="#ads-copy-images-{ads.id}">View Images</a>
    <a class="btn btn-primary" href="#ads-copy-lp-{ads.id}">View Landing Page</a>
    <a class="btn btn-primary" href="#ads-copy-video-{ads.id}">View Video Script</a>
</div>
""",
                "clear_url": f"/ads_copy/{ads.id}/clear",
            } for ads in record.ads_copy_ids.sorted(key=lambda rec: rec.name or "")]
            
        if regenerate_type == "image_variants":
            return [{
                "id": iv.id,
                "name": iv.name,
                "output_html": f"""<a href="{iv.image_url}" target="_new">
    <img src='{iv.image_url_512}' class='img-fluid'/>
</a>
<button class="btn btn-primary btn-sm mt-2 js-upload-facebook" data-image-url="{iv.image_url}">
    <i class="fa fa-facebook me-1"></i> Upload to Facebook Page
</button>
""",
                "clear_url": f"/image_generator/{record.id}/clear",
                "record_id": record.id
            } for iv in record.image_variant_ids[-1]]
        return []

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

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/clear/<fieldname>', type='json', auth='user', website=True, methods=['POST'])
    def clear_product_analysis(self, analysis, fieldname, **kwargs):
        self._clear_record_output(analysis, fieldname)
        return {"status": "ok"}

    @http.route('/market_mapper/<model("vit.market_mapper"):market_mapper>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_market_mapper(self, market_mapper, **kwargs):
        self._clear_record_output(market_mapper)
        return {"status": "ok"}

    @http.route('/audience_profiler/<model("vit.audience_profiler"):audience_profiler>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_audience_profiler(self, audience_profiler, **kwargs):
        self._clear_record_output(audience_profiler)
        return {"status": "ok"}

    @http.route('/angle_hook/<model("vit.angle_hook"):angle_hook>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_angle_hook(self, angle_hook, **kwargs):
        self._clear_record_output(angle_hook)
        return {"status": "ok"}

    @http.route('/hook/<model("vit.hook"):hook>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_hook(self, hook, **kwargs):
        self._clear_record_output(hook)
        return {"status": "ok"}

    @http.route('/ads_copy/<model("vit.ads_copy"):ads_copy>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_ads_copy(self, ads_copy, **kwargs):
        self._clear_record_output(ads_copy)
        return {"status": "ok"}

    @http.route('/image_generator/<model("vit.image_generator"):image_generator>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_image_generator(self, image_generator, **kwargs):
        self._clear_record_output(image_generator)
        return {"status": "ok"}

    @http.route('/video_director/<model("vit.video_director"):video_director>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_video_director(self, video_director, **kwargs):
        self._clear_record_output(video_director)
        return {"status": "ok"}

    @http.route('/landing_page/<model("vit.landing_page_builder"):landing_page>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_landing_page(self, landing_page, **kwargs):
        self._clear_record_output(landing_page)
        return {"status": "ok"}

    # CRUD 
    @http.route(['/product_analysis', '/product_analysis/page/<int:page>'], type='http', auth='user', website=True)
    def list(self, page=1, **kwargs):
        product_analysis_obj = request.env['vit.product_value_analysis']
        domain = []
        
        # Pagination
        per_page = 12
        total = product_analysis_obj.search_count(domain)
        pager = request.website.pager(
            url='/product_analysis',
            total=total,
            page=page,
            step=per_page,
            scope=7,
            url_args=kwargs
        )
        
        analyses = product_analysis_obj.search(domain, offset=pager['offset'], limit=per_page, order="create_date desc")
        
        return request.render('vit_adsuhu_frontend.product_analysis_list_template', {
            'analyses': analyses,
            'pager': pager,
        })

    @http.route('/product_analysis/create', type='http', auth='user', website=True)
    def create(self, **kwargs):
        langs = request.env['res.lang'].search([('active', '=', True)])
        return request.render('vit_adsuhu_frontend.product_analysis_create_template', {
            'langs': langs,
        })

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/edit', type='http', auth='user', website=True)
    def edit(self, analysis, **kwargs):
        langs = request.env['res.lang'].search([('active', '=', True)])
        return request.render('vit_adsuhu_frontend.product_analysis_edit_template', {
            'analysis': analysis,
            'langs': langs,
        })

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/download_docx', type='http', auth='user', website=True)
    def download_docx(self, analysis, **kwargs):
        action = analysis.sudo().action_download_docx()
        url = action.get("url") if isinstance(action, dict) else None
        if url:
            return request.redirect(url)
        return request.redirect(f'/product_analysis/{analysis.id}')

    @http.route(['/customer_credits', '/customer_credits/page/<int:page>'], type='http', auth='user', website=True)
    def customer_credits(self, page=1, **kwargs):
        credit_obj = request.env['vit.customer_credit'].sudo()
        partner = request.env.user.partner_id
        domain = [('customer_id', '=', partner.id)]

        per_page = 20
        total = credit_obj.search_count(domain)
        pager = request.website.pager(
            url='/customer_credits',
            total=total,
            page=page,
            step=per_page,
            scope=7,
            url_args=kwargs
        )

        credits = credit_obj.search(
            domain,
            offset=pager['offset'],
            limit=per_page,
            order="date_time desc"
        )

        return request.render('vit_adsuhu_frontend.customer_credits_list_template', {
            'credits': credits,
            'pager': pager,
        })

    @http.route('/payment/manual_info', type='json', auth='user', website=True, methods=['POST'])
    def manual_payment_info(self, **kwargs):
        provider = request.env['payment.provider'].sudo().search(
            [('code', '=', 'custom'), ('is_published', '=', True), ('state', '=', 'enabled')], limit=1
        )
        if not provider or not provider.pending_msg:
            return {"error": "Manual payment instruction not configured."}
        return {"message": provider.pending_msg}

    @http.route('/payment/manual_submit', type='http', auth='user', website=True, methods=['POST'])
    def manual_payment_submit(self, **post):
        package = (post.get('package') or '').strip()
        amount_raw = (post.get('amount') or post.get('custom_amount') or '').strip()
        partner = request.env.user.partner_id
        proof_file = request.httprequest.files.get('transfer_proof')

        if not partner:
            return request.make_response(
                json.dumps({"error": "Partner not found."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        if not proof_file:
            return request.make_response(
                json.dumps({"error": "Transfer proof file is required."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        predefined_packages = {
            "100000": {"amount": 100000.0},
            "200000": {"amount": 200000.0},
            "500000": {"amount": 500000.0},
        }

        try:
            if package in predefined_packages:
                amount = predefined_packages[package]["amount"]
            else:
                amount = float(amount_raw or 0)
            if amount <= 0:
                raise ValueError("amount must be positive")
        except Exception:
            return request.make_response(
                json.dumps({"error": "Invalid top up amount."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        proof_content = proof_file.read()
        if not proof_content:
            return request.make_response(
                json.dumps({"error": "Transfer proof file is empty."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        credit = request.env['vit.customer_credit'].sudo().create({
            'customer_id': partner.id,
            'ref': 'Manual transfer - pending verification',
            'credit': amount,
            'is_usage': False,
            'date_time': fields.Datetime.now(),
            'state': 'draft',
            'transfer_proof': base64.b64encode(proof_content).decode(),
            'transfer_proof_filename': proof_file.filename or 'transfer_proof',
        })

        return request.make_response(
            json.dumps({"success": True, "id": credit.id}),
            headers=[('Content-Type', 'application/json')],
            status=200,
        )

    @http.route('/product_analysis/submit', type='http', auth='user', website=True, methods=['POST'])
    def submit(self, **post):
        product_name = post.get('product_name')
        product_url = post.get('product_url')
        target_market = post.get('target_market')
        description = post.get('description')
        initial_description = post.get('initial_description')
        features = post.get('features')
        tags = post.get('tags')
        deafult_lang = request.env['res.lang'].search([('active', '=', True)], limit=1)
        lang_id = int(post.get('lang_id')) if post.get('lang_id') else deafult_lang.id

        # if not product_url:
        #     return request.redirect('/product_analysis/create')

        new_analysis = request.env['vit.product_value_analysis'].create({
            'name': product_name,
            'product_url': product_url,
            'target_market': target_market,
            'description': description,
            'initial_description': initial_description,
            'features': features,
            'tags': tags,
            'lang_id': lang_id,
            'partner_id': request.env.user.partner_id.id
        })

        return request.redirect(f'/product_analysis/{new_analysis.id}')

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/update', type='http', auth='user', website=True, methods=['POST'])
    def update(self, analysis, **post):
        product_name = post.get('product_name')
        product_url = post.get('product_url')
        target_market = post.get('target_market')
        description = post.get('description')
        initial_description = post.get('initial_description')
        features = post.get('features')
        deafult_lang = request.env['res.lang'].search([('active', '=', True)], limit=1)
        lang_id = int(post.get('lang_id')) if post.get('lang_id') else deafult_lang.id

        if not product_url:
            return request.redirect(f'/product_analysis/{analysis.id}/edit')

        analysis.write({
            'name': product_name if product_name else analysis.name,
            'product_url': product_url,
            'target_market': target_market if target_market else analysis.target_market,
            'description': description,
            'initial_description': initial_description,
            'features': features,
            'lang_id': lang_id,
        })

        return request.redirect(f'/product_analysis/{analysis.id}')

    # Regenerate secion
    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_product_analysis(self, analysis, **kwargs):
        analysis.write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.product_value_analysis", analysis.id, lambda rec: rec.action_generate())
        return {"status": "processing"}

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/market_mapper/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_market_mapper(self, analysis, **kwargs):
        analysis.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.product_value_analysis", analysis.id, lambda rec: rec.action_generate_market_mapping())
        return {"status": "processing"}

    @http.route('/market_mapper/<model("vit.market_mapper"):market_mapper>/audience_profiler/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_audience_profiler(self, market_mapper, **kwargs):
        market_mapper.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.market_mapper", market_mapper.id, lambda rec: rec.action_generate_audience_profiler())
        return {"status": "processing"}

    @http.route('/audience_profiler/<model("vit.audience_profiler"):audience_profiler>/angle_hook/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_angle_hook(self, audience_profiler, **kwargs):
        audience_profiler.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.audience_profiler", audience_profiler.id, lambda rec: rec.action_generate_angles())
        return {"status": "processing"}

    @http.route('/hook/<model("vit.hook"):hook>/ads_copy/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_ads_copy(self, hook, **kwargs):
        hook.write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.hook", hook.id, lambda rec: rec.action_create_ads_copy())
        return {"status": "processing"}

    @http.route('/image_generator/<model("vit.image_generator"):image_generator>/image_variant/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_image_variant(self, image_generator, **kwargs):
        image_generator.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.image_generator", image_generator.id, lambda rec: rec.action_generate())
        return {"status": "processing"}
    
    def _add_img_responsive_classes(self, html):
        if not html:
            return html

        def _inject(match):
            tag = match.group(0)
            class_match = re.search(r'class="([^"]*)"', tag)
            if class_match:
                classes = class_match.group(1).split()
                if "img" not in classes:
                    classes.append("img")
                if "img-fluid" not in classes:
                    classes.append("img-fluid")
                new_class_attr = f'class="{" ".join(classes)}"'
                return tag[: class_match.start()] + new_class_attr + tag[class_match.end() :]
            return tag.replace("<img", '<img class="img img-fluid"', 1)

        return re.sub(r"<img\b[^>]*>", _inject, html)

    def _process_markdown(self, text):
        if not text:
            return '', ''
        
        lines = text.split('\n')
        new_lines = []
        toc_lines = []
        counters = [0] * 6  # For h1 to h6
        
        import re
        header_pattern = re.compile(r'^(#{1,6})\s+(.*)')
        
        for line in lines:
            match = header_pattern.match(line)
            if match:
                hashes, title = match.groups()
                level = len(hashes)
                
                # Increment current level, reset deeper levels
                counters[level-1] += 1
                for i in range(level, 6):
                    counters[i] = 0
                
                # Build version string 1.2.1
                version_parts = [str(c) for c in counters[:level]]
                version = ".".join(version_parts)
                
                new_title = f"{version} {title}"
                new_lines.append(f"{hashes} {new_title}")
                
                # Add to TOC
                indent = "  " * (level - 1)
                slug = re.sub(r'[^a-zA-Z0-9\-_]', '', new_title.replace(' ', '-').lower())
                
                # Check if the title already has a link, if so avoid double linking in TOC or handle gracefully
                # Generally markdown headers get IDs. We need to ensure we can link to them.
                # The 'toc' extension usually handles IDs.
                # If we manually change content, 'toc' extension will see the numbers.
                # simpler approach: Just collect them here, we will rely on markdown toc extension for anchoring if we pass 'toc' extension?
                # Actually, simply prepending text is enough. 
                # To define anchors, we might rely on python-markdown's default behavior or 'toc' extension.
                # Let's use [TOC] marker if we want to use the extension, BUT the user wants numbering in the text too.
                # So we modified the text.
                
                toc_lines.append(f"{indent}- [{new_title}](#slug-{version.replace('.', '-')})")
                
                # Add explicit anchor to the line to ensure linking works
                # Python-markdown attr_list extension allows {: #id } but maybe not available?
                # We can use raw html or just hope standard slugify works with the new numbering?
                # Safer: inject encoded header id if we can. 
                # Let's try to append standard HTML anchor if possible or use attr_list if available.
                # Since we don't know extensions available, let's output raw HTML header? No, mixing markdown is risky.
                # Let's use the fact that later we render with markdown.
                
                # Optimized approach:
                # We modified the line to: "## 1.1 Title"
                # We want a TOC that links to this.
                # Standard markdown generates id "11-title" or similar.
                # Let's manually constructing a cleaned slug is hard to match exactly what python-markdown does.
                # ALTERNATIVE: Don't generate TOC manually, just Number the headers, then use the 'toc' extension to generate the TOC?
                # User asked to "create table of content section".
                # If we use `markdown(extensions=['toc'])` object, we can extract the TOC object.
                pass 
            else:
                new_lines.append(line)
        
        numbered_text = "\n".join(new_lines)
        
        # Now pass to markdown with 'toc' extension
        md = markdown.Markdown(extensions=['tables', 'toc'])
        html_content = md.convert(numbered_text)
        html_content = self._add_img_responsive_classes(html_content)
        
        # The 'toc' extension automatically supports [TOC] marker, but we can also access md.toc
        # However, to display TOC separately, we can return md.toc
        
        return Markup(html_content), Markup(md.toc)



    # fetch status
    @http.route('/regenerate_status/<string:regenerate_type>/<int:record_id>', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_status(self, regenerate_type, record_id, **kwargs):
        model_map = {
            "write_with_ai": "vit.product_value_analysis",
            "product_value_analysis": "vit.product_value_analysis",
            "market_map_analysis": "vit.product_value_analysis",
            "audience_profile_analysis": "vit.market_mapper",
            "angle_hook": "vit.audience_profiler",
            "hook": "vit.hook",
            "ads_copy": "vit.hook",
            "image_variants": "vit.image_generator",
        }
        model_name = model_map.get(regenerate_type)
        if not model_name:
            return {"status": "failed", "error": "Unknown regenerate type."}

        record = request.env[model_name].browse(record_id)
        status = record.status or "idle"
        result = []
        if status == "done":
            result = self._build_result(regenerate_type, record)
        error_message = record.error_message if status == "failed" else False
        return {"status": status, "result": result, "error": error_message}

    # view details
    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>', type='http', auth='user', website=True)
    def detail(self, analysis, **kwargs):
        final_report_html, final_report_toc = self._process_markdown(analysis.final_report)
        
        values = {
            'analysis': analysis,
            'description_html': Markup(markdown.markdown(analysis.description, extensions=['tables'])) if analysis.description else '',
            'features_html': Markup(markdown.markdown(analysis.features, extensions=['tables'])) if analysis.features else '',
            'final_report_html': final_report_html,
            'final_report_toc': final_report_toc,
        }
        return request.render('vit_adsuhu_frontend.product_analysis_detail_template', values)
