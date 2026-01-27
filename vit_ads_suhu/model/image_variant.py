#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class image_variant(models.Model):
    """
    {
    "inherit_image_mixin":true
    }
    """

    _name = "vit.image_variant"
    _description = "vit.image_variant"

    _inherit = ['image.mixin']

    def _get_image_url(self, ):
        pass


    def action_generate(self, ):
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


    def action_post_telegram(self, ):
        pass


    def action_post_whatsapp(self, ):
        pass


    def _get_lp_url(self, ):
        pass


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    image_1920 = fields.Binary( string=_("Image 1920"))
    image_filename = fields.Char( string=_("Image Filename"))
    image_url = fields.Char(compute="_get_image_url", widget="url",  string=_("Image Url"))
    is_autopost = fields.Boolean( string=_("Is Autopost"))
    autopost_time = fields.Float( string=_("Autopost Time"))
    headline = fields.Text( string=_("Headline"))
    primary_text = fields.Text( string=_("Primary Text"))
    cta = fields.Char(string="CTA")
    tags = fields.Text( string=_("Tags"))
    linkedin_url = fields.Text(string="LinkedIn URL")
    facebook_url = fields.Text(string="Facebook URL")
    ig_url = fields.Text(string="IG URL")
    telegram_url = fields.Text(string="Telegram URL")
    whatsapp_url = fields.Text(string="WhatsApp URL")
    lp_url = fields.Text(compute="_get_lp_url", string="Landing Page URL")


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(image_variant, self).copy(default)

    image_generator_id = fields.Many2one(comodel_name="vit.image_generator",  string=_("Image Generator"))
    auto_post_period_id = fields.Many2one(comodel_name="vit.auto_post_period",  string=_("Auto Post Period"))
