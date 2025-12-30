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
    angle = fields.Text(related="ads_copy_id.angle_hook_id.description",  string=_("Angle"))
    hook = fields.Text(related="ads_copy_id.hook_id.description",  string=_("Hook"))
    main_actor = fields.Binary( string=_("Main Actor"))
    main_actor_filename = fields.Char( string=_("Main Actor Filename"))


    visual_concept_id = fields.Many2one(comodel_name="vit.visual_concept",  string=_("Visual Concept"))
    video_service_id = fields.Many2one(comodel_name="vit.video_service",  string=_("Video Service"))
    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy",  string=_("Ads Copy"))
    video_variant_ids = fields.One2many(comodel_name="vit.video_variant",  inverse_name="video_director_id",  string=_("Video Variant"))
    video_script_ids = fields.One2many(comodel_name="vit.video_script",  inverse_name="video_director_id",  string=_("Video Script"))
    hook_id = fields.Many2one(comodel_name="vit.hook", related="ads_copy_id.hook_id",  string=_("Hook"))
