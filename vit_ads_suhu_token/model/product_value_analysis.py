# -*- coding: utf-8 -*-

from odoo import models


class ProductValueAnalysis(models.Model):
    _inherit = "vit.product_value_analysis"

    def action_generate(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "script", ref_model=rec._name, ref_id=rec.id
            )
            super(ProductValueAnalysis, rec).action_generate()

    def action_write_with_ai(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "script", ref_model=rec._name, ref_id=rec.id
            )
            super(ProductValueAnalysis, rec).action_write_with_ai()
