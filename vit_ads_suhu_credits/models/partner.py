#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class partner(models.Model):
    """
    {
    "odoo_attributes":[{"_sql_constraints":"UNIQUE(chat_number)"}]
    }
    """

    _name = "res.partner"
    _inherit = "res.partner"

    @api.depends("customer_credit_ids")
    def _get_customer_limit(self, ):
        """
        {
        "@api.depends":["customer_credit_ids"]
        }
        """
        for rec in self:
            rec.customer_limit = rec._get_monthly_usage()
    
    # _sql_constraints = [("chat_number_unique", "UNIQUE(chat_number)", _("Chat number must be unique."))]
    # street = fields.Char(required=False, default="Jalan PHH. MUSTAFA Blok C No.16")
    # zip = fields.Char(required=False, default="40192")
    # city = fields.Char(required=False, default="Kabupaten Bandung")
    # country_id = fields.Many2one(comodel_name="res.country", required=False, default=lambda self: self.env.ref("base.id").id)
    # customer_limit = fields.Integer( string=_("Customer Limit"))

    def init(self):
        # update website_form_blacklisted on ir.fields for this object chat_number field to false
        # self.env.cr.execute("""
        #     UPDATE ir_model_fields SET website_form_blacklisted = false
        #     WHERE model = 'res.partner' AND name in ('chat_number', 'initial_business_type_id')
        # """)
        pass 
    
    def calculate_monthly_usage(self):
        """
        Calculate the monthly usage of the partner.
        This method should be called periodically to update the monthly usage.
        """
        for partner in self.search([]):
            # Assuming you have a method to calculate the usage
            monthly_usage = self._get_monthly_usage(partner)
            partner.monthly_usage = monthly_usage

    def _get_monthly_usage(self):
        # Count vit.messages for all vit.ai_agent that belong to the given partner
        # ai_agents = self.env['vit.ai_agent'].search([('partner_id', '=', partner.id)])
        credits = self.env['vit.customer_credit'].search([('customer_id', '=', self.id),('state','=','done')])
        return sum(credits.mapped('credit'))
    
    def reset_monthly_usage(self):
        """
        Reset the monthly usage of the partner.
        This method should be called at the beginning of each month.
        """
        for partner in self.search([]):
            partner.monthly_usage = 0
            # Optionally, you can log this reset action
            _logger.info(f"Monthly usage for {partner.name} has been reset to 0.")