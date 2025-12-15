#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class script_writer(models.Model):
    _name = "vit.script_writer"
    _inherit = "vit.script_writer"

    def action_generate(self, ):
        pass


    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_script_writer", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "script_writer")], limit=1
        ).id
    

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("Gpt Prompt"), default=_get_default_prompt)

    @api.onchange("ads_copy_id","angle_hook_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["ads_copy_id.output","angle_hook_id.output"]
        }
        """
        for rec in self:
            rec.name = f"SCRIPT - ANGLE {rec.angle_hook_id.angle_no} - HOOK {rec.ads_copy_id.hook_no}"
            rec.input = f"""
# ✅ ADS COPY:
================
{rec.ads_copy_id.output}

"""
