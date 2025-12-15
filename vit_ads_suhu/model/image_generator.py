#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class image_generator(models.Model):

    _name = "vit.image_generator"
    _description = "vit.image_generator"


    def action_generate(self, ):
        pass


    @api.onchange("visual_concept_id","image_prompt_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["visual_concept_id","image_prompt_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"


    image_prompt_id = fields.Many2one(comodel_name="vit.image_prompt",  string=_("Image Prompt"))
    visual_concept_id = fields.Many2one(comodel_name="vit.visual_concept",  string=_("Visual Concept"))
