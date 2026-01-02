#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
import json
from .libs.social_poster import SocialPoster, SocialPostError

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
                rec._notify_post_success("LinkedIn", response)
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
                rec._notify_post_success("Facebook", response)
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
                rec._notify_post_success("Instagram", response)
            except SocialPostError as e:
                raise UserError(_("Instagram post failed: %s") % e)

    def _social_caption(self):
        return self.primary_text or self.headline or self.name

    def _build_social_poster(self):
        """Create SocialPoster using tokens from system parameters."""
        params = self.env["ir.config_parameter"].sudo()
        config = {
            "linkedin_token": params.get_param("linkedin_access_token"),
            "facebook_token": params.get_param("facebook_access_token"),
            "instagram_token": params.get_param("instagram_access_token"),
            "linkedin_author_urn": params.get_param("linkedin_author_urn"),
            "facebook_page_id": params.get_param("facebook_page_id"),
            "instagram_business_account_id": params.get_param("instagram_business_account_id"),
        }
        poster = SocialPoster(
            linkedin_token=config["linkedin_token"],
            facebook_token=config["facebook_token"],
            instagram_token=config["instagram_token"],
        )
        return poster, config

    def _notify_post_success(self, platform, response):
        # Minimal feedback hook; could be extended to chatter notifications.
        _unused = response
        message = _("%s post submitted successfully.") % platform
        return self.env.user.notify_success(message)
