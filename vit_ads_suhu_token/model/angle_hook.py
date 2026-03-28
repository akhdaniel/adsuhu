# -*- coding: utf-8 -*-

from odoo import models


class AngleHook(models.Model):
    _inherit = "vit.angle_hook"

    def action_generate(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "script", ref_model=rec._name, ref_id=rec.id
            )
            super(AngleHook, rec).action_generate()
