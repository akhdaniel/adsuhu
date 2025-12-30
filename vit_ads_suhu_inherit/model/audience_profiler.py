#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


DEFAULT_SPECIFIC_INSTRUCTION = """
REQUIRED JSON OUTPUT FORMAT:
```json
{
    "main_target_segment": "....",
    "customer_empathy_profile": {
        "think_and_feel": [
            "...",
            "...",
            "...",
            "..."
        ],
        "look": [
            "...",
            "...",
            "..."
        ],
        "listen": [
            "...",
            "...",
            "..."
        ],
        "say_and_do": [
            "...",
            "...",
            "..."
        ],
        "pain_points": [
            "...",
            "...",
            "...",
            "..."
        ],
        "aspitations_and_goals": [
            "...",
            "...",
            "...",
        ],
        "barriers_and_objections": [
            "...",
            "...",
            "...",
        ]
    },
    "communication_tone_and_language": {
        "key_phrases_and_expressions": [
            "..",
            "..."
        ],
        "speaking_style": "..."
    },
    "emotion_triggers": [
        {
            "emotion": "...",
            "situation_example": "..."
        },
        {
            "emotion": "...",
            "situation_example": "..."
        },
        {
            "emotion": "...",
            "situation_example": "..."
        }
    ]
}
```
"""
class audience_profiler(models.Model):
    _name = "vit.audience_profiler"
    _inherit = "vit.audience_profiler"

    def action_generate(self, ):
        pass
    specific_instruction = fields.Text( string=_("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)


    lang_id = fields.Many2one(comodel_name="res.lang", related="market_mapper_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="market_mapper_id.product_value_analysis_id.partner_id")

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_audience_profiler", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "audience_profiler")], limit=1
        ).id
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    

    @api.onchange("market_mapper_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["market_mapper_id.output"]
        }
        """
        for rec in self:
            # rec.name = f"AUDIENCE PROFILE {rec.audience_profile_no}"
            rec.input = f"""
# FOCUS:
---
Fokus ke profile ini dulu: {rec.description}.
Alasan: {rec.alasan}.

# OVERALL MARKET MAP:
---
{rec.market_mapper_id.output}

# INSTRUCTIONS:
---
{rec.general_instruction}

{rec.specific_instruction or ''}

Response in {self.lang_id.name} language.

"""
