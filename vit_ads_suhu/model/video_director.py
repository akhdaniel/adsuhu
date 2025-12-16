#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class video_director(models.Model):

    _name = "vit.video_director"
    _description = "vit.video_director"


    def action_generate(self, ):
        pass


    def _get_input(self, ):
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"


    visual_concept_id = fields.Many2one(comodel_name="vit.visual_concept",  string=_("Visual Concept"))
    video_service_id = fields.Many2one(comodel_name="vit.video_service",  string=_("Video Service"))
