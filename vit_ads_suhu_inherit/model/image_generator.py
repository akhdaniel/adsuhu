#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
import logging
_logger = logging.getLogger(__name__)
from .libs.openai_lib import generate_image
import json 
DEFAULT_SPECIFIC_INSTRUCTION = "Langsung Create PNG image, ratio 1:1. Jangan terlalu banyak text, pilih yang paling kuat dari primary text, hook library, dan angle library."

class image_generator(models.Model):
    _name = "vit.image_generator"
    _inherit = "vit.image_generator"
    specific_instruction = fields.Text( string=_("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)

    def action_generate(self, ):

        if not self.gpt_prompt_id:
            raise UserError('Image GPT empty')
        if not self.gpt_model_id:
            raise UserError('GPT model empty')

        openai_api_key = self.env["ir.config_parameter"].sudo().get_param("openai_api_key")
        openai_base_url = None

        model = self.gpt_model_id.name

        user_prompt = self.gpt_prompt_id.user_prompt
        user_prompt += f"{self.output}\n"
        system_prompt = self.gpt_prompt_id.system_prompt 

        context = ""
        additional_command=""
        question = ""

        response = generate_image(openai_api_key=openai_api_key, 
                                openai_base_url=openai_base_url, 
                                model=model, 
                                system_prompt=system_prompt, 
                                user_prompt=user_prompt, 
                                context=context, 
                                question=question, 
                                additional_command=additional_command)    

        v = self.env['vit.image_variant'].create({
            'image_generator_id':self.id,
            'name': '/',
            'image_1920': response,
        })
        v._get_default_name()

    lang_id = fields.Many2one(comodel_name="res.lang", related="ads_copy_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="ads_copy_id.product_value_analysis_id.partner_id")

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_image_generator", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "image_generator")], limit=1
        ).id
    
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)

    @api.onchange("ads_copy_id","specific_instruction")
    def _get_input(self, ):
        """
        {
        }
        """
        for rec in self:
            rec.name = f"IMAGE - ANGLE {rec.ads_copy_id.angle_hook_id.angle_no} - HOOK {rec.ads_copy_id.hook_no}"
            rec.input = f"""

# ✅ ADS COPY:
{rec.ads_copy_id.output}

# ✅ PRODUCT VALUE:
================
{rec.ads_copy_id.audience_profiler_id.market_mapper_id.product_value_analysis_id.output}

# INSTRUCTIONS:
---
{rec.general_instruction}

{rec.specific_instruction or ''}

Response in {self.lang_id.name} language.

"""

    def generate_output_html(self):
        res = self.json_to_markdown(json.loads(self.clean_md(self.output)), level=2, max_level=3)
        self.output_html = self.md_to_html(res)
