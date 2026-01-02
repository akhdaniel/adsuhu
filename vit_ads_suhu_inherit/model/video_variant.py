#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time

class video_variant(models.Model):

    _name = "vit.video_variant"
    _inherit = "vit.video_variant"

    def _get_default_name(self):
        ap = self.image_generator_id.hook_id.angle_hook_id.audience_profiler_id.audience_profile_no
        angle = self.image_generator_id.hook_id.angle_hook_id.angle_no
        hook = self.image_generator_id.hook_id.hook_no
        ads = 1 #self.image_generator_id.ads_copy_id.hook_no
        ad_copy = self.image_generator_id.ads_copy_no
        return f"AP{ap}-ANGLE{angle}-HOOK{hook}-ADS{ads}-COPY{ad_copy}"

    name = fields.Char(sting="Name", default=_get_default_name)

    def _get_video_url(self, ):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self:
            rec.video_url = f'{base_url}/web/content/vit.video_variant/{rec.id}/video?unique={int(time.time())}'
