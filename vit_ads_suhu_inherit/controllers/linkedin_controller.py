import logging

import requests
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LinkedInOAuthController(http.Controller):
    @http.route("/linkedin/callback", type="http", auth="public", csrf=False)
    def linkedin_callback(self, **kwargs):
        _logger.info('calback-----')
        code = kwargs.get("code")
        state = kwargs.get("state")
        if not code:
            return "Missing authorization code."

        params = request.env["ir.config_parameter"].sudo()
        expected_state = params.get_param("linkedin_oauth_state")
        if expected_state and state != expected_state:
            _logger.warning("LinkedIn OAuth state mismatch: expected %s got %s", expected_state, state)
            return "Invalid state parameter."

        client_id = params.get_param("linkedin_client_id")
        client_secret = params.get_param("linkedin_client_secret")
        redirect_uri = params.get_param("linkedin_redirect_uri")

        if not all([client_id, client_secret, redirect_uri]):
            return "LinkedIn client credentials or redirect URI not configured."

        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            response = requests.post(token_url, data=payload, timeout=15)
            data = response.json()
        except Exception as e:
            _logger.exception("LinkedIn token exchange failed")
            return f"Token exchange failed: {e}"

        if response.status_code >= 400:
            _logger.error("LinkedIn token exchange error %s: %s", response.status_code, data)
            return f"Token exchange error: {data}"

        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

        if access_token:
            params.set_param("linkedin_access_token", access_token)
        if refresh_token:
            params.set_param("linkedin_refresh_token", refresh_token)

        return "LinkedIn authorization successful. Tokens saved."
