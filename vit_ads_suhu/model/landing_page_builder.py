#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class landing_page_builder(models.Model):

    _name = "vit.landing_page_builder"
    _description = "vit.landing_page_builder"


    def action_generate(self, ):
        pass


    @api.onchange("ads_copy_id","compliance_checker_id","product_value_analysis_id","audience_profiler_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["ads_copy_id","compliance_checker_id","product_value_analysis_id","audience_profiler_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    angle = fields.Text(related="ads_copy_id.angle_hook_id.description",  string=_("Angle"))
    hook = fields.Text(related="ads_copy_id.description",  string=_("Hook"))


    def action_view_detail_campaign_builder_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_campaign_builder")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_campaign_builder_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_campaign_builder_form")
        action["domain"] = [
            ("landing_page_builder_id", "in", self.ids)
        ]
        action["context"] = {
            "default_landing_page_builder_id": self.id
        }
        recs = self.campaign_builder_ids
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

    def compute_campaign_builder_ids(self):
        for rec in self:
            rec.campaign_builder_ids_count = len(rec.campaign_builder_ids)

    campaign_builder_ids_count = fields.Integer(compute="compute_campaign_builder_ids")


    compliance_checker_id = fields.Many2one(comodel_name="vit.compliance_checker",  string=_("Compliance Checker"))
    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy",  string=_("Ads Copy"))
    audience_profiler_id = fields.Many2one(comodel_name="vit.audience_profiler", related="compliance_checker_id.ads_copy_id.audience_profiler_id",  string=_("Audience Profiler"))
    product_value_analysis_id = fields.Many2one(comodel_name="vit.product_value_analysis", related="compliance_checker_id.ads_copy_id.audience_profiler_id.market_mapper_id.product_value_analysis_id",  string=_("Product Value Analysis"))
    campaign_builder_ids = fields.One2many(comodel_name="vit.campaign_builder",  inverse_name="landing_page_builder_id",  string=_("Campaign Builder"))
