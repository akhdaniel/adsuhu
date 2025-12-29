#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
import logging
_logger = logging.getLogger(__name__)

DEFAULT_SPECIFIC_INSTRUCTION = "Langsung Create PNG image, ratio 1:1. Jangan terlalu banyak text, pilih yang paling kuat dari primary text, hook library, dan angle library."

class image_generator(models.Model):
    _name = "vit.image_generator"
    _inherit = "vit.image_generator"
    specific_instruction = fields.Text( string=_("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)

    def action_generate(self, ):
        pass


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

    @api.onchange("visual_concept_id","image_prompt_id","ads_copy_id","specific_instruction")
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


# ✅ VISUAL CONCEPT:
================
{rec.visual_concept_id.output}

# ✅ PRODUCT VALUE:
================
{rec.ads_copy_id.audience_profiler_id.market_mapper_id.product_value_analysis_id.output}

# INSTRUCTIONS:
---
{rec.general_instruction}

{rec.specific_instruction or ''}

Response in {self.lang_id.name} language.

"""
