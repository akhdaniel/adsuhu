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
        self.output_html = self.md_to_html(
            self.json_to_markdown(
                json.loads(self.clean_md(self.output)),
                level=3,
                max_level=4
            )
        )

    # =====================================================
    # VIDEO PROMPT BUILDER (FROM output_html)
    # =====================================================

    def _build_video_prompt_from_output_html(self):
        """
        Convert output_html (scene table) → structured video prompt
        """
        self.ensure_one()

        if not self.output_html:
            raise UserError("Output HTML kosong. Generate dulu.")

        soup = BeautifulSoup(self.output_html, "html.parser")
        rows = soup.find_all("tr")

        scenes = []

        for row in rows[1:]:  # skip header
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            name = cols[0].get_text(strip=True)
            duration = cols[1].get_text(strip=True)
            visuals = cols[2].get_text(strip=True)
            text_overlay = cols[3].get_text(strip=True)
            voice_over = cols[4].get_text(strip=True)

            scenes.append(f"""
Scene: {name}
Duration: {duration}
Visuals: {visuals}
On-screen text: {text_overlay}
Voice over: {voice_over}
""")

        final_prompt = f"""
Create a vertical cinematic advertisement video (9:16).

Style:
- realistic
- cinematic lighting
- smooth camera motion
- professional commercial look
- emotional storytelling

Total Duration: 30–45 seconds

Scenes:
{chr(10).join(scenes)}

Rules:
- follow scene order strictly
- match visuals with narration
- smooth transitions
- readable text overlays
"""

        return final_prompt.strip()

    # =====================================================
    # VIDEO GENERATION
    # =====================================================

    def action_generate_video(self):
        for rec in self:
            api_key = self.env["ir.config_parameter"].sudo().get_param("fal_api_key")
            model_video_name = self.env["ir.config_parameter"].sudo().get_param("fal_video_model")
            if not api_key:
                raise UserError("FAL API Key belum diset di System Parameters")

            video_prompt = rec._build_video_prompt_from_output_html()

            _logger.info("VIDEO PROMPT:\n%s", video_prompt)

            fal = Fal(api_key=api_key)

            video_url = fal.generate_video(
                video_prompt=video_prompt,
                # model_name='bytedance/seedance-v1-pro-fast/text-to-video',
                model_name= model_video_name,
                additional_payload={
                    "duration": 45,
                    "fps": 24,
                    "aspect_ratio": "9:16",
                    "motion_strength": 0.8,
                }
            )
            _logger.info("Video URL:\n%s", video_url)

            if not video_url:
                raise UserError("Gagal generate video")

            rec.video_url = video_url
            rec._download_video_from_url()

        return True

    # =====================================================
    # DOWNLOAD VIDEO
    # =====================================================

    def _download_video_from_url(self):
        for rec in self:
            if not rec.video_url:
                continue

            try:
                response = requests.get(rec.video_url, timeout=60)
                if response.status_code == 200:
                    rec.video_file = base64.b64encode(response.content)
                    rec.video_filename = "generated_video.mp4"
                else:
                    raise UserError(
                        f"Gagal download video ({response.status_code})"
                    )
            except Exception as e:
                raise UserError(f"Error download video: {e}")
