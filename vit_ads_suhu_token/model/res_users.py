# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    ai_token_balance = fields.Integer(string="AI Token Balance", default=0)

    @api.model
    def get_my_token_balance(self):
        user = self.sudo().browse(self.env.uid)
        return user.ai_token_balance or 0

    def _get_ai_token_cost(self, category_code):
        category = self.env["vit.ai_token_category"].search(
            [("code", "=", category_code)], limit=1
        )
        return category.token_cost if category else 0

    def consume_ai_tokens(self, category_code, multiplier=1, ref_model=None, ref_id=None):
        self.ensure_one()
        category = self.env["vit.ai_token_category"].search(
            [("code", "=", category_code)], limit=1
        )
        if not category:
            raise UserError(
                _("Kategori token %s belum diset.") % (category_code,)
            )
        cost = (category.token_cost or 0) * multiplier
        if cost <= 0:
            raise UserError(
                _("Biaya token untuk kategori %s belum diset.") % (category_code,)
            )
        if self.ai_token_balance < cost:
            raise UserError(
                _(
                    "Token tidak cukup untuk kategori %s. Dibutuhkan %s, sisa %s."
                )
                % (category_code, cost, self.ai_token_balance)
            )
        self.ai_token_balance -= cost
        self.env["vit.ai_token_log"].create(
            {
                "user_id": self.id,
                "category_id": category.id if category else False,
                "token_delta": -cost,
                "ref_model": ref_model,
                "ref_id": ref_id,
                "note": "Usage",
            }
        )
        return cost
