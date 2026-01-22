#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

class hook(models.Model):

    _name = "vit.hook"
    _inherit = "vit.hook"


    def action_generate(self, ):
        pass
    
    lang_id = fields.Many2one(comodel_name="res.lang", related="angle_hook_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="angle_hook_id.product_value_analysis_id.partner_id")

    # def _get_default_prompt(self):
    #     prompt = self.env.ref("vit_ads_suhu_inherit.gpt_ads_copy", raise_if_not_found=False)
    #     if prompt:
    #         return prompt.id
    #     return self.env["vit.gpt_prompt"].search(
    #         [("name", "=", "ads_copy")], limit=1
    #     ).id
    
    # gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    
    @api.onchange("angle_hook_id")
    def _get_input(self, ):
        """
        {
        }
        """
        for rec in self:
            hook = len(rec.angle_hook_id.hook_ids)+1
            rec.hook_no = hook
            rec.name = f"HOOK {hook} - ANGLE {rec.angle_hook_id.angle_no} "
            rec.input = f"""
# ANGLE:
---
{rec.angle_hook_id.output}

# AUDIENCE PROFILE:
---
{rec.audience_profiler_id.output}

# PRODUCT VALUE:
---
{rec.product_value_analysis_id.output}

# INSTRUCTIONS:
---
{rec.general_instruction}

{rec.specific_instruction or ''}

Response in {self.lang_id.name} language.

"""

    def generate_output_html(self):
        self.output_html = self.json_to_markdown(json.loads(self.clean_md(self.output)), level=2, max_level=3)
