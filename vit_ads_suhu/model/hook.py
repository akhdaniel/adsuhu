#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class hook(models.Model):

    _name = "vit.hook"
    _description = "vit.hook"


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    hook_no = fields.Integer( string=_("Hook No"))


    def action_view_detail_ads_copy_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_ads_copy")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_ads_copy_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_ads_copy_form")
        action["domain"] = [
            ("hook_id", "in", self.ids)
        ]
        action["context"] = {
            "default_hook_id": self.id
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


    ads_copy_ids = fields.One2many(comodel_name="vit.ads_copy",  inverse_name="hook_id",  string=_("Ads Copy"))
    angle_hook_id = fields.Many2one(comodel_name="vit.angle_hook", string="Angle")
    audience_profiler_id = fields.Many2one(comodel_name="vit.audience_profiler", related="angle_hook_id.audience_profiler_id",  string=_("Audience Profiler"))
    product_value_analysis_id = fields.Many2one(comodel_name="vit.product_value_analysis", related="angle_hook_id.product_value_analysis_id",  string=_("Product Value Analysis"))
