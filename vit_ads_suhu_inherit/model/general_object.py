#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import re
import unicodedata

UNICODE_ASCII_MAP = {
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2015": "-",  # horizontal bar
    "\u2212": "-",  # minus sign
    "\u2010": "-",  # hyphen
    "\u2011": "-",  # non-breaking hyphen
    "\u00a0": " ",  # non-breaking space
    "\u200b": "",   # zero width space
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u2026": "...",  # ellipsis
}
DEFAULT_GENERAL_INSTRUCTION="""You MUST respond with ONLY valid JSON. 
ONLY plain ASCII, No Unicode characters. 
Do NOT include explanations or extra text. 
If you cannot comply, return an empty JSON object {}. 
You a free to add list element in the json list as many as needed. 
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
        text = text or ""
        text = text.replace("```json","").replace("```","")
        # Convert escaped unicode sequences like "\\u2013" into real characters
        text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
        # Normalize to ASCII by decomposing unicode characters and mapping common symbols
        normalized = unicodedata.normalize("NFKD", text)
        translated = []
        for ch in normalized:
            if ord(ch) < 128:
                translated.append(ch)
                continue
            replacement = UNICODE_ASCII_MAP.get(ch, "")
            translated.append(replacement)
        return "".join(translated)
    
    def wrap_md(self, text):
        return json.dumps(text, indent=3) 
    
    def reformat_output(self, ):
        outputs = []
        for rec in self:
            if not rec.output:
                outputs.append("")
                continue
            cleaned = rec.clean_md(rec.output)
            try:
                parsed = json.loads(cleaned)
                formatted = json.dumps(parsed, indent=3)
            except json.JSONDecodeError:
                formatted = cleaned
            rec.output = formatted
            outputs.append(formatted)
        return outputs[0] if len(outputs) == 1 else outputs
