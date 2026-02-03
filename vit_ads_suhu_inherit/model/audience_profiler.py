#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import json

from .libs.openai_lib import generate_content

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
        "aspirations_and_goals": [
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

        if not self.gpt_prompt_id:
            raise UserError('Market Mapper GPT empty')
        if not self.gpt_model_id:
            raise UserError('GPT model empty')


        openai_api_key = self.env["ir.config_parameter"].sudo().get_param("deepseek_api_key")
        openai_base_url = self.env["ir.config_parameter"].sudo().get_param("deepseek_base_url", None)

        model = self.gpt_model_id.name

        user_prompt = self.gpt_prompt_id.user_prompt
        user_prompt += f"{self.input}\n"
        system_prompt = self.gpt_prompt_id.system_prompt 

        context = ""
        additional_command=""
        question = ""

        response = generate_content(openai_api_key=openai_api_key, 
                                openai_base_url=openai_base_url, 
                                model=model, 
                                system_prompt=system_prompt, 
                                user_prompt=user_prompt, 
                                context=context, 
                                question=question, 
                                additional_command=additional_command)    

        response = self.clean_md(response)
        self.output = self.fix_json(response)

        self.generate_output_html()
    
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
    

    @api.onchange("market_mapper_id","specific_instruction","lang_id")
    def _get_input(self, ):
        """
        {
        "@api.depends":["market_mapper_id.output"]
        }
        """
        for rec in self:
            rec.name = f"AP {rec.audience_profile_no}"
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



    def generate_output_html(self):
        try:
            self.output_html = self.md_to_html(
                self.json_to_markdown(
                    json.loads(self.clean_md(self.output)), level=3, max_level=4
                )
            )
        except Exception as e:
            _logger.error(self.output)
            raise UserError('Failed to generate Output HTML')

    def action_generate_angles(self):
        an = self.env['vit.angle_hook'].create({
            'name':'/',
            'audience_profiler_id': self.id,
            'gpt_model_id':self.gpt_model_id.id,
        })

        an._get_input()
        an.action_generate()
        an.action_split_angles()
        an.active=False
        
        for an in self.angle_hook_ids:
            an.action_split_hooks()
            an.generate_output_html()

            for hook in an.hook_ids:
                hook.generate_output_html()
