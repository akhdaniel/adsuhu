#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class auto_post_period(models.Model):

    _name = "vit.auto_post_period"
    _description = "vit.auto_post_period"


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    period_days = fields.Integer( string=_("Period Days"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(auto_post_period, self).copy(default)

