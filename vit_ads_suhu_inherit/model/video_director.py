#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class video_director(models.Model):

    _name = "vit.video_director"
    _inherit = "vit.video_director"

    lang_id = fields.Many2one(comodel_name="res.lang", related="ads_copy_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="ads_copy_id.product_value_analysis_id.partner_id")



    def action_generate(self, ):
        pass


    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.write_description_prompt", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "Write Description Prompt")], limit=1
        ).id
    

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)

    @api.onchange("visual_concept_id","ads_copy_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["visual_concept_id.output"]
        }
        """
        for rec in self:
            rec.name = f"VIDEO DIRECTOR - ANGLE {rec.ads_copy_id.angle_hook_id.angle_no} - HOOK {rec.ads_copy_id.hook_no}"
            rec.input = f"""
# ✅ ADS COPY:
================
{rec.ads_copy_id.output}


# ✅ VISUAL CONCEPT:
================
{rec.visual_concept_id.output or ''}

"""
