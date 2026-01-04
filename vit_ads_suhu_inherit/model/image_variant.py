#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
import json
import logging
from .libs.social_poster import SocialPoster, SocialPostError

_logger = logging.getLogger(__name__)

import logging
_logger = logging.getLogger(__name__)


class image_variant(models.Model):

    _name = "vit.image_variant"
    _inherit = "vit.image_variant"


    @api.onchange("image_generator_id")
    def _get_default_name(self):
        ap = self.image_generator_id.hook_id.angle_hook_id.audience_profiler_id.audience_profile_no
        angle = self.image_generator_id.hook_id.angle_hook_id.angle_no
        hook = self.image_generator_id.hook_id.hook_no
        ads = 1 #self.image_generator_id.ads_copy_id.hook_no
        ad_copy = self.image_generator_id.ads_copy_no
        self.tags = self.image_generator_id.ads_copy_id.product_value_analysis_id.tags or ""

        self.name = f"AP{ap}-ANGLE{angle}-HOOK{hook}-ADS{ads}-COPY{ad_copy}"

        body = json.loads(self.image_generator_id.output)
        self.headline = body["headline"]
        self.primary_text = body["primary_text"]
        self.cta = body["cta"]
    

    def _get_lp_url(self, ):
        for rec in self:
            rec.lp_url = self.image_generator_id.ads_copy_id.landing_page_builder_ids[0].lp_url \
                if self.image_generator_id.ads_copy_id.landing_page_builder_ids \
                    else lp = self.image_generator_id.ads_copy_id.product_value_analysis_id.product_url

    def _get_image_url(self, ):
        for rec in self:
            rec.image_url = rec._image_field_url("image_1024")

    def action_post_linkedin(self, ):
        _logger.info(f"----- {__name__}")
        for rec in self:
            poster, config = rec._build_social_poster()
            author_urn = config.get("linkedin_author_urn")
            if not author_urn:
                raise UserError(_("Please set linkedin_author_urn in system parameters."))
            try:
                response = poster.post_linkedin(
                    author_urn=author_urn,
                    message=rec._social_caption(),
                    media_url=rec._image_field_url("image_1024"),
                )
                rec.linkedin_url = rec._extract_linkedin_url(response)
                return rec._notify_post_success("LinkedIn", response)
            except SocialPostError as e:
                raise UserError(_("LinkedIn post failed: %s") % e)


    def action_post_facebook(self, ):
        for rec in self:
            poster, config = rec._build_social_poster()
            page_id = config.get("facebook_page_id")
            if not page_id:
                raise UserError(_("Please set facebook_page_id in system parameters."))
            try:
                response = poster.post_facebook(
                    page_id=page_id,
                    message=rec._social_caption(),
                    image_url=rec._image_field_url("image_1024"),
                )
                rec.facebook_url = rec._extract_facebook_url(response)
                return rec._notify_post_success("Facebook", response)
            except SocialPostError as e:
                raise UserError(_("Facebook post failed: %s") % e)


    def action_post_ig(self, ):
        """
        {
        "label":"Post IG"
        }
        """
        for rec in self:
            poster, config = rec._build_social_poster()
            business_account_id = config.get("instagram_business_account_id")
            if not business_account_id:
                raise UserError(_("Please set instagram_business_account_id in system parameters."))
            try:
                response = poster.post_instagram(
                    business_account_id=business_account_id,
                    image_url=rec._image_field_url("image_512"),
                    caption=rec._social_caption(),
                )
                rec.ig_url = rec._extract_instagram_url(response)
                return rec._notify_post_success("Instagram", response)
            except SocialPostError as e:
                raise UserError(_("Instagram post failed: %s") % e)

    def _social_caption(self):

        if self.tags:
            hashtags = ", ".join(f"#{w.strip()}" for w in self.tags.split(","))
        else:
            hashtags =""

        res = f"""{self.headline}

{self.primary_text}

{self.cta}: {self.lp_url}

{hashtags}
"""
        return res 

    def _image_field_url(self, field_name: str) -> str:
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        return f"{base_url}/web/image/vit.image_variant/{self.id}/{field_name}?unique={int(time.time())}"

    def _build_social_poster(self):
        """Create SocialPoster using tokens from system parameters."""
        params = self.env["ir.config_parameter"].sudo()
        config = {
            "linkedin_token": params.get_param("linkedin_access_token"),
            "linkedin_client_id": params.get_param("linkedin_client_id"),
            "linkedin_client_secret": params.get_param("linkedin_client_secret"),
            "linkedin_redirect_uri": params.get_param("linkedin_redirect_uri"),
            "linkedin_refresh_token": params.get_param("linkedin_refresh_token"),
            "linkedin_authorization_code": params.get_param("linkedin_authorization_code"),
            "facebook_token": params.get_param("facebook_access_token"),
            "instagram_token": params.get_param("instagram_access_token"),
            "telegram_bot_token": params.get_param("telegram_bot_token"),
            "telegram_chat_id": params.get_param("telegram_chat_id"),
            "linkedin_author_urn": params.get_param("linkedin_author_urn"),
            "facebook_page_id": params.get_param("facebook_page_id"),
            "instagram_business_account_id": params.get_param("instagram_business_account_id"),
        }

        def save_tokens(tokens):
            if tokens.get("access_token"):
                params.set_param("linkedin_access_token", tokens["access_token"])
            if tokens.get("refresh_token"):
                params.set_param("linkedin_refresh_token", tokens["refresh_token"])

        poster = SocialPoster(
            linkedin_token=config["linkedin_token"],
            linkedin_client_id=config["linkedin_client_id"],
            linkedin_client_secret=config["linkedin_client_secret"],
            linkedin_redirect_uri=config["linkedin_redirect_uri"],
            linkedin_refresh_token=config["linkedin_refresh_token"],
            linkedin_authorization_code=config["linkedin_authorization_code"],
            facebook_token=config["facebook_token"],
            instagram_token=config["instagram_token"],
            telegram_token=config["telegram_bot_token"],
            token_saver=save_tokens,
        )
        return poster, config

    def _notify_post_success(self, platform, response):
        # Minimal feedback hook; extend to chatter/notifications if desired.
        _logger.info("%s post submitted successfully: %s", platform, response)
        message = _("%s post submitted successfully.") % platform
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }

    def _extract_linkedin_url(self, response):
        # LinkedIn responses often include URN; URL can be constructed if absent.
        if isinstance(response, dict):
            if response.get("id"):
                return f"https://www.linkedin.com/feed/update/{response['id']}"
            if response.get("value", {}).get("id"):
                return f"https://www.linkedin.com/feed/update/{response['value']['id']}"
        return self.linkedin_url

    def _extract_facebook_url(self, response):
        if isinstance(response, dict):
            post_id = response.get("id")
            page_id = response.get("post_id", "").split("_")[0] if response.get("post_id") else None
            if post_id and page_id:
                return f"https://www.facebook.com/{page_id}/posts/{post_id.split('_')[-1]}"
            if post_id:
                return f"https://www.facebook.com/{post_id}"
        return self.facebook_url

    def _extract_instagram_url(self, response):
        if isinstance(response, dict):
            ig_id = response.get("id")
            if ig_id:
                return f"https://www.instagram.com/p/{ig_id}"
        return self.ig_url


    def action_post_telegram(self, ):
        for rec in self:
            poster, config = rec._build_social_poster()
            chat_id = config.get("telegram_chat_id")
            if not chat_id:
                raise UserError(_("Please set telegram_chat_id in system parameters."))
            try:
                response = poster.post_telegram(
                    chat_id=chat_id,
                    photo_url=rec._image_field_url("image_512"),
                    caption=rec._social_caption(),
                )
                result = response.get("result", {}) if isinstance(response, dict) else {}
                message_id = result.get("message_id")
                rec.telegram_url = f"chat:{chat_id} message:{message_id}" if message_id else rec.telegram_url
                return rec._notify_post_success("Telegram", response)
            except SocialPostError as e:
                raise UserError(_("Telegram post failed: %s") % e)


    def action_post_whatsapp(self, ):
        pass
