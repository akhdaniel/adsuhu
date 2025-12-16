#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class visual_concept(models.Model):
    _name = "vit.visual_concept"
    _inherit = "vit.visual_concept"

    def action_generate(self, ):
        pass


    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_visual_concept", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "visual_concept")], limit=1
        ).id
    
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)



    @api.onchange("ads_copy_id","script_writer_id","audience_profiler_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["ads_copy_id.output","script_writer_id.output","audience_profiler_id.output"]
        }
        """
        for rec in self:
            rec.name = f"VISUAL CONCEPT - ANGLE {rec.script_writer_id.angle_hook_id.angle_no} - HOOK {rec.ads_copy_id.hook_no}"
            rec.input = f"""
# ✅ SCRIPT:
---
{rec.script_writer_id.output}

# ✅ ADS COPY:
---
{rec.ads_copy_id.output}

# ✅ AUDIENCE PROFILE:
---
{rec.audience_profiler_id.output}

"""
