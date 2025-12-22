#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class angle_hook(models.Model):
    """
    {
    "label":"Angle"
    }
    """

    _name = "vit.angle_hook"
    _description = "vit.angle_hook"


    def action_generate(self, ):
        pass


    def action_split_angles(self, ):
        pass


    def action_create_ad_copy(self, ):
        pass


    @api.onchange("audience_profiler_id","product_value_analysis_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["audience_profiler_id","product_value_analysis_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    angle_no = fields.Integer( string=_("Angle No"))


    audience_profiler_id = fields.Many2one(comodel_name="vit.audience_profiler",  string=_("Audience Profiler"))
    product_value_analysis_id = fields.Many2one(comodel_name="vit.product_value_analysis", related="audience_profiler_id.market_mapper_id.product_value_analysis_id",  string=_("Product Value Analysis"))
    hook_ids = fields.One2many(comodel_name="vit.hook",  inverse_name="angle_hook_id",  string=_("Hook"))
