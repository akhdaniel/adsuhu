# -*- coding: utf-8 -*-

import logging
import re

from markupsafe import Markup

import markdown

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _md(text):
    if not text:
        return ""
    return Markup(markdown.markdown(text, extensions=["tables"]))


def _record_status(rec):
    return rec.status or "idle"


class AdsuhuUi(http.Controller):
    @http.route(
        "/adsui/save",
        type="json",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def save(self, **kw):
        data = request.get_json_data()
        model_name = data.get("model")
        record_id = data.get("id")
        values = data.get("values", {})
        if not model_name or not record_id or not values:
            return {"error": "missing params"}
        Record = request.env[model_name].sudo().browse(record_id).exists()
        if not Record:
            return {"error": "not_found"}
        # output_html is rendered HTML - keep as-is.
        # description/features/initial_description expect markdown - strip HTML tags.
        for field, val in values.items():
            if (
                isinstance(val, str)
                and field in ("description", "features", "initial_description")
                and "<" in val
            ):
                values[field] = re.sub(r"<[^>]+>", "", val)
        Record.write(values)
        return {"status": "ok"}

    @http.route(
        "/adsui",
        type="http",
        auth="user",
        website=True,
    )
    def dashboard(self, page=1, **kw):
        Analysis = request.env["vit.product_value_analysis"].sudo()
        domain = []
        per_page = 12
        total = Analysis.search_count(domain)
        pager = request.website.pager(
            url="/adsui",
            total=total,
            page=page,
            step=per_page,
            scope=7,
        )
        analyses = Analysis.search(
            domain, offset=pager["offset"], limit=per_page, order="create_date desc"
        )
        return request.render(
            "vit_adsuhu_ui.dashboard_template",
            {"analyses": analyses, "pager": pager},
        )

    @http.route(
        "/adsui/create",
        type="http",
        auth="user",
        website=True,
    )
    def create(self, **kw):
        langs = request.env["res.lang"].search([("active", "=", True)])
        return request.render(
            "vit_adsuhu_ui.form_template",
            {
                "langs": langs,
                "analysis": False,
                "is_edit": False,
            },
        )

    @http.route(
        "/adsui/<int:analysis_id>/edit",
        type="http",
        auth="user",
        website=True,
    )
    def edit(self, analysis_id, **kw):
        analysis = (
            request.env["vit.product_value_analysis"].sudo().browse(analysis_id).exists()
        )
        if not analysis:
            return request.not_found()
        langs = request.env["res.lang"].search([("active", "=", True)])
        return request.render(
            "vit_adsuhu_ui.form_template",
            {
                "langs": langs,
                "analysis": analysis,
                "is_edit": True,
            },
        )

    @http.route(
        "/adsui/<int:analysis_id>",
        type="http",
        auth="user",
        website=True,
    )
    def page(self, analysis_id, **kw):
        analysis = (
            request.env["vit.product_value_analysis"].sudo().browse(analysis_id).exists()
        )
        if not analysis:
            return request.not_found()
        return request.render("vit_adsuhu_ui.app_page", {"analysis": analysis})

    @http.route(
        "/adsui/data/<int:analysis_id>",
        type="json",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def data(self, analysis_id, **kw):
        analysis = (
            request.env["vit.product_value_analysis"].sudo().browse(analysis_id).exists()
        )
        if not analysis:
            return {"error": "not_found"}
        stages = self._build_stages(analysis)
        return {
            "analysis": {
                "id": analysis.id,
                "name": analysis.name,
                "target_market": analysis.target_market or "",
                "product_url": analysis.product_url or "",
                "tags": analysis.tags or "",
            },
            "stages": stages,
        }

    # ------------------------------------------------------------------
    # Stage builders
    # ------------------------------------------------------------------
    def _action(self, gen_key, gen_route, status_route, record):
        return {
            "gen_key": gen_key,
            "gen_route": gen_route,
            "status_route": status_route,
            "status": _record_status(record),
            "error": record.error_message or "",
        }

    def _build_stages(self, analysis):
        stages = []

        # --- Product (description + features) ---
        desc_html = _md(analysis.description)
        feats_html = _md(analysis.features)
        initial_desc_html = _md(analysis.initial_description)
        stages.append(
            {
                "key": "product",
                "label": "Product",
                "icon": "fa-cube",
                "hint": "Product description and key features.",
                "cards": [
                    {
                        "id": analysis.id,
                        "title": analysis.name,
                        "subtitle": analysis.product_url or "",
                        "status": _record_status(analysis),
                        "action": self._action(
                            "write_with_ai",
                            f"/product_analysis/{analysis.id}/write_with_ai",
                            f"/regenerate_status/write_with_ai/{analysis.id}",
                            analysis,
                        ),
                        "content": {
                            "blocks": [
                                {
                                    "name": "Initial Description",
                                    "html": initial_desc_html,
                                    "edit_model": "vit.product_value_analysis",
                                    "edit_id": analysis.id,
                                    "edit_field": "initial_description",
                                    "edit_raw": analysis.initial_description or "",
                                },
                                {
                                    "name": "Description",
                                    "html": desc_html,
                                    "edit_model": "vit.product_value_analysis",
                                    "edit_id": analysis.id,
                                    "edit_field": "description",
                                    "edit_raw": analysis.description or "",
                                },
                                {
                                    "name": "Features",
                                    "html": feats_html,
                                    "edit_model": "vit.product_value_analysis",
                                    "edit_id": analysis.id,
                                    "edit_field": "features",
                                    "edit_raw": analysis.features or "",
                                },
                            ]
                        },
                    }
                ],
            }
        )

        # --- Product value analysis ---
        stages.append(
            {
                "key": "pva",
                "label": "Value",
                "icon": "fa-diamond",
                "hint": "Deep product value proposition analysis.",
                "cards": [
                    {
                        "id": analysis.id,
                        "title": "Product Value Analysis",
                        "subtitle": analysis.name,
                        "status": _record_status(analysis),
                        "action": self._action(
                            "product_value_analysis",
                            f"/product_analysis/{analysis.id}/regenerate",
                            f"/regenerate_status/product_value_analysis/{analysis.id}",
                            analysis,
                        ),
                        "content": {
                            "html": analysis.output_html or "",
                            "edit_model": "vit.product_value_analysis",
                            "edit_id": analysis.id,
                            "edit_field": "output_html",
                            "edit_raw": analysis.output_html or "",
                        },
                    }
                ],
            }
        )

        # --- Market map ---
        market_action = self._action(
            "market_map_analysis",
            f"/product_analysis/{analysis.id}/market_mapper/regenerate",
            f"/regenerate_status/market_map_analysis/{analysis.id}",
            analysis,
        )
        stages.append(
            {
                "key": "market",
                "label": "Market",
                "icon": "fa-globe",
                "hint": "Market analysis and segmentation.",
                "cards": [
                    {
                        "id": analysis.id,
                        "title": "Market Map",
                        "subtitle": analysis.target_market or "",
                        "status": market_action["status"],
                        "action": market_action,
                        "content": {
                            "blocks": [
                                {
                                    "name": mm.name,
                                    "html": mm.output_html or "",
                                    "edit_model": "vit.market_mapper",
                                    "edit_id": mm.id,
                                    "edit_field": "output_html",
                                    "edit_raw": mm.output_html or "",
                                }
                                for mm in analysis.market_mapper_ids
                            ]
                        },
                    }
                ],
            }
        )

        # --- Audience ---
        audience_cards = []
        for mm in analysis.market_mapper_ids:
            audience_cards.append(
                {
                    "id": mm.id,
                    "title": f"Audience — {mm.name}",
                    "subtitle": analysis.target_market or "",
                    "status": _record_status(mm),
                    "action": self._action(
                        "audience_profile_analysis",
                        f"/market_mapper/{mm.id}/audience_profiler/regenerate",
                        f"/regenerate_status/audience_profile_analysis/{mm.id}",
                        mm,
                    ),
                    "content": {
                        "blocks": [
                            {
                                "name": ap.name,
                                "html": ap.output_html or "",
                                "edit_model": "vit.audience_profiler",
                                "edit_id": ap.id,
                                "edit_field": "output_html",
                                "edit_raw": ap.output_html or "",
                            }
                            for ap in mm.audience_profiler_ids
                        ]
                    },
                }
            )
        stages.append(
            {
                "key": "audience",
                "label": "Audience",
                "icon": "fa-users",
                "hint": "Audience profiles per market segment.",
                "cards": audience_cards,
            }
        )

        # --- Angles & Hooks ---
        angle_cards = []
        for ap in analysis.market_mapper_ids.audience_profiler_ids:
            angle_cards.append(
                {
                    "id": ap.id,
                    "title": f"Angles & Hooks — {ap.name}",
                    "subtitle": ap.description or "",
                    "status": _record_status(ap),
                    "action": self._action(
                        "angle_hook",
                        f"/audience_profiler/{ap.id}/angle_hook/regenerate",
                        f"/regenerate_status/angle_hook/{ap.id}",
                        ap,
                    ),
                    "content": {
                        "blocks": [
                            {
                                "name": an.name or f"Angle {an.angle_no}",
                                "html": an.output_html or "",
                                "edit_model": "vit.angle_hook",
                                "edit_id": an.id,
                                "edit_field": "output_html",
                                "edit_raw": an.output_html or "",
                            }
                            for an in ap.angle_hook_ids
                        ]
                    },
                }
            )
        stages.append(
            {
                "key": "angle",
                "label": "Angles",
                "icon": "fa-lightbulb",
                "hint": "Copywriting angles and hooks per audience.",
                "cards": angle_cards,
            }
        )

        # --- Ads copy ---
        ads_cards = []
        for hook in analysis.market_mapper_ids.audience_profiler_ids.angle_hook_ids.hook_ids:
            ads_cards.append(
                {
                    "id": hook.id,
                    "title": f"Ads Copy — {hook.name or 'Hook'}",
                    "subtitle": hook.description or "",
                    "status": _record_status(hook),
                    "action": self._action(
                        "ads_copy",
                        f"/hook/{hook.id}/ads_copy/regenerate",
                        f"/regenerate_status/hook/{hook.id}",
                        hook,
                    ),
                    "content": {
                        "blocks": [
                            {
                                "name": ads.name,
                                "html": getattr(ads, "output_html_trimmed", None)
                                or ads.output_html
                                or "",
                                "edit_model": "vit.ads_copy",
                                "edit_id": ads.id,
                                "edit_field": "output_html",
                                "edit_raw": ads.output_html or "",
                            }
                            for ads in hook.ads_copy_ids
                        ]
                    },
                }
            )
        stages.append(
            {
                "key": "ads",
                "label": "Ads Copy",
                "icon": "fa-bullhorn",
                "hint": "Ad copy variants per hook.",
                "cards": ads_cards,
            }
        )

        # --- Creatives (images / landing pages / videos) ---
        creative_cards = []
        for ads in (
            analysis.market_mapper_ids.audience_profiler_ids.angle_hook_ids.hook_ids.ads_copy_ids
        ):
            images = [
                {
                    "id": iv.id,
                    "name": iv.name,
                    "image_url": iv.image_url or "",
                    "image_url_512": iv.image_url_512 or "",
                    "headline": iv.headline or "",
                    "primary_text": iv.primary_text or "",
                }
                for iv in ads.image_generator_ids.image_variant_ids
            ]
            creative_cards.append(
                {
                    "id": ads.id,
                    "title": f"Creatives — {ads.name}",
                    "subtitle": "",
                    "status": _record_status(ads.image_generator_ids[:1]),
                    "images": images,
                    "blocks": [
                        {"name": lp.name, "html": lp.output_html or ""}
                        for lp in ads.landing_page_builder_ids
                    ]
                    + [
                        {"name": vid.name, "html": vid.output_html or ""}
                        for vid in ads.video_director_ids
                    ],
                    "image_actions": [
                        self._action(
                            "image_variants",
                            f"/image_generator/{ig.id}/image_variant/regenerate",
                            f"/regenerate_status/image_variants/{ig.id}",
                            ig,
                        )
                        for ig in ads.image_generator_ids
                    ],
                }
            )
        stages.append(
            {
                "key": "creatives",
                "label": "Creatives",
                "icon": "fa-image",
                "hint": "Generated images, landing pages and video scripts.",
                "cards": creative_cards,
            }
        )

        return stages
