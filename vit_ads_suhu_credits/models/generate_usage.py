from odoo import fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.vit_ads_suhu_inherit.model.constants import NOT_ENOUGH_CREDIT

MIN_CREDIT = 1000 # Rp

import logging
_logger = logging.getLogger(__name__)


# Ponytail: DeepSeek repriced its models in 2026 (deepseek-flash / v4-pro,
# peak/off-peak, per 1M). Everything below is read from ir.config_parameter
# so the resale prices can track the vendor without a code release. Defaults
# are the most expensive published tier (v4-pro at peak) so resale cost never
# drops below the vendor bill. Lower them per-parameter if your account uses
# flash / off-peak only.

_DEFAULT_INPUT_MISS_USD = 1.32    # v4-pro, cache miss, peak
_DEFAULT_INPUT_HIT_USD = 0.044    # v4-pro, cache hit, peak
_DEFAULT_OUTPUT_USD = 3.96        # v4-pro, output, peak
_DEFAULT_USD_TO_IDR = 17000
_DEFAULT_TEXT_MARGIN = 10
_DEFAULT_IMAGE_MARGIN = 4
_DEFAULT_IMAGE_REF_INPUT_USD = 0.10   # per reference image on the /edit endpoint


def _get_param(params, key, default):
    value = params.get_param(key)
    if not value:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        _logger.warning("Invalid numeric ir.config_parameter %s=%r, using %r", key, value, default)
        return default


def _pricing(env):
    """DeepSeek + FX + margin, all overridable via ir.config_parameter."""
    params = env["ir.config_parameter"].sudo()
    return {
        "input_miss_usd": _get_param(params, "deepseek_input_usd_per_1m", _DEFAULT_INPUT_MISS_USD),
        "input_hit_usd": _get_param(params, "deepseek_cache_hit_usd_per_1m", _DEFAULT_INPUT_HIT_USD),
        "output_usd": _get_param(params, "deepseek_output_usd_per_1m", _DEFAULT_OUTPUT_USD),
        "usd_to_idr": _get_param(params, "usd_to_idr", _DEFAULT_USD_TO_IDR),
        "text_margin": _get_param(params, "text_margin", _DEFAULT_TEXT_MARGIN),
        "image_margin": _get_param(params, "image_margin", _DEFAULT_IMAGE_MARGIN),
        "image_ref_input_usd": _get_param(params, "image_ref_input_usd", _DEFAULT_IMAGE_REF_INPUT_USD),
    }


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
    cache_hit: bool = False,
    env=None,
) -> dict:
    """
    Estimate DeepSeek API cost.

    Pricing follows the current deepseek-flash / v4-pro tiers (USD per 1M
    tokens). All numbers are overridable via ir.config_parameter and default
    to the most expensive tier so the resale price never undercuts the vendor.
    """
    p = _pricing(env)

    input_price = p["input_hit_usd"] if cache_hit else p["input_miss_usd"]
    output_price = p["output_usd"]

    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)

    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    total_cost = input_cost + output_cost
    total_tokens = input_tokens + output_tokens

    total_cost_idr = total_cost * p["usd_to_idr"]
    total_sale_idr = total_cost_idr * p["text_margin"]

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "total_cost_idr": round(total_cost_idr, 2),
        "total_sale_idr": round(total_sale_idr, 2),
    }


def charge_usage(records, env, name, input_text, output_text, cache_hit=False):
    """Compute the DeepSeek cost for a call and book the usage credit.

    Shared by every stage so the billing logic lives in one place. The name
    argument may be a static string or a callable taking the record.
    """
    result = calculate_deepseek_cost(
        input_text,
        output_text,
        cache_hit=cache_hit,
        env=env,
    )
    credit = - result.get('total_sale_idr')
    cost = - result.get('total_cost_idr')
    topup = env['vit.topup.service']
    for rec in records:
        label = name(rec) if callable(name) else name
        partner = rec.partner_id
        if not partner:
            _logger.warning("Usage credit skipped for %s (%s): no partner.", rec._name, rec.id)
            continue
        topup.create_usage_credit(
            partner, name=label, credit=credit, cost=cost
        )


def require_balance(rec, minimum=MIN_CREDIT):
    """Fail closed before an unbilled call starts."""
    partner = rec.partner_id
    if partner and (partner.customer_limit or 0) <= minimum:
        raise UserError(NOT_ENOUGH_CREDIT)


class ProductValueAnalysis(models.Model):
    _inherit = "vit.product_value_analysis"

    def action_write_with_ai(self):
        if self.partner_id and self.partner_id.customer_limit <= MIN_CREDIT:
            raise UserError(NOT_ENOUGH_CREDIT)
        res = super().action_write_with_ai()

        charge_usage(
            self, self.env, lambda rec: f"{rec.display_name} - Write with Ai",
            input_text=self.initial_description,
            output_text=(self.description or "") + (self.features or ""),
        )
        return res

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <= MIN_CREDIT:
            raise UserError(NOT_ENOUGH_CREDIT)
        res = super().action_generate()

        charge_usage(
            self, self.env, lambda rec: f"{rec.display_name} - Product analysis",
            input_text=self.input,
            output_text=self.output or "",
        )
        return res


class StageUsageMixin(object):
    """Billing for the DeepSeek pipeline stages.

    Subclasses it with the recordset the stage lives on; super() resolves to
    the registered model's action_generate, so billing wraps the real API call.
    """

    def action_generate(self):
        if self.partner_id and self.partner_id.customer_limit <= MIN_CREDIT:
            raise UserError(NOT_ENOUGH_CREDIT)
        res = super().action_generate()

        charge_usage(
            self, self.env, lambda rec: f"{rec.display_name or rec._name}",
            input_text=self.input,
            output_text=self.output or "",
        )
        return res


class MarketMapper(StageUsageMixin, models.Model):
    _inherit = "vit.market_mapper"


class AudienceProfiler(StageUsageMixin, models.Model):
    _inherit = "vit.audience_profiler"


class AngleHook(StageUsageMixin, models.Model):
    _inherit = "vit.angle_hook"


class Hook(StageUsageMixin, models.Model):
    _inherit = "vit.hook"


class AdsCopy(StageUsageMixin, models.Model):
    _inherit = "vit.ads_copy"


class VideoDirector(StageUsageMixin, models.Model):
    _inherit = "vit.video_director"
