from odoo import models

import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    def action_post(self):
        super().action_post()
        # self._do_invoice_logic()

    def _do_invoice_logic(self):
        # Get related invoices
        if self.payment_transaction_id and '-' in self.payment_transaction_id.reference:
            # Assuming the reference is in the format "INV-12345-1" or "SO-12345-1"
            so_number, index = self.payment_transaction_id.reference.split('-')
        else:
            so_number = self.payment_transaction_id.reference
        so = self.env['sale.order'].search([('name','=',so_number)])
        if so:
            # Your custom logic here
            # Example: print(invoice.name)
            partner = so.partner_id
            _logger.info(f"Processing SO {so.name} for payment {self.name}")
            for line in so.order_line:
                product = line.product_id
                qty = line.product_uom_qty
                self.process_line(partner, product, qty)
        else:
            if self.payment_transaction_id and '-' in self.payment_transaction_id.reference:
                # Assuming the reference is in the format "INV-12345-1"
                inv_number, index = self.payment_transaction_id.reference.split('-')
            else:
                inv_number = self.payment_transaction_id.reference
            invoice = self.env['account.move'].search([('name','=',inv_number)])
            if invoice:
                partner = invoice.partner_id
                _logger.info(f"Processing invoice {invoice.name} for payment {self.name}")
                for line in invoice.order_line:
                    product = line.product_id
                    qty = line.product_uom_qty
                    self.process_line(partner, product, qty)
            else:
                _logger.warning(f"No sale order or invoice found for payment {self.name} with reference {self.payment_transaction_id.reference}")
    
    def process_line(self, partner, product, qty=1):
        
        if product:
            _logger.info(f"Processing product {product.name} for partner {partner.name}")
            # You can add more logic here related to the product
            _logger.info(f"\n\n product.categ_id.category_type={product.categ_id.category_type}\n\n")
            if product.categ_id.category_type == "agent":
                pass
                # new_credit = int(product.barcode) * qty
                # agent_limit = product.agent_limit
                # self.env['vit.ai_agent'].create_ai_agent(partner, product, self)    
            elif product.categ_id.category_type == "topup":
                # Handle topup products - update partner's monthly_limit
                expired_count_day = 30 #change if this if you want to make dynamic
                self.env['vit.topup.service'].process_topup_product(
                    partner, product, expired_count_day, qty
                )
            else:
                _logger.warning(f"Product {product.name} is not in 'Chat Master Agent' or 'Chat Master Topup' category, skipping processing.")
