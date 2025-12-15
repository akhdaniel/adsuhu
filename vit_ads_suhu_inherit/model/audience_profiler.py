#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class audience_profiler(models.Model):
    _name = "vit.audience_profiler"
    _inherit = "vit.audience_profiler"

    def action_generate(self, ):
        pass


    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_audience_profiler", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "audience_profiler")], limit=1
        ).id
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    

    @api.onchange("market_mapper_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["market_mapper_id.output"]
        }
        """
        for rec in self:
            rec.name = f"AUDIENCE PROFILE - {rec.market_mapper_id.product_value_analysis_id.name}"
            rec.input = f"""
# ✅ MARKET MAP:
---
{rec.market_mapper_id.output}

"""
