#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import json

class landing_page_builder(models.Model):
    _name = "vit.landing_page_builder"
    _inherit = "vit.landing_page_builder"
    lang_id = fields.Many2one(comodel_name="res.lang", related="ads_copy_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="ads_copy_id.product_value_analysis_id.partner_id")    


    def action_generate(self, ):
        pass

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_landing_page_builder", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "landing_page_builder")], limit=1
        ).id
    
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)

    @api.onchange("ads_copy_id","compliance_checker_id","product_value_analysis_id","audience_profiler_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["ads_copy_id.output","visual_concept_id.output","compliance_checker_id.output","product_value_analysis_id.output","audience_profiler_id.output"]
        }
        """
        for rec in self:
            rec.name = f"LP - ANGLE {rec.ads_copy_id.angle_hook_id.angle_no} - HOOK {rec.ads_copy_id.hook_no}"
            rec.input = f"""
# ✅ ADS COPY:
---
{rec.ads_copy_id.output}

# ✅ AUDIENCE PROFILE:
---
{rec.audience_profiler_id.output}


# ✅ COMPLIANCE CHECK:
---
{rec.compliance_checker_id.output}

# ✅ PRODUCT VALUE:
---
{rec.product_value_analysis_id.output}

"""


    def generate_output_html(self):
        self.output_html = self.json_to_markdown(json.loads(self.clean_md(self.output)), level=2, max_level=3)
