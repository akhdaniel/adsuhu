#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class image_variant(models.Model):

    _name = "vit.image_variant"
    _description = "vit.image_variant"


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    image = fields.Binary( string=_("Image"))
    image_filename = fields.Char( string=_("Image Filename"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(image_variant, self).copy(default)

    image_generator_id = fields.Many2one(comodel_name="vit.image_generator",  string=_("Image Generator"))
