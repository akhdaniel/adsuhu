#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class product_value_analysis(models.Model):

    _name = "vit.product_value_analysis"
    _description = "vit.product_value_analysis"


    def action_fetch_product_description(self, ):
        pass


    def action_write_with_ai(self, ):
        pass


    def action_generate(self, ):
        pass


    def action_generate_report(self, ):
        pass


    def action_download_docx(self, ):
        pass


    def _get_default_prompt(self, ):
        pass


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    product_url = fields.Text( string=_("Product Url"))
    features = fields.Text( string=_("Features"))
    final_report = fields.Text( string=_("Final Report"))
    report_template = fields.Binary( string=_("Report Template"))
    report_template_filename = fields.Char( string=_("Report Template Filename"))
    report_docx = fields.Binary( string=_("Report Docx"))
    report_docx_filename = fields.Char( string=_("Report Docx Filename"))
    target_market = fields.Char( string=_("Target Market"), default="US (Global)")


    def action_view_detail_market_mapper_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("vit_ads_suhu.action_market_mapper")
        view_tree = self.env.ref("vit_ads_suhu.view_vit_market_mapper_tree")
        view_form = self.env.ref("vit_ads_suhu.view_vit_market_mapper_form")
        action["domain"] = [
            ("product_value_analysis_id", "in", self.ids)
        ]
        action["context"] = {
            "default_product_value_analysis_id": self.id
        }
        recs = self.market_mapper_ids
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

    def compute_market_mapper_ids(self):
        for rec in self:
            rec.market_mapper_ids_count = len(rec.market_mapper_ids)

    market_mapper_ids_count = fields.Integer(compute="compute_market_mapper_ids")


    market_mapper_ids = fields.One2many(comodel_name="vit.market_mapper",  inverse_name="product_value_analysis_id",  string=_("Market Mapper"))
    write_gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("Write Gpt Prompt"))
