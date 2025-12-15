#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class market_mapper(models.Model):
    _name = "vit.market_mapper"
    _inherit = "vit.market_mapper"

    def action_generate(self, ):
        pass


    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_market_mapper", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "market_mapper")], limit=1
        ).id
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    
    @api.onchange("product_value_analysis_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["product_value_analysis_id.output"]
        }
        """
        for rec in self:
            rec.name = f"MARKET MAP - {rec.product_value_analysis_id.name}"
            rec.input = f"""
# ✅ PROODUCT VALUE:
================
{rec.product_value_analysis_id.output}

"""
