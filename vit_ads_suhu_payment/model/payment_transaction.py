# -*- coding: utf-8 -*-

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _set_done(self, **kwargs):
        res = super()._set_done(**kwargs)
        for tx in self:
            invoices = getattr(tx, "invoice_ids", None)
            if invoices:
                invoices._grant_ai_tokens_if_needed()
        return res
