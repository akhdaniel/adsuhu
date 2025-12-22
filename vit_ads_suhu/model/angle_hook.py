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


    def action_view_detail_hook_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_hook")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_hook_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_hook_form")
        action["domain"] = [
            ("angle_hook_id", "in", self.ids)
        ]
        action["context"] = {
            "default_angle_hook_id": self.id
        }
        recs = self.hook_ids
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

    def compute_hook_ids(self):
        for rec in self:
            rec.hook_ids_count = len(rec.hook_ids)

    hook_ids_count = fields.Integer(compute="compute_hook_ids")


    def action_view_detail_ads_copy_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_ads_copy")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_ads_copy_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_ads_copy_form")
        action["domain"] = [
            ("angle_hook_id", "in", self.ids)
        ]
        action["context"] = {
            "default_angle_hook_id": self.id
        }
        recs = self.ads_copy_ids
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

    def compute_ads_copy_ids(self):
        for rec in self:
            rec.ads_copy_ids_count = len(rec.ads_copy_ids)

    ads_copy_ids_count = fields.Integer(compute="compute_ads_copy_ids")


    audience_profiler_id = fields.Many2one(comodel_name="vit.audience_profiler",  string=_("Audience Profiler"))
    product_value_analysis_id = fields.Many2one(comodel_name="vit.product_value_analysis", related="audience_profiler_id.market_mapper_id.product_value_analysis_id",  string=_("Product Value Analysis"))
    hook_ids = fields.One2many(comodel_name="vit.hook",  inverse_name="angle_hook_id",  string=_("Hook"))
    ads_copy_ids = fields.One2many(comodel_name="vit.ads_copy",  inverse_name="angle_hook_id",  string=_("Ads Copy"))
