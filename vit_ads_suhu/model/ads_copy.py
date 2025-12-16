#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ads_copy(models.Model):

    _name = "vit.ads_copy"
    _description = "vit.ads_copy"


    def action_generate(self, ):
        pass


    @api.onchange("audience_profiler_id","angle_hook_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["audience_profiler_id","angle_hook_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    hook_no = fields.Integer( string=_("Hook No"))


    def action_view_detail_script_writer_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_script_writer")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_script_writer_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_script_writer_form")
        action["domain"] = [
            ("ads_copy_id", "in", self.ids)
        ]
        action["context"] = {
            "default_ads_copy_id": self.id
        }
        recs = self.script_writer_ids
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

    def compute_script_writer_ids(self):
        for rec in self:
            rec.script_writer_ids_count = len(rec.script_writer_ids)

    script_writer_ids_count = fields.Integer(compute="compute_script_writer_ids")


    def action_view_detail_image_generator_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_image_generator")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_image_generator_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_image_generator_form")
        action["domain"] = [
            ("ads_copy_id", "in", self.ids)
        ]
        action["context"] = {
            "default_ads_copy_id": self.id
        }
        recs = self.image_generator_ids
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

    def compute_image_generator_ids(self):
        for rec in self:
            rec.image_generator_ids_count = len(rec.image_generator_ids)

    image_generator_ids_count = fields.Integer(compute="compute_image_generator_ids")


    angle_hook_id = fields.Many2one(comodel_name="vit.angle_hook", string="Angle")
    audience_profiler_id = fields.Many2one(comodel_name="vit.audience_profiler", related="angle_hook_id.audience_profiler_id",  string=_("Audience Profiler"))
    script_writer_ids = fields.One2many(comodel_name="vit.script_writer",  inverse_name="ads_copy_id",  string=_("Script Writer"))
    image_generator_ids = fields.One2many(comodel_name="vit.image_generator",  inverse_name="ads_copy_id",  string=_("Image Generator"))
