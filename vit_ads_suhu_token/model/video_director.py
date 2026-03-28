# -*- coding: utf-8 -*-

from odoo import models


class VideoDirector(models.Model):
    _inherit = "vit.video_director"

    def action_generate(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "video", ref_model=rec._name, ref_id=rec.id
            )
            super(VideoDirector, rec).action_generate()
