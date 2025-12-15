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


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    output = fields.Text( string=_("Output"))
    input = fields.Text( string=_("Input"))
    gpt_url = fields.Char(related="gpt_prompt_id.gpt_url",  string=_("Gpt Url"))
    description = fields.Text( string=_("Description"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(general_object, self).copy(default)

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("Gpt Prompt"))
