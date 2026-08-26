# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)

_STATUS_FIELDS = {"status", "error_message"}


class GeneralObject(models.Model):
    _inherit = "vit.general_object"

    def _analysis_id(self):
        """Resolve the owning vit.product_value_analysis id, if any."""
        self.ensure_one()
        if self._name == "vit.product_value_analysis":
            return self.id
        if "product_value_analysis_id" in self._fields:
            return self.product_value_analysis_id.id or False
        # Walk relations for models without a direct link.
        for path in (
            "image_generator_id.ads_copy_id.product_value_analysis_id",
            "landing_page_builder_id.ads_copy_id.product_value_analysis_id",
            "compliance_checker_id.ads_copy_id.product_value_analysis_id",
            "ads_copy_id.product_value_analysis_id",
            "hook_id.product_value_analysis_id",
            "angle_hook_id.product_value_analysis_id",
            "audience_profiler_id.product_value_analysis_id",
            "market_mapper_id.product_value_analysis_id",
        ):
            try:
                rec = self
                for hop in path.split("."):
                    if hop not in rec._fields:
                        rec = None
                        break
                    rec = rec[hop]
                if rec:
                    return rec.id
            except Exception:  # pragma: no cover - defensive
                continue
        return False

    def write(self, vals):
        res = super().write(vals)
        if _STATUS_FIELDS & set(vals):
            for rec in self:
                analysis_id = rec._analysis_id()
                if not analysis_id:
                    continue
                try:
                    self.env["bus.bus"].sudo()._sendone(
                        f"adsuhu.analysis.{analysis_id}",
                        "status",
                        {
                            "model": rec._name,
                            "id": rec.id,
                            "status": rec.status or "idle",
                            "error": rec.error_message or "",
                        },
                    )
                except Exception:
                    _logger.warning(
                        "Failed to emit bus status for %s(%s)", rec._name, rec.id
                    )
        return res
