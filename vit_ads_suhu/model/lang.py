#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class lang(models.Model):

    _name = "res.lang"
    _description = "res.lang"


    def action_reload_view(self):
        pass


    _inherit = "res.lang"


