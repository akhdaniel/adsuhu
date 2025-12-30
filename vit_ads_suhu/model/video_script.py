#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class video_script(models.Model):

    _name = "vit.video_script"
    _description = "vit.video_script"


    def action_generate_prompt(self, ):
        pass


    def action_generate_video(self, ):
        pass


    def action_reload_view(self):
        pass

    name = fields.Char( required=True, copy=False, string=_("Name"))
    duration = fields.Char( string=_("Duration"))
    script = fields.Text( string=_("Script"))
    prompt = fields.Text( string=_("Prompt"))
    video_filename = fields.Char( string=_("Video Filename"))
    video_url = fields.Char( string=_("Video Url"))
    fal_ai_url = fields.Char( string=_("Fal Ai Url"))


    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': self.name + ' (Copy)'
        })
        return super(video_script, self).copy(default)

    video_director_id = fields.Many2one(comodel_name="vit.video_director",  string=_("Video Director"))
