from odoo import fields, models, _


class CustomerCredit(models.Model):
    _inherit = "vit.customer_credit"

    transfer_proof = fields.Binary(string=_("Transfer Proof"), attachment=True)
    transfer_proof_filename = fields.Char(string=_("Transfer Proof Filename"))
