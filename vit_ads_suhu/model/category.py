#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class category(models.Model):

    _name = "product.category"
    _description = "product.category"


    def action_reload_view(self):
        pass


    _inherit = "product.category"
    category_type = fields.Selection(selection=[('normal','Normal'),('topup','Top Up')],  string=_("Category Type"))


