# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    ai_token_granted = fields.Boolean(string="AI Token Granted", default=False, copy=False)
    ai_token_user_id = fields.Many2one(
        "res.users",
        string="Token User",
        default=lambda self: self.env.user,
        help="User who will receive the AI tokens from this invoice.",
    )

    def _get_ai_token_qty_from_lines(self):
        self.ensure_one()
        sign = 1
        if self.move_type == "out_refund":
            sign = -1
        total = 0
        for line in self.invoice_line_ids:
            product = line.product_id
            if not product:
                continue
            qty = product.product_tmpl_id.ai_token_qty or 0
            if qty <= 0:
                continue
            total += int(qty * line.quantity)
        return total * sign

    def _get_ai_token_target_user(self):
        self.ensure_one()
        if self.ai_token_user_id:
            return self.ai_token_user_id
        if self.invoice_user_id:
            return self.invoice_user_id
        users = self.env["res.users"].search(
            [("partner_id", "=", self.partner_id.id)], limit=1
        )
        return users if users else self.env.user

    def _grant_ai_tokens_if_needed(self):
        for move in self:
            if move.ai_token_granted:
                continue
            if move.move_type not in ("out_invoice", "out_refund"):
                continue
            if move.payment_state != "paid":
                continue
            token_qty = move._get_ai_token_qty_from_lines()
            if token_qty <= 0:
                continue
            user = move._get_ai_token_target_user()
            user.ai_token_balance += token_qty
            self.env["vit.ai_token_log"].create(
                {
                    "user_id": user.id,
                    "category_id": False,
                    "token_delta": token_qty,
                    "ref_model": move._name,
                    "ref_id": move.id,
                    "note": "Invoice Paid",
                }
            )
            move.ai_token_granted = True

    @api.model
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._grant_ai_tokens_if_needed()
        return moves

    def write(self, vals):
        res = super().write(vals)
        if "payment_state" in vals:
            self._grant_ai_tokens_if_needed()
        return res
