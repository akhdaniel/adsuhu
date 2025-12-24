#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
DEFAULT_GENERAL_INSTRUCTION="""You MUST respond with ONLY valid JSON. Do NOT include explanations or extra text. 
If you cannot comply, return an empty JSON object {}. You a free to add list element in the json list as many as needed. 
"""
class general_object(models.Model):
    """
    {
    "sequence": 0
    }
    """

    _name = "vit.general_object"
    _inherit = "vit.general_object"
    
    general_instruction = fields.Text(default=DEFAULT_GENERAL_INSTRUCTION,  string=_("General Instruction"))

    def clean_md(self, text):
        return text.replace("```json","").replace("```","")
    
    def wrap_md(self, text):
        return json.dumps(text, indent=4) 