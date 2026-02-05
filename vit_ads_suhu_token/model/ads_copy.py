# -*- coding: utf-8 -*-

from odoo import models


class AdsCopy(models.Model):
    _inherit = "vit.ads_copy"

    def action_generate(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "script", ref_model=rec._name, ref_id=rec.id
            )
            super(AdsCopy, rec).action_generate()
