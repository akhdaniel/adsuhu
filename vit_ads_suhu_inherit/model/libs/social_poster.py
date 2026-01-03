import logging
from typing import Any, Callable, Dict, Optional

import requests

_logger = logging.getLogger(__name__)

GRAPH_VERSION = "v19.0"


class SocialPostError(Exception):
    """Raised when a social post fails or validation is missing."""


class SocialPoster:
    """Helper for posting content to LinkedIn, Facebook, and Instagram."""

    def __init__(
        self,
        linkedin_token: Optional[str] = None,
        linkedin_client_id: Optional[str] = None,
        linkedin_client_secret: Optional[str] = None,
        linkedin_redirect_uri: Optional[str] = None,
        linkedin_refresh_token: Optional[str] = None,
        linkedin_authorization_code: Optional[str] = None,
        facebook_token: Optional[str] = None,
        instagram_token: Optional[str] = None,
        token_saver: Optional[Callable[[Dict[str, str]], None]] = None,
        timeout: int = 20,
        session: Optional[requests.Session] = None,
        graph_version: str = GRAPH_VERSION,
    ) -> None:
        self.linkedin_token = linkedin_token
        self.linkedin_client_id = linkedin_client_id
        self.linkedin_client_secret = linkedin_client_secret
        self.linkedin_redirect_uri = linkedin_redirect_uri
        self.linkedin_refresh_token = linkedin_refresh_token
        self.linkedin_authorization_code = linkedin_authorization_code
        self.facebook_token = facebook_token
        self.instagram_token = instagram_token
        self.token_saver = token_saver
        self.timeout = timeout
        self.session = session or requests.Session()
        self.graph_version = graph_version

    def post_linkedin(
        self,
        author_urn: str,
        message: str,
        media_url: Optional[str] = None,
        visibility: str = "PUBLIC",
    ) -> Dict[str, Any]:
        """Publish a LinkedIn UGC post with optional image URL."""
        token = self._get_linkedin_access_token()

        _logger.info('token==============>', token)

        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        share_content: Dict[str, Any] = {
            "shareCommentary": {"text": message},
            "shareMediaCategory": "NONE",
        }

        if media_url:
            share_content.update(
                {
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {"text": message[:200] if message else ""},
                            "media": media_url,
                            "title": {"text": "Image"},
                        }
                    ],
                }
            )

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }
        _logger.info("Posting to LinkedIn as %s", author_urn)
        return self._post_linkedin_with_refresh(url, payload, headers=headers)

    def post_facebook(
        self,
        page_id: str,
        message: str,
        link_url: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish a feed post or photo to a Facebook Page."""
        self._ensure_token(self.facebook_token, "Facebook")

        base_url = self._graph_url(page_id)
        payload: Dict[str, Any] = {"access_token": self.facebook_token}

        if image_url:
            url = f"{base_url}/photos"
            payload.update({"caption": message or "", "url": image_url})
        else:
            url = f"{base_url}/feed"
            payload.update({"message": message or ""})
            if link_url:
                payload["link"] = link_url

        _logger.info("Posting to Facebook page %s", page_id)
        return self._post_form(url, payload)

    def post_instagram(
        self,
        business_account_id: str,
        image_url: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish an image post through the Instagram Graph API."""
        self._ensure_token(self.instagram_token, "Instagram")

        base_url = self._graph_url(business_account_id)
        media_payload: Dict[str, Any] = {
            "access_token": self.instagram_token,
            "image_url": image_url,
        }
        if caption:
            media_payload["caption"] = caption

        _logger.info("Creating Instagram media container for %s", business_account_id)
        media_response = self._post_form(f"{base_url}/media", media_payload)
        creation_id = media_response.get("id")
        if not creation_id:
            raise SocialPostError("Instagram media container creation failed.")

        publish_payload = {
            "access_token": self.instagram_token,
            "creation_id": creation_id,
        }
        _logger.info("Publishing Instagram media %s", creation_id)
        publish_response = self._post_form(f"{base_url}/media_publish", publish_payload)
        publish_response["creation_id"] = creation_id
        return publish_response

    def _graph_url(self, path: str) -> str:
        return f"https://graph.facebook.com/{self.graph_version}/{path.lstrip('/')}"

    def _get_linkedin_access_token(self) -> str:
        """Return a LinkedIn access token, refreshing or exchanging if needed."""
        if self.linkedin_token:
            return self.linkedin_token

        _logger.info(f"{self.linkedin_client_id} and {self.linkedin_client_secret}")
        
        self._require_client_credentials()

        _logger.info(f"{self.linkedin_refresh_token}")
        if self.linkedin_refresh_token:
            return self._exchange_linkedin_token(
                grant_type="refresh_token", refresh_token=self.linkedin_refresh_token
            )

        if self.linkedin_authorization_code:
            if not self.linkedin_redirect_uri:
                raise SocialPostError("LinkedIn redirect URI is required with an authorization code.")
            return self._exchange_linkedin_token(
                grant_type="authorization_code",
                code=self.linkedin_authorization_code,
                redirect_uri=self.linkedin_redirect_uri,
            )

        raise SocialPostError(
            "LinkedIn token is missing. Provide linkedin_refresh_token or linkedin_authorization_code."
        )

    def _exchange_linkedin_token(self, grant_type: str, **kwargs: str) -> str:
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        payload = {
            "grant_type": grant_type,
            "client_id": self.linkedin_client_id,
            "client_secret": self.linkedin_client_secret,
        }
        payload.update(kwargs)

        _logger.info("Requesting LinkedIn %s token", grant_type)
        response = self.session.post(token_url, data=payload, timeout=self.timeout)
        data = self._handle_response(response)
        access_token = data.get("access_token")
        if not access_token:
            raise SocialPostError("LinkedIn token response missing access_token.")
        self.linkedin_token = access_token
        if data.get("refresh_token"):
            self.linkedin_refresh_token = data["refresh_token"]
        self._save_tokens(
            {
                "access_token": self.linkedin_token,
                "refresh_token": self.linkedin_refresh_token or "",
            }
        )
        return access_token

    def _require_client_credentials(self) -> None:
        if not (self.linkedin_client_id and self.linkedin_client_secret):
            raise SocialPostError("LinkedIn client_id or client_secret is missing.")

    def _save_tokens(self, tokens: Dict[str, str]) -> None:
        if self.token_saver:
            try:
                self.token_saver(tokens)
            except Exception:
                _logger.exception("Failed to persist LinkedIn tokens")

    def _post_linkedin_with_refresh(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        if response.status_code == 401 and self.linkedin_refresh_token:
            _logger.info("LinkedIn token expired, refreshing and retrying post")
            try:
                new_token = self._exchange_linkedin_token(
                    grant_type="refresh_token", refresh_token=self.linkedin_refresh_token
                )
                headers = dict(headers, Authorization=f"Bearer {new_token}")
                response = self.session.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                )
            except SocialPostError:
                raise
            except Exception as exc:
                raise SocialPostError(f"LinkedIn token refresh failed: {exc}")

        return self._handle_response(response)

    def _ensure_token(self, token: Optional[str], platform: str) -> None:
        if not token:
            raise SocialPostError(f"{platform} access token is missing.")

    def _post_json(
        self, url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        return self._handle_response(response)

    def _post_form(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(url, data=payload, timeout=self.timeout)
        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        if response.status_code >= 400:
            message = body if isinstance(body, dict) else {"raw": body}
            raise SocialPostError(f"Request failed ({response.status_code}): {message}")

        return body
