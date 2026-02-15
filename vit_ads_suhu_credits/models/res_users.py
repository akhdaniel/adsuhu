from odoo import api, fields, models


INITIAL_SIGNUP_CREDIT = 10_000.0
SIGNUP_BONUS_REF = "Signup Bonus"


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        credit_model = self.env["vit.customer_credit"].sudo()

        for user in users:
            partner = user.partner_id
            if not partner:
                continue

            existing_bonus = credit_model.search_count(
                [
                    ("customer_id", "=", partner.id),
                    ("ref", "=", SIGNUP_BONUS_REF),
                ]
            )
            if existing_bonus:
                continue

            credit_model.create(
                {
                    "customer_id": partner.id,
                    "ref": SIGNUP_BONUS_REF,
                    "credit": INITIAL_SIGNUP_CREDIT,
                    "is_usage": False,
                    "date_time": fields.Datetime.now(),
                    "state": "done",
                }
            )
        return users
