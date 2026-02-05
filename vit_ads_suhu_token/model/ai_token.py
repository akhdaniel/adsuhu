# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AiTokenCategory(models.Model):
    _name = "vit.ai_token_category"
    _description = "AI Token Category"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Internal code, e.g. video, script, image")
    token_cost = fields.Integer(default=0)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Category code must be unique."),
    ]


class AiTokenLog(models.Model):
    _name = "vit.ai_token_log"
    _description = "AI Token Log"
    _order = "create_date desc"

    user_id = fields.Many2one("res.users", required=True)
    category_id = fields.Many2one("vit.ai_token_category")
    token_delta = fields.Integer(help="Positive for topup, negative for usage")
    ref_model = fields.Char()
    ref_id = fields.Integer()
    note = fields.Char()


class AiTokenTopup(models.Model):
    _name = "vit.ai_token_topup"
    _description = "AI Token Topup"
    _order = "create_date desc"

    name = fields.Char(default=lambda self: _("AI Token Topup"))
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    product_id = fields.Many2one("product.product")
    token_qty = fields.Integer(required=True, default=0)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id and hasattr(self.product_id, "ai_token_qty"):
            self.token_qty = self.product_id.ai_token_qty or 0

    def action_confirm(self):
        for rec in self:
            if rec.state == "done":
                continue
            if rec.token_qty <= 0:
                raise UserError("Token qty must be greater than 0.")
            rec.user_id.ai_token_balance += rec.token_qty
            self.env["vit.ai_token_log"].create({
                "user_id": rec.user_id.id,
                "category_id": False,
                "token_delta": rec.token_qty,
                "ref_model": rec._name,
                "ref_id": rec.id,
                "note": "Topup",
            })
            rec.state = "done"
