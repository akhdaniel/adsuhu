
import os
import json
import time
import logging
_logger = logging.getLogger(__name__)

class Fal:
    def __init__(self, api_key=None):
        self.api_key=api_key

    def generate(self, model_name, prompt, additional_payload={} ):
        _logger.info(f"    model: {model_name}")
        _logger.info(f"    prompt: {prompt}")
        _logger.info(f"    payload: {additional_payload}")

        url = f"https://api.wavespeed.ai/api/v3/{model_name}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
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
            result = response.json()["data"]
            request_id = result["id"]
            _logger.info(f"    Task submitted. Request ID: {request_id}")
        else:
            _logger.info(f"    Error: {response.status_code}, {response.text}")
            return

        url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Poll for results
        while True:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()["data"]
                status = result["status"]

                if status == "completed":
                    end = time.time()
                    _logger.info(f"    Task completed in {end - begin} seconds.")
                    final_url = result["outputs"][0]
                    _logger.info(f"    URL: {final_url}")
                    break
                elif status == "failed":
                    _logger.info(f"    Task failed: {result.get('error')}")
                    break
                else:
                    _logger.info(f"    Task still processing. Status: {status}")
            else:
                _logger.info(f"    Error: {response.status_code}, {response.text}")
                break

            time.sleep(1)

        return final_url

    def generate_image(self, image_prompt, model_name='google/nano-banana/text-to-image', additional_payload={},):
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
