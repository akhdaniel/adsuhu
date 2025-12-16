#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class image_generator(models.Model):

    _name = "vit.image_generator"
    _description = "vit.image_generator"


    def action_generate(self, ):
        pass


    @api.onchange("visual_concept_id","image_prompt_id","ads_copy_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["visual_concept_id","image_prompt_id","ads_copy_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    ratio = fields.Selection(selection=[('1:1','1:1'),('9:16','9:16'),('16:9','16:9')], required=True, default="1:1",  string=_("Ratio"))
    angle = fields.Text(related="ads_copy_id.angle_hook_id.description",  string=_("Angle"))
    hook = fields.Text(related="ads_copy_id.description",  string=_("Hook"))


    image_prompt_id = fields.Many2one(comodel_name="vit.image_prompt",  string=_("Image Prompt"))
    visual_concept_id = fields.Many2one(comodel_name="vit.visual_concept",  string=_("Visual Concept"))
    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy",  string=_("Ads Copy"))
    image_variant_ids = fields.One2many(comodel_name="vit.image_variant",  inverse_name="image_generator_id",  string=_("Image Variant"))
