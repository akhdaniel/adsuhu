from odoo import models, api

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        res = super().write(vals)
        self._check_payment_state_and_execute()
        return res

    def _check_payment_state_and_execute(self):
        _logger.info(f"Checking payment state for invoices... {self.name} ")
        for invoice in self:
            if invoice.move_type == 'out_invoice' and invoice.payment_state == 'paid':
                _logger.info(f"Invoice {invoice.name} is paid, executing custom logic.")
                partner = invoice.partner_id
                expired_count_day = 30  # change this if you want to make dynamic
                for line in invoice.invoice_line_ids:
                    product = line.product_id
                    qty = line.quantity or 1
                    if not product:
                        continue
                    if product.categ_id.category_type == "topup":
                        self.env['vit.topup.service'].process_topup_product(self.name,
                            partner, product, expired_count_day, qty
                        )
