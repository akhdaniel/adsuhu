#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class visual_concept(models.Model):

    _name = "vit.visual_concept"
    _description = "vit.visual_concept"


    def action_generate(self, ):
        pass


    @api.onchange("ads_copy_id","script_writer_id","audience_profiler_id")
    def _get_input(self, ):
        """
        {
        "@api.onchange":["ads_copy_id","script_writer_id","audience_profiler_id"]
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


    def action_view_detail_compliance_checker_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_compliance_checker")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_compliance_checker_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_compliance_checker_form")
        action["domain"] = [
            ("visual_concept_id", "in", self.ids)
        ]
        action["context"] = {
            "default_visual_concept_id": self.id
        }
        recs = self.compliance_checker_ids
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

    def compute_compliance_checker_ids(self):
        for rec in self:
            rec.compliance_checker_ids_count = len(rec.compliance_checker_ids)

    compliance_checker_ids_count = fields.Integer(compute="compute_compliance_checker_ids")


    def action_view_detail_image_prompt_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_image_prompt")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_image_prompt_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_image_prompt_form")
        action["domain"] = [
            ("visual_concept_id", "in", self.ids)
        ]
        action["context"] = {
            "default_visual_concept_id": self.id
        }
        recs = self.image_prompt_ids
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

    def compute_image_prompt_ids(self):
        for rec in self:
            rec.image_prompt_ids_count = len(rec.image_prompt_ids)

    image_prompt_ids_count = fields.Integer(compute="compute_image_prompt_ids")


    def action_view_detail_video_director_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_video_director")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_video_director_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_video_director_form")
        action["domain"] = [
            ("visual_concept_id", "in", self.ids)
        ]
        action["context"] = {
            "default_visual_concept_id": self.id
        }
        recs = self.video_director_ids
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

    def compute_video_director_ids(self):
        for rec in self:
            rec.video_director_ids_count = len(rec.video_director_ids)

    video_director_ids_count = fields.Integer(compute="compute_video_director_ids")


    script_writer_id = fields.Many2one(comodel_name="vit.script_writer",  string=_("Script Writer"))
    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy", related="script_writer_id.ads_copy_id",  string=_("Ads Copy"))
    audience_profiler_id = fields.Many2one(comodel_name="vit.audience_profiler", related="script_writer_id.ads_copy_id.audience_profiler_id",  string=_("Audience Profiler"))
    compliance_checker_ids = fields.One2many(comodel_name="vit.compliance_checker",  inverse_name="visual_concept_id",  string=_("Compliance Checker"))
    image_prompt_ids = fields.One2many(comodel_name="vit.image_prompt",  inverse_name="visual_concept_id",  string=_("Image Prompt"))
    video_director_ids = fields.One2many(comodel_name="vit.video_director",  inverse_name="visual_concept_id",  string=_("Video Director"))
