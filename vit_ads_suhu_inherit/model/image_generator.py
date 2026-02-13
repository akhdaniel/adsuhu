#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
import logging
_logger = logging.getLogger(__name__)
# from .libs.openai_lib import generate_image
from .libs.fal import Fal
import requests
import base64
import json 
import math

DEFAULT_SPECIFIC_INSTRUCTION = "Langsung Create PNG image, ratio 1:1. Jangan terlalu banyak text, pilih yang paling kuat dari primary text, hook library, dan angle library."

class image_generator(models.Model):
    _name = "vit.image_generator"
    _inherit = "vit.image_generator"
    specific_instruction = fields.Text( string=("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)

    def action_generate(self, ):

        if not self.gpt_prompt_id:
            raise UserError('Image GPT empty')
        if not self.gpt_model_id:
            raise UserError('GPT model empty')

        # openai_api_key = self.env["ir.config_parameter"].sudo().get_param("openai_api_key")
        # openai_base_url = None

        image_model = self.env.ref('vit_ads_suhu_inherit.gpt_model_gpt_image_1_5')

        # model = self.gpt_model_id.name
        model = image_model.name

        output = json.loads(self.output)
        headline = output['headline']
        primary_text = output['primary_text']
        cta = output['cta']
        visual_concept = output['visual_suggestion']
        brand_personality = "Professional"

        image_prompt = self.gpt_prompt_id.system_prompt
        image_prompt = (image_prompt
                       .replace('{campaign_objective}', 'Sales')
                       .replace('{target_audience}', 'UMKM')
                       .replace('{headline}', headline)
                       .replace('{primary_text}', primary_text)
                       .replace('{cta}', cta)
                       .replace('{visual_concept}', visual_concept)
                       .replace('{brand_personality}', brand_personality)
                       )

        def _count_input_tokens(text):
            words = len((text or "").split())
            return words * 4

        def _get_image_cost_usd(quality, size):
            pricing = {
                "medium": {
                    "1024x1024": 0.034,
                    "1024x1536": 0.051,
                    "1536x1024": 0.050,
                },
                "high": {
                    "1024x1024": 0.133,
                    "1024x1536": 0.200,
                    "1536x1024": 0.199,
                },
            }
            return pricing.get(quality, pricing["medium"]).get(size, 0.034)

        params = self.env["ir.config_parameter"].sudo()
        usd_to_idr = float(params.get_param("image_usd_to_idr", "17000"))
        image_quality = (params.get_param("image_quality", "medium") or "medium").lower()
        image_size = params.get_param("image_size", "1024x1024") or "1024x1024"

        input_tokens = _count_input_tokens(image_prompt)
        input_cost_usd = (input_tokens / 1000.0) * 0.005
        image_cost_usd = _get_image_cost_usd(image_quality, image_size)
        total_cost_idr = (input_cost_usd + image_cost_usd) * usd_to_idr
        resale_cost_idr = total_cost_idr * 2  # 100% margin
        credits_used = resale_cost_idr # Rp // int(math.ceil(resale_cost_idr / 100.0))
        if self.partner_id and (self.partner_id.customer_limit or 0) < credits_used:
            raise UserError('Not enough credit')

        fal_api_key = self.env["ir.config_parameter"].sudo().get_param("fal_api_key")
        fal = Fal(api_key=fal_api_key)

        image_url = fal.generate_image(image_prompt=image_prompt, 
                       model_name=model, 
                       additional_payload={},)
        
        if not image_url:
            raise UserError('fal Image URL Empty!')
        
        response = requests.get(image_url)
        response.raise_for_status()
        image_b64 = base64.b64encode(response.content).decode("utf-8")

        v = self.env['vit.image_variant'].create({
            'image_generator_id':self.id,
            'name': '/',
            'image_1920': image_b64,
        })
        v._get_default_name()
        self.generate_output_html()

        self.env['vit.topup.service'].create_usage_credit(
            self.partner_id,
            name=f"image_generation:{self.id}",
            credit=-credits_used,
        )

    lang_id = fields.Many2one(comodel_name="res.lang", related="ads_copy_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="ads_copy_id.product_value_analysis_id.partner_id")

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_image_generator", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "image_generator")], limit=1
        ).id
    
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=("GPT Prompt"), default=_get_default_prompt)

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
        try:
            self.output_html = self.md_to_html(
                self.json_to_markdown(
                    json.loads(self.clean_md(self.output)), level=3, max_level=4
                )
            )
        except Exception as e:
            _logger.error(self.output)
            raise UserError('Failed to generate Output HTML')
        
        # md = self.json_to_markdown(
        #         json.loads(self.clean_md(self.output)), level=3, max_level=4
        #     )
        # append image variants 
        # variants = []
        # for v in self.image_variant_ids:
        #     variants.append(f"![{v.name}]({v.image_url})")
        #     variants.append(f"Image: [{v.image_url}]({v.image_url})")
        #     if v.lp_url:
        #         variants.append(f"Landing Page: [{v.lp_url}]({v.lp_url})\n")
        #     else:
        #         variants.append(f"Landing Page: -")

        # md += "\n\n"
        # md += "## Image Variants\n\n"
        # md += "\n".join(variants)

        # self.output_html = self.md_to_html(md)
