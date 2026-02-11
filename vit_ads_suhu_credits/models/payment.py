from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta


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
                self._process_topup_product(partner, product, expired_count_day, qty)
            else:
                _logger.warning(f"Product {product.name} is not in 'Chat Master Agent' or 'Chat Master Topup' category, skipping processing.")

    def _process_topup_product(self, partner, product, expired_date, qty=1):
        """
        Process Adsuhu Topup products by inserting customer_credit, is_usage = False
        
        Args:
            partner: res.partner record of the customer
            product: product.template record of the topup product
            qty: quantity purchased (default: 1)
        """
        if not product.credit_amount:
            _logger.warning(f"Topup product {product.name} has no credit_amount defined, skipping topup processing.")
            return
        
        # Calculate topup amount
        topup_amount = product.credit_amount * qty
        current_limit = partner.customer_limit or 0
        expired_date_updated = datetime.now() + timedelta(days=expired_date)

        _logger.info(f"\n\nTopup processing for partner {partner.name}: current_limit={current_limit}, topup_amount={topup_amount},  expired_date={expired_date_updated}\n\n")
        
        try:
            self.env['vit.customer_limit'].create({
                    'name':'topup',
                    'credit': topup_amount,
                    'is_usage':False,
                    'date_time': fields.Datetime.now()
                })
            
            # # Update partner's monthly limit
            # partner.sudo().write({
            #     'monthly_limit': new_limit,
            #     'expired_date': expired_date_updated,
            # })
            
            _logger.info(f"Successfully updated customer limit for partner {partner.name}: added {topup_amount} tokens for {qty}x {product.name})")
            
            # Optional: Create a log entry or notification for the topup
            self._create_topup_log(partner, product, qty, topup_amount, current_limit, expired_date)
            
        except Exception as e:
            _logger.error(f"Failed to update monthly limit for partner {partner.name}: {str(e)}")
            raise
    
    def _create_topup_log(self, partner, product, qty, topup_amount, old_limit, expired_date):
        """
        Create a log entry for the topup transaction
        
        Args:
            partner: res.partner record
            product: product.template record
            qty: quantity purchased
            topup_amount: total tokens added
            old_limit: previous monthly limit
        """
        try:
            # You can extend this to create audit logs or notifications
            # For now, we'll just log to the system
            message = f"Token Topup: {partner.name} purchased {qty} x {product.name}, " \
                     f"added {topup_amount} tokens, current limit {old_limit} expired date set to {expired_date}"
            
            _logger.info(f"Topup Log: {message}")
            
            # Optional: Send notification email or create internal note
            # partner.message_post(body=message, subject="Token Topup Processed")
            
        except Exception as e:
            _logger.warning(f"Failed to create topup log for partner {partner.name}: {str(e)}")

