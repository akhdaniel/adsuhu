#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .libs.fal import Fal
import requests
import base64
import json 

import logging
_logger = logging.getLogger(__name__)


class video_director(models.Model):

    _name = "vit.video_director"
    _inherit = "vit.video_director"

    lang_id = fields.Many2one(comodel_name="res.lang", related="ads_copy_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="ads_copy_id.product_value_analysis_id.partner_id")



    def action_generate(self, ):
        self.generate_output_html()


    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.write_description_prompt", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "Write Description Prompt")], limit=1
        ).id
    

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)

    @api.onchange("visual_concept_id","ads_copy_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["visual_concept_id.output"]
        }
        """
        for rec in self:
            rec.name = f"VIDEO DIRECTOR - ANGLE {rec.ads_copy_id.angle_hook_id.angle_no} - HOOK {rec.ads_copy_id.hook_no}"
            rec.input = f"""
# ✅ ADS COPY:
================
{rec.ads_copy_id.output}


# ✅ VISUAL CONCEPT:
================
{rec.visual_concept_id.output or ''}

"""

    def action_generate_actor(self):
        if not self.main_character:
            raise UserError('Main character empty!')
        api_key = self.env["ir.config_parameter"].sudo().get_param("fal_api_key")        
        fal = Fal(api_key=api_key)
        image_url = fal.generate_image(image_prompt=self.main_character, 
                                       model_name='fal-ai/flux-pro/v1.1-ultra',)
        self.main_actor_url = image_url
        if self.main_actor_url:
            self.download_actor_image()
        
    def download_actor_image(self):
        for rec in self:
            image_url = rec.main_actor_url
            if not image_url :
                continue
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    # response.content sudah berupa bytes
                    rec.main_actor = base64.b64encode(response.content)
                else:
                    # optional: log error / raise warning
                    raise UserError(
                        "Failed to download image from %s, status: %s", image_url, response.status_code
                    )
            except Exception as e:
                # optional: log error
                raise UserError("Error downloading image from %s: %s", image_url, e)
            

    def generate_output_html(self):
        try:
            self.output_html = self.md_to_html(
                self.json_to_markdown(
                    json.loads(self.clean_md(self.output)), level=3, max_level=4
                )
            )
        except Exception as e:
            _logger.error(self.output)
            raise UserError('Failed to generate Output HTML')