#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class gpt_model(models.Model):

    _name = "vit.gpt_model"
    _description = "vit.gpt_model"


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(gpt_model, self).copy(default)

