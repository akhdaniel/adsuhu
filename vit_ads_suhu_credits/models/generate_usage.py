from odoo import models
from odoo.exceptions import UserError, ValidationError

TOKENS_PER_CREDIT=1000 # 1 credit = 1000 tokens
MIN_CREDIT=10

import logging
_logger = logging.getLogger(__name__)



def estimate_tokens(text: str) -> int:
    """
    Hybrid token estimation.
    Combines word-based and character-based heuristics.
    """
    if not text:
        return 0

    word_estimate = len(text.strip().split()) * 1.3
    char_estimate = len(text) / 4

    return int((word_estimate + char_estimate) / 2)


def calculate_deepseek_cost(
    input_text: str,
    output_text: str,
    cache_hit: bool = False
) -> dict:
    """
    Estimate DeepSeek-Chat API cost.

    Pricing (USD per 1M tokens):
    - Input (cache miss): $0.27
    - Input (cache hit):  $0.07
    - Output:             $1.10
    """

    # Pricing constants
    INPUT_PRICE = 0.07 if cache_hit else 0.27
    OUTPUT_PRICE = 1.10

    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)

    input_cost = (input_tokens / 1_000_000) * INPUT_PRICE
    output_cost = (output_tokens / 1_000_000) * OUTPUT_PRICE
    total_cost = input_cost + output_cost
    total_tokens = input_tokens + output_tokens

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "total_credit_used": total_tokens/TOKENS_PER_CREDIT
    }


class ProductValueAnalysis(models.Model):
    _inherit = "vit.product_value_analysis"

    def action_write_with_ai(self):
        if self.partner_id and self.partner_id.customer_limit <= MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_write_with_ai()

        result = calculate_deepseek_cost(self.initial_description, 
                                         self.description or "" + self.features or "" , 
                                         cache_hit=False)
        # _logger.info(result)
        credit = - result.get('total_credit_used')
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=f"{rec.display_name} - Write with Ai", credit=credit
            )
        return res
    
    
    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=f"{rec.display_name} - Product analysis", credit=credit
            )
        return res


class MarketMapper(models.Model):
    _inherit = "vit.market_mapper"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
        
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=f"{rec.display_name}", credit=credit
            )
        return res


class AudienceProfiler(models.Model):
    _inherit = "vit.audience_profiler"

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <=MIN_CREDIT:
            raise UserError('Not enough credit')
        res = super().action_generate()

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
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

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
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

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
        
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

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
        
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

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
        
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

        result = calculate_deepseek_cost(self.input, self.output, cache_hit=False)
        credit = - result.get('total_credit_used')
        
        for rec in self:
            partner = rec.partner_id
            self.env['vit.topup.service'].create_usage_credit(
                partner, name=rec.display_name, credit=credit
            )
        return res
