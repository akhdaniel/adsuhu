#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class product(models.Model):

    _name = "product.template"
    _description = "product.template"


    def action_reload_view(self):
        pass


    _inherit = "product.template"
    credit_amount = fields.Integer( string=_("Credit Amount"))


