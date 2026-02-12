#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class customer_credit(models.Model):

    _name = "vit.customer_credit"
    _description = "vit.customer_credit"


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    date_time = fields.Datetime( string=_("Date Time"))
    credit = fields.Float( string=_("Credit"))
    is_usage = fields.Boolean( string=_("Is Usage"), default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        string=_("Status"),
        default="draft",
        copy=False,
    )


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(customer_credit, self).copy(default)

    customer_id = fields.Many2one(comodel_name="res.partner",  string=_("Customer"))
