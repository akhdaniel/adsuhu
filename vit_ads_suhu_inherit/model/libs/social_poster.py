import logging
from io import BytesIO
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

try:
    from PIL import Image
except ImportError:  # Pillow is optional until resize is requested
    Image = None  # type: ignore

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
        author_urn = self._normalize_linkedin_author(
            author_urn or self._get_linkedin_member_urn_from_token(token)
        )
        asset_urn = None
        if media_url:
            asset_urn = self._upload_linkedin_image(media_url, author_urn, token)

        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        share_content: Dict[str, Any] = {
            "shareCommentary": {"text": message},
            "shareMediaCategory": "NONE",
        }

        if asset_urn:
            share_content.update(
                {
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {"text": message[:200] if message else ""},
                            "media": asset_urn,
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
        return self._post_linkedin_with_refresh(url, payload, headers=headers, token=token)

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
        page_token = self._get_facebook_page_token(page_id)
        tokens_to_try: Tuple[Tuple[str, str], ...] = tuple(
            token
            for token in (
                ("page", page_token) if page_token and page_token != self.facebook_token else None,
                ("configured", self.facebook_token),
            )
            if token
        )

        def build_request(token: str) -> Tuple[str, Dict[str, Any]]:
            payload: Dict[str, Any] = {"access_token": token}
            if image_url:
                url = f"{base_url}/photos"
                payload.update({"caption": message or ""})
            else:
                url = f"{base_url}/feed"
                payload.update({"message": message or ""})
                if link_url:
                    payload["link"] = link_url
            return url, payload

        last_error: Optional[Exception] = None
        for token_source, token in tokens_to_try:
            url, payload = build_request(token)
            _logger.info("Posting to Facebook page %s using %s token", page_id, token_source)
            try:
                if image_url:
                    original_bytes = self._download_bytes(image_url)
                    resized_bytes, mime = self._resize_image_bytes(original_bytes, 0.75)
                    files = {"source": ("image", resized_bytes, mime)}
                    return self._post_form(url, payload, files=files)
                return self._post_form(url, payload)
            except SocialPostError as exc:
                last_error = exc
                if not self._is_facebook_permission_error(exc):
                    break
                _logger.warning(
                    "Facebook post failed with %s token (%s); trying fallback if available",
                    token_source,
                    exc,
                )

        assert last_error is not None
        raise last_error

    def post_instagram(
        self,
        business_account_id: str,
        image_url: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish an image post through the Instagram Graph API."""
        self._ensure_token(self.instagram_token, "Instagram")

        base_url = self._graph_url(business_account_id)
        media_base_payload: Dict[str, Any] = {"access_token": self.instagram_token}
        if caption:
            media_base_payload["caption"] = caption

        url_attempts = [
            ("0.75x", self._scaled_image_url(image_url, 0.75)),
            ("0.50x", self._scaled_image_url(image_url, 0.5)),
            ("original", image_url),
        ]

        last_error: Optional[Exception] = None
        media_response: Optional[Dict[str, Any]] = None
        _logger.info("Creating Instagram media container for %s", business_account_id)
        for label, candidate_url in url_attempts:
            payload = dict(media_base_payload, image_url=candidate_url)
            try:
                _logger.info("Attempting IG upload with %s image URL", label)
                media_response = self._post_form(f"{base_url}/media", payload)
                break
            except SocialPostError as exc:
                last_error = exc
                if not self._is_instagram_download_timeout(exc):
                    break
                _logger.warning(
                    "IG upload failed due to download timeout using %s; trying next smaller size",
                    label,
                )

        if not media_response:
            assert last_error is not None
            raise last_error

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
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str], token: str
    ) -> Dict[str, Any]:
        response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        if response.status_code == 401 and self.linkedin_refresh_token:
            _logger.info("LinkedIn token expired, refreshing and retrying post")
            try:
                new_token = self._exchange_linkedin_token(
                    grant_type="refresh_token", refresh_token=self.linkedin_refresh_token
                )
                token = new_token
                headers = dict(headers, Authorization=f"Bearer {new_token}")
                response = self.session.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                )
            except SocialPostError:
                raise
            except Exception as exc:
                raise SocialPostError(f"LinkedIn token refresh failed: {exc}")

        if response.status_code == 403:
            body = self._safe_json(response)
            if self._author_error(body):
                fallback_author = self._get_linkedin_member_urn_from_token(token)
                attempts = []
                if fallback_author:
                    attempts.append(self._normalize_linkedin_author(fallback_author))
                    attempts.append(self._to_person_urn(fallback_author))
                for alt_author in attempts:
                    if alt_author and alt_author != payload.get("author"):
                        _logger.info("Retrying LinkedIn post with token owner author %s", alt_author)
                        payload = dict(payload, author=alt_author)
                        response = self.session.post(
                            url, json=payload, headers=headers, timeout=self.timeout
                        )
                        if response.status_code < 400:
                            break

        return self._handle_response(response)

    def _ensure_token(self, token: Optional[str], platform: str) -> None:
        if not token:
            raise SocialPostError(f"{platform} access token is missing.")

    def _post_json(
        self, url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.Timeout as exc:
            raise SocialPostError(f"Request timed out posting to {url}: {exc}")

    def _post_form(
        self, url: str, payload: Dict[str, Any], files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            response = self.session.post(url, data=payload, files=files, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.Timeout as exc:
            raise SocialPostError(f"Request timed out posting to {url}: {exc}")

    def _normalize_linkedin_author(self, author_urn: str) -> str:
        # LinkedIn expects member URNs for people (urn:li:member:<id>)
        if not author_urn:
            return author_urn
        if author_urn.startswith("urn:li:person:"):
            return author_urn.replace("urn:li:person:", "urn:li:member:", 1)
        return author_urn

    def _to_person_urn(self, author_urn: str) -> str:
        if not author_urn:
            return author_urn
        if author_urn.startswith("urn:li:member:"):
            return author_urn.replace("urn:li:member:", "urn:li:person:", 1)
        return author_urn

    def _get_linkedin_member_urn_from_token(self, token: str) -> Optional[str]:
        """Fetch member URN tied to the access token."""
        try:
            resp = self.session.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout,
            )
            data = self._safe_json(resp)
            member_id = data.get("id")
            if member_id:
                return f"urn:li:member:{member_id}"
        except Exception:
            _logger.exception("Failed to fetch LinkedIn member URN from token")
        return None

    def _upload_linkedin_image(self, media_url: str, owner_urn: str, token: str) -> str:
        """Register and upload an image so it renders inline on LinkedIn."""
        image_bytes, _ = self._resize_image_bytes(self._download_bytes(media_url), 0.5)
        if not image_bytes:
            raise SocialPostError("Failed to download image for LinkedIn upload.")

        register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
        payload = {
            "registerUploadRequest": {
                "owner": owner_urn,
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "serviceRelationships": [
                    {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                ],
            }
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        register_resp = self.session.post(
            register_url, json=payload, headers=headers, timeout=self.timeout
        )
        data = self._handle_response(register_resp)
        value = data.get("value", {}) if isinstance(data, dict) else {}
        asset_urn = value.get("asset")
        upload_info = (
            value.get("uploadMechanism", {})
            .get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {})
        )
        upload_url = upload_info.get("uploadUrl")
        upload_headers = self._normalize_upload_headers(upload_info.get("headers", {}), token)

        if not upload_url or not asset_urn:
            raise SocialPostError("LinkedIn upload registration failed.")

        upload_resp = self.session.put(
            upload_url, data=image_bytes, headers=upload_headers, timeout=self.timeout
        )
        if upload_resp.status_code >= 300:
            raise SocialPostError(
                f"LinkedIn image upload failed ({upload_resp.status_code}): {upload_resp.text}"
            )
        return asset_urn

    def _download_bytes(self, url: str) -> bytes:
        resp = self.session.get(url, timeout=self.timeout)
        if resp.status_code != 200:
            raise SocialPostError(f"Failed to download media from {url}: {resp.status_code}")
        return resp.content

    def _normalize_upload_headers(self, headers: Dict[str, Any], token: str) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for key, val in (headers or {}).items():
            out[str(key)] = str(val)
        if "Authorization" not in out:
            out["Authorization"] = f"Bearer {token}"
        if "Content-Type" not in out:
            out["Content-Type"] = "application/octet-stream"
        return out

    def _resize_image_bytes(self, image_bytes: bytes, scale: float = 0.5) -> Tuple[bytes, str]:
        """Resize an image by the provided scale and return bytes and mime type."""
        if Image is None:
            raise SocialPostError("Pillow is required to resize images. Please install 'pillow'.")
        if scale <= 0:
            raise SocialPostError("Scale must be positive.")

        try:
            with Image.open(BytesIO(image_bytes)) as img:
                new_size = (
                    max(1, int(img.width * scale)),
                    max(1, int(img.height * scale)),
                )
                resized = img.resize(new_size, Image.LANCZOS)
                fmt = (img.format or "JPEG").upper()
                mime = f"image/{'jpeg' if fmt in ('JPG', 'JPEG') else fmt.lower()}"
                buffer = BytesIO()
                resized.save(buffer, format=fmt)
                return buffer.getvalue(), mime
        except Exception as exc:
            raise SocialPostError(f"Failed to resize image: {exc}")

    def _scaled_image_url(self, image_url: str, scale: float) -> str:
        """Append width/height params to ask Odoo to serve a scaled image."""
        if scale >= 1 or scale <= 0:
            return image_url
        width = height = None
        try:
            with Image.open(BytesIO(self._download_bytes(image_url))) as img:
                width = max(1, int(img.width * scale))
                height = max(1, int(img.height * scale))
        except Exception:
            # Fallback to a reasonable bound if we cannot read size
            width = height = int(1080 * scale)

        parsed = urlparse(image_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        # Do not override explicit user-provided width/height
        query.setdefault("width", str(width))
        query.setdefault("height", str(height))
        new_query = urlencode(query)
        return urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
        )

    def _safe_json(self, response: requests.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {}

    def _author_error(self, body: Dict[str, Any]) -> bool:
        if not isinstance(body, dict):
            return False
        message = body.get("message", "")
        if not message:
            return False
        return "/author" in message or "author" in message

    def _is_facebook_permission_error(self, error: Exception) -> bool:
        text = str(error).lower()
        return "does not have permission to post" in text or "(#200)" in text

    def _is_instagram_download_timeout(self, error: Exception) -> bool:
        text = str(error).lower()
        return "takes too long to download the media" in text or "download the media" in text

    def _get_facebook_page_token(self, page_id: str) -> Optional[str]:
        """Return the page access token so posts are made on behalf of the page."""
        url = self._graph_url(page_id)
        params = {"fields": "access_token", "access_token": self.facebook_token}
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except Exception:
            _logger.exception("Failed to call Facebook API for page token")
            return None

        data = self._safe_json(response)
        if response.status_code >= 400:
            _logger.warning("Unable to fetch Facebook page token for %s: %s", page_id, data)
            return None

        token = data.get("access_token")
        if not token:
            _logger.warning("Facebook page token missing in response for %s: %s", page_id, data)
        return token

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}

        if response.status_code >= 400:
            message = body if isinstance(body, dict) else {"raw": body}
            raise SocialPostError(f"Request failed ({response.status_code}): {message}")

        return body
