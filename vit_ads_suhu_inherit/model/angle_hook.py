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
  "big_ideas": [
    {
      "title": "...",
      "emotionsal_conflict": "...",
      "insight": "..."
    },
    {
      "title": "...",
      "emotionsal_conflict": "...",
      "insight": "..."
    }
  ],
  "strategic_notes": {
    "ab_test": [
      "...",
      "...",
      "..."
    ],
    "platform_adaptation": {
      "meta": "...",
      "tiktok": "...",
      "youtube": "..."
    },
    "category_entry_points": [
      "...",
      "...",
      "...",
      "..."
    ]
  },
  "angles": [
    {
      "angle": "...",
      "pov": "...",
      "hooks": [
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "..."
        },
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "real-talk"
        },
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "..."
        },
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "..."
        },
        {
          "text": "....",
          "emotions": ["...", "...", "..."],
          "technique": ".."
        }
      ]
    },
    {
      "angle": "...",
      "pov": "...",
      "hooks": [
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "..."
        },
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "real-talk"
        },
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "pertanyaan reflektif"
        },
        {
          "text": "...",
          "emotions": ["...", "...", "..."],
          "technique": "..."
        },
        {
          "text": "....",
          "emotions": ["...", "...", "..."],
          "technique": ".."
        }
      ]
    },
    ... # more angles 
  ]  
}
```
"""
class angle_hook(models.Model):
    _name = "vit.angle_hook"
    _inherit = "vit.angle_hook"

    def action_generate(self, ):

        if not self.gpt_prompt_id:
            raise UserError('Angle & Hook GPT empty')
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
        self.output = response

        self.generate_output_html()


    specific_instruction = fields.Text( string=_("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_angle_hook", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "angle_hook")], limit=1
        ).id
    
    lang_id = fields.Many2one(comodel_name="res.lang", related="product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="product_value_analysis_id.partner_id")    

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)

    @api.onchange("audience_profiler_id","product_value_analysis_id","lang_id")
    def _get_input(self, ):
        """
        {
        @api.onchange("audience_profiler_id","product_value_analysis_id")
        }
        """
        for rec in self:
            index = len(rec.audience_profiler_id.angle_hook_ids)+1
            rec.angle_no = index
            rec.name = f"AP {rec.audience_profiler_id.audience_profile_no} - ANGLE {index}: Master"
            rec.input = f"""
# ✅ AUDIENCE PROFILE:
---
{rec.audience_profiler_id.output}

# ✅ PRODUCT VALUE:
---
{rec.product_value_analysis_id.output}

# INSTRUCTIONS:
---
{rec.general_instruction}

{rec.specific_instruction or ''}

Response in {self.lang_id.name} language.

"""


    # def action_split_angles_md(self, ):
    #     import re
    #     from typing import List, Dict


    #     def extract_sections(text: str) -> Dict:
    #         result = {}

    #         # --- Extract BIG IDEA ---
    #         big_idea_pattern = re.compile(
    #             r"## === BIG IDEA ===(.*?)(?=---)",
    #             re.DOTALL
    #         )
    #         big_idea_match = big_idea_pattern.search(text)
    #         if big_idea_match:
    #             result["BIG_IDEA"] = big_idea_match.group(1).strip()

    #         # --- Extract CATATAN STRATEGIS ---
    #         catatan_pattern = re.compile(
    #             r"## === CATATAN STRATEGIS ===(.*)$",
    #             re.DOTALL
    #         )
    #         catatan_match = catatan_pattern.search(text)
    #         if catatan_match:
    #             result["strategic_notes"] = catatan_match.group(1).strip()

    #         # --- Extract ANGLES ---
    #         angle_pattern = re.compile(
    #             r"### .+? ANGLE (\d+) — \*\*(.+?)\*\*(.*?)(?=---|\Z)",
    #             re.DOTALL
    #         )

    #         angles = []
    #         for match in angle_pattern.finditer(text):
    #             angle_no = int(match.group(1))
    #             angle_title = match.group(2).strip()
    #             angle_body = match.group(3).strip()

    #             angles.append({
    #                 "angle_no": angle_no,
    #                 "title": angle_title,
    #                 "content": angle_body
    #             })

    #         result["ANGLES"] = angles

    #         return result


    #     extracted = extract_sections(self.output)

    #     for angle in extracted['ANGLES']:
    #         print(angle)
    #         default = dict(
    #             audience_profiler_id=self.audience_profiler_id.id,
    #             name=f"ANGLE {angle['angle_no']}",
    #             angle_no=angle['angle_no'],
    #             description=angle['title'],
    #             output=f"# ANGLE {angle['angle_no']} {angle['title']}\n\n{angle['content']}\n---\n# BIG_IDEA\n\n{extracted['BIG_IDEA']}\n---\n# strategic_notes\n\n{extracted['strategic_notes']}",
    #         )
    #         an = self.create(default)


    # def action_split_hooks_md(self, ):

    #     import re
    #     from typing import List, Dict

    #     def extract_hooks(text: str) -> List[Dict]:
    #         hooks = []

    #         # 1️⃣ Ambil blok Hooks sampai sebelum # BIG_IDEA
    #         hooks_block_pattern = re.compile(
    #             r"\*\*Hooks:\*\*(.*?)(?=\n---\n# BIG_IDEA)",
    #             re.DOTALL
    #         )

    #         hooks_block_match = hooks_block_pattern.search(text)
    #         if not hooks_block_match:
    #             return hooks

    #         hooks_block = hooks_block_match.group(1)

    #         # 2️⃣ Extract setiap hook bernomor
    #         hook_pattern = re.compile(
    #             r"\d+\.\s+\*\*“(.+?)”\*\*\s*\n\s*\*\(emotions:\s*(.+?)\s*\|\s*technique:\s*(.+?)\)",
    #             re.DOTALL
    #         )

    #         for match in hook_pattern.finditer(hooks_block):
    #             hooks.append({
    #                 "hook": match.group(1).strip(),
    #                 "emotions": match.group(2).strip(),
    #                 "technique": match.group(3).strip()
    #             })

    #         return hooks


    #     extracted_hooks = extract_hooks(self.output)

    #     from pprint import pprint
    #     pprint(extracted_hooks)

    #     hooks = []
    #     self.hook_ids = hooks
    #     self.hook_ids = [(0,0,{
    #         'angle_hook_id': self.id,
    #         'name':f"HOOK {i+1} - ANGLE {self.angle_no}",
    #         'hook_no': i+1,
    #         'description': hook['hook'],
    #         'output': f"# {hook['hook']}\n\nEmotion: {hook['emotions']}\ntechnique: {hook['technique']}"
    #     }) for i,hook in enumerate(extracted_hooks)]
        

    def action_split_angles(self, ):
        js = json.loads(self.clean_md(self.output))

        if not 'angles' in js:
            raise UserError('Split angles only in master angle')

        big_ideas= js['big_ideas']
        angles= js['angles']
        strategic_notes= js['strategic_notes']

        for i,angle in enumerate(angles):
            # angle = {
            #  "angle": "Siap Audit Itu Bukan Klaim, Tapi Bukti",
            #  "pov": "Sistem persuratan bukan soal fitur, tapi soal apakah bisa dipertanggungjawabkan di depan auditor dan pimpinan.",
            #  "hooks": []
            # }
            output={
                'big_ideas':big_ideas,
                'strategic_notes': strategic_notes
            }
            output.update(angle)
            default = dict(
                audience_profiler_id=self.audience_profiler_id.id,
                name=f"AP {self.audience_profiler_id.audience_profile_no} - ANGLE {i+1}: {angle['angle']}",
                angle_no=i+1,
                description=angle['angle'],
                output= json.dumps(output, indent=4),
                gpt_session=self.gpt_session,
                gpt_model_id=self.gpt_model_id.id,
            )
            an = self.create(default)

    def action_split_hooks(self, ):
        angle = json.loads(self.clean_md(self.output))
        for i,hook in enumerate(angle['hooks']):
            output = {
                'angle':angle['angle'],
                'pov':angle['pov'],
                'hook': hook
            }
            default = dict(
                angle_hook_id=self.id,
                name = f"AP {self.audience_profiler_id.audience_profile_no} - ANGLE {self.angle_no} - HOOK {i+1}",
                hook_no= i+1,
                description = hook['text'],
                output="```json\n"+json.dumps(output, indent=4) + "\n```",
                gpt_model_id=self.gpt_model_id.id,
            )
            hook = self.env['vit.hook'].create(default)

    def generate_output_html(self):
        self.output_html = self.md_to_html(
            self.json_to_markdown(
                json.loads(self.clean_md(self.output)), level=3, max_level=4
            )
        )
