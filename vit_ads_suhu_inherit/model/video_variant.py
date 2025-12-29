#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time

class video_variant(models.Model):

    _name = "vit.video_variant"
    _inherit = "vit.video_variant"

    def _get_video_url(self, ):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self:
            rec.video_url = f'{base_url}/web/content/vit.video_variant/{rec.id}/video?unique={int(time.time())}'
