from odoo import http
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl


class SocialControllerBase(http.Controller):
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
