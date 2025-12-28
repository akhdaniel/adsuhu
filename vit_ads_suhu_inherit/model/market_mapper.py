#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import json 
DEFAULT_SPECIFIC_INSTRUCTION = """
TUJUAN: Full map.
TrenScan otomatis sesuai SOP.
Market Indonesia.

REQUIRED JSON OUTPUT FORMAT:
```json
{
    "product": "...",
    "wilayah": "...",
    "tujuan": "full map",

    "segmentasi_pasar": {
      "demografis": {
        "usia": "...",
        "gender": "L/P",
        "lokasi": "...",
        "pekerjaan": "...",
        "penghasilan": "..."
      },
      "psikografis": {
        "minat": [
          "...",
          "...",
          "...",
          "..."
        ],
        "nilai_dan_gaya_hidup": ["..."],
        "kepribadian": ["..."]
      },
      "perilaku": {
        "kebiasaan_belanja": "...",
        "jenis_konten_dikonsumsi": "...",
        "respons_terhadap_promo": "..."
      }
    },

    "segment_prioritas": [
      {
        "nama": "...",
        "alasan": "...",
        "nilai_prioritas": ""
      },
      {
        "nama": "...",
        "alasan": "...",
        "nilai_prioritas": ""
      },
      {
        "nama": "...",
        "alasan": "...",
        "nilai_prioritas": ""
      }
    ],

    "channel_dan_touchpoint": {
      "platform_utama": ["LinkedIn", "Google Search", "YouTube", "Website (SEO)", "Email B2B", ...],
      "komunitas_online": [
        "...",
        "...",
        "..."
      ],
      "influencer_relevan": [
        "...",
        "...",
        "..."
      ]
    },

    "interest_dan_keyword_targeting": {
      "interest": [
        "...",
        "...",
        "..."
      ],
      "keyword": [
        "...",
        "...",
        "..."
      ]
    },

    "confidence_score": "",
    "keterbatasan": "..."
}
```
"""
class market_mapper(models.Model):
    _name = "vit.market_mapper"
    _inherit = "vit.market_mapper"

    def action_generate(self, ):
        pass
    
    specific_instruction = fields.Text( string=_("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)

    lang_id = fields.Many2one(comodel_name="res.lang", related="product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="product_value_analysis_id.partner_id")
    
    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_market_mapper", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "market_mapper")], limit=1
        ).id
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    
    @api.onchange("product_value_analysis_id","specific_instruction")
    def _get_input(self, ):
        """
        {
        "@api.depends":["product_value_analysis_id.output"]
        }
        """
        for rec in self:
            rec.name = f"MARKET MAP - {rec.product_value_analysis_id.name}"
            rec.input = f"""
# ✅ PROODUCT VALUE:
---
{rec.product_value_analysis_id.output}

# INSTRUCTIONS
---
{rec.general_instruction}

{rec.specific_instruction or ''}

Response in {rec.lang_id.name} language.


"""


    def action_create_audience_profiles(self, ):
        output = self.clean_md(self.output)
        js = json.loads(output)

        self.audience_profiler_ids = [(0,0,{
            'name':f'AUDIENCE PROFILE {i}',
            'audience_profile_no': i,
            'market_mapper_id': self.id,
            'description': x['nama'],
            'alasan': x['alasan'],
            'lang_id': self.lang_id.id
        }) for i,x in enumerate(js['segment_prioritas'], start=1)]

        self.audience_profiler_ids._get_input()