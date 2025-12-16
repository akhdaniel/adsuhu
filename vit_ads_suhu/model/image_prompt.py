#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class image_prompt(models.Model):

    _name = "vit.image_prompt"
    _description = "vit.image_prompt"


    def action_generate_image(self, ):
        pass


    def action_generate_video(self, ):
        pass


    def action_reload_view(self):
        pass

    prompt = fields.Text( string=_("Prompt"))
    image = fields.Binary( string=_("Image"))
    image_filename = fields.Char( string=_("Image Filename"))
    name = fields.Char( required=True, copy=False, string=_("Name"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(image_prompt, self).copy(default)

    visual_concept_id = fields.Many2one(comodel_name="vit.visual_concept",  string=_("Visual Concept"))
    image_generator_id = fields.Many2one(comodel_name="vit.image_service",  string=_("Image Generator"))
