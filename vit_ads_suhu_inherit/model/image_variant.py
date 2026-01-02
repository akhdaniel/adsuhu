#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
import json

class image_variant(models.Model):

    _name = "vit.image_variant"
    _inherit = "vit.image_variant"


    @api.onchange("image_generator_id")
    def _get_default_name(self):
        ap = self.image_generator_id.hook_id.angle_hook_id.audience_profiler_id.audience_profile_no
        angle = self.image_generator_id.hook_id.angle_hook_id.angle_no
        hook = self.image_generator_id.hook_id.hook_no
        ads = 1 #self.image_generator_id.ads_copy_id.hook_no
        ad_copy = self.image_generator_id.ads_copy_no
        self.name = f"AP{ap}-ANGLE{angle}-HOOK{hook}-ADS{ads}-COPY{ad_copy}"

        body = json.loads(self.image_generator_id.output)
        self.headline = body["headline"]
        self.primary_text = body["primary_text"]
        self.cta = body["cta"]
    

    def _get_image_url(self, ):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self:
            rec.image_url = f'{base_url}/web/image/vit.image_variant/{rec.id}/image?unique={int(time.time())}'

    def action_post_linkedin(self, ):
        pass


    def action_post_facebook(self, ):
        pass


    def action_post_ig(self, ):
        """
        {
        "label":"Post IG"
        }
        """
        pass