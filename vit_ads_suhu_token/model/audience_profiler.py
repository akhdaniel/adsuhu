# -*- coding: utf-8 -*-

from odoo import models


class AudienceProfiler(models.Model):
    _inherit = "vit.audience_profiler"

    def action_generate(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "script", ref_model=rec._name, ref_id=rec.id
            )
            super(AudienceProfiler, rec).action_generate()
