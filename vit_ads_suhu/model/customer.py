#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class customer(models.Model):

    _name = "res.partner"
    _description = "res.partner"


    def action_reload_view(self):
        pass


    _inherit = "res.partner"
    customer_limit = fields.Integer( string=_("Customer Limit"))


    customer_credit_ids = fields.One2many(comodel_name="vit.customer_credit",  inverse_name="customer_id",  string=_("Customer Credit"))
