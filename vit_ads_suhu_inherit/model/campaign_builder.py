#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class campaign_builder(models.Model):
    _name = "vit.campaign_builder"
    _inherit = "vit.campaign_builder"

    def action_generate(self, ):
        pass



    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_campaign_builder", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "campaign_builder")], limit=1
        ).id
    
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)

    @api.onchange("ads_copy_id","script_writer_id","visual_concept_id","compliance_checker_id","landing_page_builder_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["ads_copy_id.output","script_writer_id.output","visual_concept_id.output","compliance_checker_id.output","landing_page_builder_id.output"]
        }
        """
        for rec in self:
            rec.name = f"CAMPAIGN - ANGLE {rec.ads_copy_id.angle_hook_id.angle_no} - HOOK {rec.ads_copy_id.hook_no}"
            rec.input = f"""
# ✅ SCRIPT:
---
{rec.script_writer_id.output}

# ✅ VISUAL CONCEPT:
---
{rec.visual_concept_id.output}

# ✅ COMPLICANCE CHECK:
---
{rec.compliance_checker_id.output}

# ✅ LANDING PAGE:
---
{rec.landing_page_builder_id.output}

# ✅ ADS COPY:
---
{rec.ads_copy_id.output}

"""
