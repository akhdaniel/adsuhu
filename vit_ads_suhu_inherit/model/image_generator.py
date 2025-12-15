#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class image_generator(models.Model):
    _name = "vit.image_generator"
    _inherit = "vit.image_generator"

    def action_generate(self, ):
        pass

    # @api.depends("audience_profiler_id.output","angle_hook_id.output")
    def _get_input(self, ):
        for rec in self:
            rec.input = ""