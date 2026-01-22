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
    lp_url = fields.Text(string="LP URL", widget="url")


    compliance_checker_id = fields.Many2one(comodel_name="vit.compliance_checker",  string=_("Compliance Checker"))
    ads_copy_id = fields.Many2one(comodel_name="vit.ads_copy",  string=_("Ads Copy"))
    audience_profiler_id = fields.Many2one(comodel_name="vit.audience_profiler", related="compliance_checker_id.ads_copy_id.audience_profiler_id",  string=_("Audience Profiler"))
    campaign_builder_ids = fields.One2many(comodel_name="vit.campaign_builder",  inverse_name="landing_page_builder_id",  string=_("Campaign Builder"))
