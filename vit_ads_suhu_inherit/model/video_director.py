#!/usr/bin/python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .libs.fal import Fal

import requests
import base64
import json
import logging
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


import logging
_logger = logging.getLogger(__name__)


class video_director(models.Model):

    _name = "vit.video_director"
    _inherit = "vit.video_director"

    # =====================================================
    # FIELDS
    # =====================================================

    lang_id = fields.Many2one(
        comodel_name="res.lang",
        related="ads_copy_id.product_value_analysis_id.lang_id"
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="ads_copy_id.product_value_analysis_id.partner_id"
    )

    video_url = fields.Char(string="Generated Video URL")
    video_file = fields.Binary(string="Video File", attachment=True)
    video_filename = fields.Char(string="Video Filename")

    gpt_prompt_id = fields.Many2one(
        comodel_name="vit.gpt_prompt",
        string=_("GPT Prompt"),
        default=lambda self: self._get_default_prompt()
    )

    # =====================================================
    # BASIC ACTIONS
    # =====================================================

    def action_generate(self):
        """Generate GPT output → output_html"""
        self.generate_output_html()

    def _get_default_prompt(self):
        prompt = self.env.ref(
            "vit_ads_suhu_inherit.write_description_prompt",
            raise_if_not_found=False
        )
        if prompt:
            return prompt.id

        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "Write Description Prompt")],
            limit=1
        ).id

    # =====================================================
    # INPUT BUILDER
    # =====================================================

    @api.onchange("visual_concept_id", "ads_copy_id")
    def _get_input(self):
        for rec in self:
            rec.name = (
                f"VIDEO DIRECTOR - "
                f"ANGLE {rec.ads_copy_id.angle_hook_id.angle_no} - "
                f"HOOK {rec.ads_copy_id.hook_no}"
            )

            rec.input = f"""
# ✅ ADS COPY:
================
{rec.ads_copy_id.output}


# ✅ VISUAL CONCEPT:
================
{rec.visual_concept_id.output or ''}
"""

    # =====================================================
    # ACTOR IMAGE
    # =====================================================

    def action_generate_actor(self):
        if not self.main_character:
            raise UserError("Main character empty!")

        api_key = self.env["ir.config_parameter"].sudo().get_param("fal_api_key")
        if not api_key:
            raise UserError("FAL API Key belum diset")

        fal = Fal(api_key=api_key)

        image_url = fal.generate_image(
            image_prompt=self.main_character,
            model_name='fal-ai/flux-pro/v1.1-ultra',
        )

        self.main_actor_url = image_url
        if image_url:
            self.download_actor_image()

    def download_actor_image(self):
        for rec in self:
            if not rec.main_actor_url:
                continue

            try:
                response = requests.get(rec.main_actor_url, timeout=15)
                if response.status_code == 200:
                    rec.main_actor = base64.b64encode(response.content)
                else:
                    raise UserError(
                        f"Failed to download image ({response.status_code})"
                    )
            except Exception as e:
                raise UserError(f"Error downloading actor image: {e}")

    # =====================================================
    # OUTPUT HTML
    # =====================================================

    def generate_output_html(self):
        try:
            self.output_html = self.md_to_html(
                self.json_to_markdown(
                    json.loads(self.clean_md(self.output)), level=3, max_level=4
                )
            )
        except Exception as e:
            _logger.error(self.output)
            raise UserError('Failed to generate Output HTML')
