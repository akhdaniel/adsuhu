from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta


class TopupService(models.AbstractModel):
    _name = 'vit.topup.service'
    _description = 'Topup Service'

    def process_topup_product(self, partner, product, expired_date, qty=1):
        """
        Process Adsuhu Topup products by inserting customer_credit, is_usage = False
        
        Args:
            partner: res.partner record of the customer
            product: product.template record of the topup product
            qty: quantity purchased (default: 1)
        """
        if not product.credit_amount:
            _logger.warning(
                f"Topup product {product.name} has no credit_amount defined, skipping topup processing."
            )
            return
        
        # Calculate topup amount
        topup_amount = product.credit_amount * qty
        current_limit = partner.customer_limit or 0
        expired_date_updated = datetime.now() + timedelta(days=expired_date)

        _logger.info(
            f"\n\nTopup processing for partner {partner.name}: "
            f"current_limit={current_limit}, topup_amount={topup_amount}, "
            f"expired_date={expired_date_updated}\n\n"
        )
        
        try:
            self.env['vit.customer_credit'].sudo().create({
                    'name': 'topup',
                    'credit': topup_amount,
                    'is_usage': False,
                    'date_time': fields.Datetime.now(),
                })
            
            _logger.info(
                f"Successfully updated customer limit for partner {partner.name}: "
                f"added {topup_amount} tokens for {qty}x {product.name})"
            )
            
            # Optional: Create a log entry or notification for the topup
            self._create_topup_log(
                partner, product, qty, topup_amount, current_limit, expired_date
            )
            
        except Exception as e:
            _logger.error(
                f"Failed to update monthly limit for partner {partner.name}: {str(e)}"
            )
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
            message = (
                f"Token Topup: {partner.name} purchased {qty} x {product.name}, "
                f"added {topup_amount} tokens, current limit {old_limit} "
                f"expired date set to {expired_date}"
            )
            
            _logger.info(f"Topup Log: {message}")
            
            # Optional: Send notification email or create internal note
            # partner.message_post(body=message, subject="Token Topup Processed")
            
        except Exception as e:
            _logger.warning(
                f"Failed to create topup log for partner {partner.name}: {str(e)}"
            )
