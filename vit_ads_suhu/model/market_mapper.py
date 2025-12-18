#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class market_mapper(models.Model):

    _name = "vit.market_mapper"
    _description = "vit.market_mapper"


    def action_generate(self, ):
        pass


    @api.onchange("product_value_analysis_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":"product_value_analysis_id"
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_create_audience_profiles(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"


    def action_view_detail_audience_profiler_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_audience_profiler")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_audience_profiler_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_audience_profiler_form")
        action["domain"] = [
            ("market_mapper_id", "in", self.ids)
        ]
        action["context"] = {
            "default_market_mapper_id": self.id
        }
        recs = self.audience_profiler_ids
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

    def compute_audience_profiler_ids(self):
        for rec in self:
            rec.audience_profiler_ids_count = len(rec.audience_profiler_ids)

    audience_profiler_ids_count = fields.Integer(compute="compute_audience_profiler_ids")


    product_value_analysis_id = fields.Many2one(comodel_name="vit.product_value_analysis",  string=_("Product Value Analysis"))
    audience_profiler_ids = fields.One2many(comodel_name="vit.audience_profiler",  inverse_name="market_mapper_id",  string=_("Audience Profiler"))
