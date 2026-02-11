from odoo import models
from odoo.exceptions import UserError, ValidationError



CREDIT_PER_CHAR=1000
MIN_CREDIT=10

class ProductValueAnalysis(models.Model):
    _inherit = "vit.product_value_analysis"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res


class MarketMapper(models.Model):
    _inherit = "vit.market_mapper"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res


class AudienceProfiler(models.Model):
    _inherit = "vit.audience_profiler"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res


class AngleHook(models.Model):
    _inherit = "vit.angle_hook"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res


class Hook(models.Model):
    _inherit = "vit.hook"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res


class AdsCopy(models.Model):
    _inherit = "vit.ads_copy"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res


class ImageGenerator(models.Model):
    _inherit = "vit.image_generator"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res


class VideoDirector(models.Model):
    _inherit = "vit.video_director"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()
        total_chars = len(self.output)
        credit = -total_chars/CREDIT_PER_CHAR
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res
