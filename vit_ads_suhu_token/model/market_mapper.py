# -*- coding: utf-8 -*-

from odoo import models


class MarketMapper(models.Model):
    _inherit = "vit.market_mapper"

    def action_generate(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "script", ref_model=rec._name, ref_id=rec.id
            )
            super(MarketMapper, rec).action_generate()
