#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class gpt_prompt(models.Model):

    _name = "vit.gpt_prompt"
    _description = "vit.gpt_prompt"


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    gpt_url = fields.Char( string=_("Gpt Url"))
    system_prompt = fields.Text( string=_("System Prompt"))
    user_prompt = fields.Text( string=_("User Prompt"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(gpt_prompt, self).copy(default)

