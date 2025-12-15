#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ads_copy(models.Model):
    _name = "vit.ads_copy"
    _inherit = "vit.ads_copy"

    def action_generate(self, ):
        pass

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_ads_copy", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "ads_copy")], limit=1
        ).id
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    
    @api.onchange("audience_profiler_id","angle_hook_id")
    def _get_input(self, ):
        """
        {
        @api.depends("audience_profiler_id","angle_hook_id")
        }
        """
        for rec in self:
            hook = len(rec.angle_hook_id.ads_copy_ids)+1
            rec.hook_no = hook
            rec.name = f"AD COPY - ANGLE {rec.angle_hook_id.angle_no} - HOOK {hook}"
            rec.input = f"""

# ✅ ANGLE & HOOK:
---
{rec.angle_hook_id.output}


# ✅ AUDIENCE PROFILE:
---
{rec.audience_profiler_id.output}

"""
