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
        self.name = f"AP{ap}-ANGLE{angle}-HOOK{hook}-ADS{ads}-COPY{ad_copy}"

        body = json.loads(self.image_generator_id.output)
        self.headline = body["headline"]
        self.primary_text = body["primary_text"]
        self.cta = body["cta"]
    

    def _get_image_url(self, ):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self:
            rec.image_url = f'{base_url}/web/image/vit.image_variant/{rec.id}/image?unique={int(time.time())}'

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
                    media_url=rec.image_url,
                )
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
                    image_url=rec.image_url,
                )
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
                    image_url=rec.image_url,
                    caption=rec._social_caption(),
                )
                return rec._notify_post_success("Instagram", response)
            except SocialPostError as e:
                raise UserError(_("Instagram post failed: %s") % e)

    def _social_caption(self):
        if self.image_generator_id.ads_copy_id.landing_page_builder_ids:
            lp = self.image_generator_id.ads_copy_id.landing_page_builder_ids[0].lp_url 
        else:
            lp = self.image_generator_id.ads_copy_id.product_value_analysis_id.product_url or ""
        if self.tags:
            hashtags = ", ".join(f"#{w.strip()}" for w in self.tags.split(","))
        else:
            hashtags =""

        link_text = lp or ""
        res = f"""{self.headline}

{self.primary_text}

{self.cta}: {link_text}

{hashtags}
"""
        return res 

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
