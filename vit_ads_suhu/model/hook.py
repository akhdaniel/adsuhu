#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class hook(models.Model):

    _name = "vit.hook"
    _description = "vit.hook"


    def action_reload_view(self):
        pass


    _inherit = "vit.general_object"
    hook_no = fields.Integer( string=_("Hook No"))


    angle_hook_id = fields.Many2one(comodel_name="vit.angle_hook", string="Angle")
    ads_copy_ids = fields.One2many(comodel_name="vit.ads_copy",  inverse_name="hook_id",  string=_("Ads Copy"))
