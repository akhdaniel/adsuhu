#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class general_object(models.Model):
    """
    {
    "sequence": 0
    }
    """

    _name = "vit.general_object"
    _description = "vit.general_object"


    def reformat_output(self, ):
        pass


    def generate_output_html(self, ):
        pass


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    output_html = fields.Text( string=_("Output Html"))
    output = fields.Text( string=_("Output"))
    input = fields.Text( string=_("Input"))
    gpt_url = fields.Char(related="gpt_prompt_id.gpt_url", string="GPT URL")
    description = fields.Text( string=_("Description"))
    general_instruction = fields.Text(default="You MUST respond with ONLY valid JSON. Do NOT include explanations, markdown, or extra text. If you cannot comply, return an empty JSON object {}.",  string=_("General Instruction"))
    specific_instruction = fields.Text( string=_("Specific Instruction"))
    active = fields.Boolean( string=_("Active"), default=True)
    gpt_session = fields.Char(required=True, string="GPT Session URL")


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(general_object, self).copy(default)

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt", string="GPT Prompt")
    lang_id = fields.Many2one(comodel_name="res.lang", required=True,  string=_("Lang"))
    partner_id = fields.Many2one(comodel_name="res.partner",  string=_("Partner"))
    gpt_model_id = fields.Many2one(comodel_name="vit.gpt_model", string="GPT Model")
