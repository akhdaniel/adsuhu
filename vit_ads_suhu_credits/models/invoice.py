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
                # Execute your custom logic here
                # Example: self.env['mail.message'].create({...})
                _logger.info(f"Invoice {invoice.name} is paid, executing custom logic.")