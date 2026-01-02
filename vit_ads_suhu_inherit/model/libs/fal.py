
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
        _logger.info(f"    payload: {additional_payload}")
        
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
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            print(result)
            self.request_id = result["request_id"]
            self.response_url = result["response_url"]
            self.status_url = result["status_url"]
            _logger.info(f"    Task submitted. Request ID: {self.request_id}")
        else:
            _logger.info(f"    Error: {response.status_code}, {response.text}")
            return

        # check status
        # headers = {"Authorization": f"Key {self.api_key}"}

        # Poll for results
        final_url = False
        while True:
            response = requests.get(self.status_url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                status = result["status"]

                if status == "COMPLETED":
                    end = time.time()
                    _logger.info(f"    Task completed in {end - begin} seconds.")
                    self._download_request(self.request_id)
                    final_url = self.response_url
                    _logger.info(f"    URL: {final_url}")
                    break
                elif status == 'IN_PROGRESS':
                    _logger.info(f"    Task still processing. Status: {status}")
                elif status == 'IN_QUEUE':
                    _logger.info(f"    Task still in queue. Status: {status}")
                else:
                    _logger.info(f"    Task failed/unknown status: {result.get('error')}")
                    break                    
            else:
                _logger.info(f"    Error: {response.status_code}, {response.text}")
                break

            time.sleep(1)

        return final_url

    def _download_request(self, request_id):
        
        headers = {"Authorization": f"Key {self.api_key}"}
        response = requests.get(self.request_url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print('---- result --- ')
            print(result)
            return '-'
        else:
            _logger.info(f"    Error: {response.status_code}, {response.text}")

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
        
        _logger.info('    Final Image URL', url)
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
