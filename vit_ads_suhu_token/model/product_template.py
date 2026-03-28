# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ai_token_qty = fields.Integer(string="AI Token Qty", default=0)
