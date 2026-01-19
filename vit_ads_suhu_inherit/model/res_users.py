from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    allowed_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Allowed Partners",
        help="Partners whose records the user can access via Ads Suhu rules.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        for user in users:
            if not user.allowed_partner_ids and user.partner_id:
                user.allowed_partner_ids = [(4, user.partner_id.id)]
        return users
