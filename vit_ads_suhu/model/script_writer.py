#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class script_writer(models.Model):

    _name = "vit.script_writer"
    _description = "vit.script_writer"


    def action_generate(self, ):
        pass


    @api.onchange("ads_copy_id","angle_hook_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["ads_copy_id","angle_hook_id"]
        }
        """
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    angle = fields.Text(related="angle_hook_id.description",  string=_("Angle"))
    hook = fields.Text(related="ads_copy_id.description",  string=_("Hook"))


    def action_view_detail_visual_concept_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_visual_concept")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_visual_concept_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_visual_concept_form")
        action["domain"] = [
            ("script_writer_id", "in", self.ids)
        ]
        action["context"] = {
            "default_script_writer_id": self.id
        }
        recs = self.visual_concept_ids
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

    def compute_visual_concept_ids(self):
        for rec in self:
            rec.visual_concept_ids_count = len(rec.visual_concept_ids)

    visual_concept_ids_count = fields.Integer(compute="compute_visual_concept_ids")


    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy",  string=_("Ads Copy"))
    angle_hook_id = fields.Many2one(comodel_name="vit.angle_hook", string="Angle", related="ads_copy_id.angle_hook_id")
    visual_concept_ids = fields.One2many(comodel_name="vit.visual_concept",  inverse_name="script_writer_id",  string=_("Visual Concept"))
