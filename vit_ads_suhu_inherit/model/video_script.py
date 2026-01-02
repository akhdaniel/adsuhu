
#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .libs.openai_lib import *
import json

class video_script(models.Model):

    _name = "vit.video_script"
    _inherit = "vit.video_script"

    def action_generate_prompt(self):
        self.generate_video_prompt()

    def generate_video_prompt(self):
        if not self.video_director_id.gpt_prompt_id:
            raise UserError('Video GPT prompt empty')
        if not self.video_director_id.gpt_model_id:
            raise UserError('Video GPT model empty')
        
        context = f"{self.name} video script. {self.script}"
        additional_command=""
        system_prompt = self.video_director_id.gpt_prompt_id.system_prompt 
        if 'hook' in self.name:
            question = self.video_director_id.main_character or ""
        else:
            question = ""
        user_prompt = self.video_director_id.gpt_prompt_id.user_prompt
        openai_api_key = self.env["ir.config_parameter"].sudo().get_param("openai_api_key")
        openai_base_url = self.env["ir.config_parameter"].sudo().get_param("openai_base_url", None)

        model = self.video_director_id.gpt_model_id.name

        response = generate_content(openai_api_key=openai_api_key, 
                                openai_base_url=openai_base_url, 
                                model=model, 
                                system_prompt=system_prompt, 
                                user_prompt=user_prompt, 
                                context=context, 
                                question=question, 
                                additional_command=additional_command)    

        response = self.video_director_id.clean_md(response)
        response = json.loads(response)
        if not 'video_prompt' in response:
            raise UserError(f'Error from GPT: {response}')
        self.prompt = response['video_prompt']

    def action_generate_video(self):
        print('generate video ')
