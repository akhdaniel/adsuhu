#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class image_variant(models.Model):

    _name = "vit.image_variant"
    _description = "vit.image_variant"


    def _get_image_url(self, ):
        pass


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


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    image = fields.Binary( string=_("Image"))
    image_filename = fields.Char( string=_("Image Filename"))
    image_url = fields.Char(compute="_get_image_url", widget="url",  string=_("Image Url"))
    is_autopost = fields.Boolean( string=_("Is Autopost"))
    autopost_time = fields.Float( string=_("Autopost Time"))
    headline = fields.Text( string=_("Headline"))
    primary_text = fields.Text( string=_("Primary Text"))
    cta = fields.Char(string="CTA")
    tags = fields.Text( string=_("Tags"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(image_variant, self).copy(default)

    image_generator_id = fields.Many2one(comodel_name="vit.image_generator",  string=_("Image Generator"))
    auto_post_period_id = fields.Many2one(comodel_name="vit.auto_post_period",  string=_("Auto Post Period"))
