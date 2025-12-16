#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class campaign_builder(models.Model):

    _name = "vit.campaign_builder"
    _description = "vit.campaign_builder"


    def action_generate(self, ):
        pass


    @api.depends("ads_copy_id.output","script_writer_id.output","visual_concept_id.output","compliance_checker_id.output","landing_page_builder_id.output")
    def _get_input(self, ):
        """
        {
        "@api.depends":["ads_copy_id.output","script_writer_id.output","visual_concept_id.output","compliance_checker_id.output","landing_page_builder_id.output"]
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


    landing_page_builder_id = fields.Many2one(comodel_name="vit.landing_page_builder",  string=_("Landing Page Builder"))
    compliance_checker_id = fields.Many2one(comodel_name="vit.compliance_checker", related="landing_page_builder_id.compliance_checker_id",  string=_("Compliance Checker"))
    visual_concept_id = fields.Many2one(comodel_name="vit.visual_concept", related="landing_page_builder_id.compliance_checker_id.visual_concept_id",  string=_("Visual Concept"))
    script_writer_id = fields.Many2one(comodel_name="vit.script_writer", related="landing_page_builder_id.compliance_checker_id.visual_concept_id.script_writer_id",  string=_("Script Writer"))
    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy", related="landing_page_builder_id.compliance_checker_id.ads_copy_id",  string=_("Ads Copy"))
