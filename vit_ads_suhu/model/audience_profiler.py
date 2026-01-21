#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class audience_profiler(models.Model):

    _name = "vit.audience_profiler"
    _description = "vit.audience_profiler"


    def action_generate(self, ):
        """
        {
            "xml:confirm":"Are you sure to re-generate Audience Profiler Output?"
        }
        """
        pass


    @api.onchange("market_mapper_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["market_mapper_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    alasan = fields.Text(string="Reason")
    audience_profile_no = fields.Integer( string=_("Audience Profile No"))


    def action_view_detail_angle_hook_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_angle_hook")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_angle_hook_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_angle_hook_form")
        action["domain"] = [
            ("audience_profiler_id", "in", self.ids)
        ]
        action["context"] = {
            "default_audience_profiler_id": self.id
        }
        recs = self.angle_hook_ids
        if len(recs) <= 1:
            action["views"] = [(view_form.id, "form")]
            action["view_mode"] = "form"
            action["view_id"] = view_form.id
            action["res_id"] = recs.id if recs else False
        else:
            action["views"] = [(view_tree.id, "list"), (view_form.id, "form")]
            action["view_mode"] = "list,form"
            action["view_id"] = view_tree.id
            action["res_id"] = False
        return action

    def compute_angle_hook_ids(self):
        for rec in self:
            rec.angle_hook_ids_count = len(rec.angle_hook_ids)

    angle_hook_ids_count = fields.Integer(compute="compute_angle_hook_ids")


    market_mapper_id = fields.Many2one(comodel_name="vit.market_mapper",  string=_("Market Mapper"))
    product_value_analysis_id = fields.Many2one(comodel_name="vit.product_value_analysis", related="market_mapper_id.product_value_analysis_id", store=True,  string=_("Product Value Analysis"))
    angle_hook_ids = fields.One2many(comodel_name="vit.angle_hook",  inverse_name="audience_profiler_id",  string=_("Angle Hook"))
