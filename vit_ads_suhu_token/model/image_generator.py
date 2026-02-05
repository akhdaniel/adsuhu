# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class ImageGenerator(models.Model):
    _inherit = "vit.image_generator"

    def action_generate(self):
        self.ensure_one()
        if not self.output or not isinstance(self.output, str):
            raise UserError(
                _("Output kosong. Silakan Generate Ads Copy dulu.")
            )
        self.env.user.consume_ai_tokens(
            "image", ref_model=self._name, ref_id=self.id
        )
        return super().action_generate()
