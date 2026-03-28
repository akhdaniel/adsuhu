# -*- coding: utf-8 -*-

from odoo import models


class VideoScript(models.Model):
    _inherit = "vit.video_script"

    def generate_video_prompt(self):
        for rec in self:
            rec.env.user.consume_ai_tokens(
                "script", ref_model=rec._name, ref_id=rec.id
            )
            super(VideoScript, rec).generate_video_prompt()
