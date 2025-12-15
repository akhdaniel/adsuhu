#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class compliance_checker(models.Model):

    _name = "vit.compliance_checker"
    _description = "vit.compliance_checker"


    def action_generate(self, ):
        pass


    @api.onchange("ads_copy_id","visual_concept_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["ads_copy_id","visual_concept_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"


    def action_view_detail_landing_page_builder_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_landing_page_builder")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_landing_page_builder_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_landing_page_builder_form")
        action["domain"] = [
            ("compliance_checker_id", "in", self.ids)
        ]
        action["context"] = {
            "default_compliance_checker_id": self.id
        }
        recs = self.landing_page_builder_ids
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

    def compute_landing_page_builder_ids(self):
        for rec in self:
            rec.landing_page_builder_ids_count = len(rec.landing_page_builder_ids)

    landing_page_builder_ids_count = fields.Integer(compute="compute_landing_page_builder_ids")


    visual_concept_id = fields.Many2one(comodel_name="vit.visual_concept",  string=_("Visual Concept"))
    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy", related="visual_concept_id.ads_copy_id",  string=_("Ads Copy"))
    landing_page_builder_ids = fields.One2many(comodel_name="vit.landing_page_builder",  inverse_name="compliance_checker_id",  string=_("Landing Page Builder"))
