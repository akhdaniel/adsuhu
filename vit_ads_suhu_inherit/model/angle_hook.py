#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class angle_hook(models.Model):
    _name = "vit.angle_hook"
    _inherit = "vit.angle_hook"

    def action_generate(self, ):
        pass

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_angle_hook", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "angle_hook")], limit=1
        ).id
    
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)

    @api.onchange("audience_profiler_id","product_value_analysis_id")
    def _get_input(self, ):
        """
        {
        @api.onchange("audience_profiler_id","product_value_analysis_id")
        }
        """
        for rec in self:
            index = len(rec.audience_profiler_id.angle_hook_ids)+1
            rec.angle_no = index
            rec.name = f"ANGLE {index} - {rec.product_value_analysis_id.name}"
            rec.input = f"""
# ✅ AUDIENCE PROFILE:
---
{rec.audience_profiler_id.output}

# ✅ PRODUCT VALUE:
---
{rec.product_value_analysis_id.output}

"""
