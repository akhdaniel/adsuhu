#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class video_variant(models.Model):

    _name = "vit.video_variant"
    _description = "vit.video_variant"


    def _get_video_url(self, ):
        pass


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    video = fields.Binary( string=_("Video"))
    video_filename = fields.Char( string=_("Video Filename"))
    video_url = fields.Char(compute="_get_video_url",  string=_("Video Url"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(video_variant, self).copy(default)

    video_director_id = fields.Many2one(comodel_name="vit.video_director",  string=_("Video Director"))
