#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time

class image_variant(models.Model):

    _name = "vit.image_variant"
    _inherit = "vit.image_variant"
    def _get_image_url(self, ):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self:
            rec.image_url = f'{base_url}/web/image/vit.image_variant/{rec.id}/image?unique={int(time.time())}'
