
import os
import json
import time
import logging
_logger = logging.getLogger(__name__)
import requests

class Fal:
    def __init__(self, api_key=None):
        self.api_key=api_key
        self.model_name=False
        # Always defined: generate() reads self.final_url after _download_request(),
        # and a non-2xx result fetch previously left it unset -> AttributeError
        # that masked the real fal error.
        self.final_url=False
        self.last_error=None

    def generate(self, model_name, prompt, additional_payload={} ):
        """
        response=$(curl --request POST \
        --url https://queue.fal.run/fal-ai/flux-pro/v1.1-ultra \
        --header "Authorization: Key $FAL_KEY" \
        --header "Content-Type: application/json" \
        --data '{
            "prompt": "Extreme close-up of a single tiger eye, direct frontal view. Detailed iris and pupil. Sharp focus on eye texture and color. 
            Natural lighting to capture authentic eye shine and depth. The word \"FLUX\" 
            is painted over it in big, white brush strokes with visible texture."
        }')
        REQUEST_ID=$(echo "$response" | grep -o '"request_id": *"[^"]*"' | sed 's/"request_id": *//; s/"//g')

        response:
        {'status': 'IN_QUEUE', 
        'request_id':   '80dbb1a2-c0a5-486c-a1b9-bdb370393e43', 
        'response_url': 'https://queue.fal.run/fal-ai/flux-pro/requests/80dbb1a2-c0a5-486c-a1b9-bdb370393e43', 
        'status_url':   'https://queue.fal.run/fal-ai/flux-pro/requests/80dbb1a2-c0a5-486c-a1b9-bdb370393e43/status', 
        'cancel_url':   'https://queue.fal.run/fal-ai/flux-pro/requests/80dbb1a2-c0a5-486c-a1b9-bdb370393e43/cancel', 
        'logs': None, 'metrics': {}, 'queue_position': 0}

        """        
        self.model_name = model_name
        _logger.info(f"    model: {self.model_name}")
        _logger.info(f"    prompt: {prompt}")
        _logger.info(f"    additional_payload: {additional_payload}")
        
        url = f"https://queue.fal.run/{model_name}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Key {self.api_key}",
        }
        payload = {}
        if prompt:
            payload.update({
                "prompt": f"{prompt}"
            })

        if additional_payload:
            payload.update(additional_payload)

        begin = time.time()
        self.last_error=None
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
        except requests.RequestException as e:
            self.last_error = f"fal submit failed: {e}"
            _logger.error("    Submit exception: %s", e)
            return False
        if response.status_code == 200:
            result = response.json()
            _logger.info(f"result={result}")
            self.request_id = result["request_id"]
            self.response_url = result["response_url"]
            self.status_url = result["status_url"]
            _logger.info(f"    Task submitted. Request ID: {self.request_id}")
        else:
            self.last_error = f"fal submit HTTP {response.status_code}: {response.text[:500]}"
            _logger.error("    Submit error: %s, %s", response.status_code, response.text[:500])
            return False

        # check status
        # headers = {"Authorization": f"Key {self.api_key}"}

        # Poll for results
        final_url = False
        max_wait = 600
        while time.time() - begin < max_wait:
            try:
                response = requests.get(self.status_url, headers=headers, timeout=30)
            except requests.RequestException as e:
                self.last_error = f"fal status poll failed: {e}"
                _logger.error("    Status poll exception: %s", e)
                break
            if response.status_code in [200,202]:
                result = response.json()
                status = result["status"]

                if status == "COMPLETED":
                    end = time.time()
                    _logger.info(f"    Task completed in {end - begin} seconds.")
                    self._download_request() # self.final_url filled
                    final_url = self.final_url
                    _logger.info(f"    URL: {final_url}")
                    break
                elif status == 'IN_PROGRESS':
                    _logger.info(f"    Task still processing. Status: {status}")
                elif status == 'IN_QUEUE':
                    _logger.info(f"    Task still in queue. Status: {status}")
                else:
                    self.last_error = f"fal task {status}: {result.get('error') or result.get('logs') or result}"
                    _logger.error("    Task failed/unknown status: %s", self.last_error)
                    break
            else:
                self.last_error = f"fal status poll HTTP {response.status_code}: {response.text[:500]}"
                _logger.error("    Status error: %s, %s", response.status_code, response.text[:500])
                break

            time.sleep(1)
        else:
            self.last_error = f"fal task timed out after {max_wait}s"
            _logger.error("    %s (model=%s)", self.last_error, self.model_name)

        return final_url

    def _download_request(self,):
        self.final_url = False
        headers = {"Authorization": f"Key {self.api_key}"}
        try:
            response = requests.get(self.response_url, headers=headers, timeout=60)
        except requests.RequestException as e:
            self.last_error = f"fal result fetch failed: {e}"
            _logger.error("    Result fetch exception: %s", e)
            return
        if response.status_code in [200,202]:
            result = response.json()
            _logger.info("    result=%s", result)
            images = result.get("images") or []
            if not images:
                self.last_error = f"fal result has no images: {result}"
                _logger.error("    %s", self.last_error)
                return
            self.final_url = images[0].get("url")
        else:
            self.last_error = f"fal result HTTP {response.status_code}: {response.text[:500]}"
            _logger.error("    Result error: %s, %s", response.status_code, response.text[:500])

    # ------------------------------------------------------------------
    # CDN upload
    # ------------------------------------------------------------------
    REST_URL = "https://rest.fal.ai"

    def _cdn_token(self):
        """Short-lived CDN upload token. The API key is not accepted by the
        v3 CDN upload endpoint directly - it needs a scoped token."""
        response = requests.post(
            f"{self.REST_URL}/storage/auth/token?storage_type=fal-cdn-v3",
            headers={
                "Authorization": f"Key {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def _upload_v3(self, data, content_type, file_name):
        token = self._cdn_token()
        response = requests.post(
            f"{token['base_url']}/files/upload",
            headers={
                "Authorization": f"{token['token_type']} {token['token']}",
                "Content-Type": content_type,
                "X-Fal-File-Name": file_name,
            },
            data=data,
            timeout=180,
        )
        response.raise_for_status()
        return response.json()["access_url"]

    def _upload_storage(self, data, content_type, file_name):
        """Fallback repository, authenticated with the API key directly."""
        response = requests.post(
            f"{self.REST_URL}/storage/upload/initiate?storage_type=gcs",
            headers={
                "Authorization": f"Key {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={"file_name": file_name, "content_type": content_type},
            timeout=60,
        )
        response.raise_for_status()
        init = response.json()
        put = requests.put(
            init["upload_url"],
            headers={"Content-Type": content_type},
            data=data,
            timeout=180,
        )
        put.raise_for_status()
        return init["file_url"]

    def upload(self, data, content_type, file_name):
        """Upload raw bytes to the fal CDN and return a public URL.

        fal models reject inline data URIs for real images with image_load_error,
        so reference assets have to be hosted. Mirrors the fal-client SDK:
        primary repository fal_v3, falling back to the REST storage repository.
        """
        errors = []
        for label, attempt in (("fal_v3", self._upload_v3), ("fal", self._upload_storage)):
            try:
                url = attempt(data, content_type, file_name)
                _logger.info("    Uploaded %s via %s: %s", file_name, label, url)
                return url
            except Exception as e:
                errors.append(f"{label}: {e}")
                _logger.warning("    Upload via %s failed: %s", label, e)
        raise RuntimeError("fal CDN upload failed (%s)" % "; ".join(errors))

    def generate_image(self, image_prompt, 
                       model_name='fal-ai/flux-pro', 
                       additional_payload={},):
        _logger.info('Generating image...')
        _logger.info(f'    additional_payload={additional_payload}')
        if not additional_payload:
            additional_payload={
                "aspect_ratio": "9:16",
                "enable_base64_output": False,
                "enable_sync_mode": False,
                "output_format": "png",
            }
        
        url = self.generate(
            model_name=model_name,
            prompt=image_prompt,
            additional_payload=additional_payload
        )
        
        _logger.info(f'    Final Image URL: {url}')
        return url

    def generate_audio(self, text, model_name='elevenlabs/eleven-v3', voice_id="Alice"):
        _logger.info('Generating audio...')

        url = self.generate(
            model_name=model_name,
            prompt=text,
            additional_payload={
                "text":text,
                "similarity": 1,
                "stability": 0.5,
                "use_speaker_boost": True,
                "voice_id": voice_id
            })
        _logger.info('    Final Audio URL', url)
        return url

    def generate_music(self, music_prompt, lyrics="", model_name='minimax/music-02',):
        _logger.info('Generating song...')

        url = self.generate(
            model_name=model_name,
            prompt=music_prompt,
            additional_payload={
                "bitrate": 256000,
                "lyrics": "instrumental",
                "sample_rate": 44100
            }            
        )
        _logger.info('    Final Music URL', url)
        return url

    def generate_video(self, video_prompt, 
                       model_name='bytedance/seedance-v1-pro-fast/text-to-video', 
                       additional_payload={}):
        _logger.info('Generating video...')
        _logger.info(f'   additional_payload={additional_payload}')
        url = self.generate(
            model_name=model_name,
            prompt=video_prompt,
            additional_payload=additional_payload
        )
        _logger.info('    Final Video URL', url)
        return url
