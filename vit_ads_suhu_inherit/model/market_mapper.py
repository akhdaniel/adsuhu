#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import json 
from .libs.openai_lib import generate_content
SIMULATE=True
SIMULATE_OUTPUT="""{
  "product": "GUIRENNIAO",
  "target_market": "Indonesia",
  "objective": "Full Map",
  "market_segmentation": {
    "demography": {
      "age": "20-45 tahun",
      "gender": "L/P (Unisex)",
      "location": "Kota besar dan menengah (Jakarta, Bandung, Surabaya, Bali, Yogyakarta, Medan), serta daerah dengan akses ke destinasi wisata alam.",
      "occupation": "Profesional muda, karyawan, entrepreneur, mahasiswa akhir, pasangan muda menikah, pekerja kreatif/freelancer.",
      "income": "Menengah ke atas (UMR hingga >10 juta per bulan), memiliki disposable income untuk lifestyle produk."
    },
    "psychographics": {
      "interests": [
        "Traveling dan petualangan alam (hiking, camping, road trip)",
        "Gaya hidup sehat dan aktif (olahraga ringan, jalan-jalan)",
        "Fashion casual dan streetwear",
        "Kuliner dan nongkrong di kafe",
        "Konten digital dan media sosial (Instagram, TikTok, YouTube)",
        "Kualitas hidup dan kenyamanan pribadi"
      ],
      "values_lifestyle": [
        "Praktis dan efisien",
        "Kualitas dan ketahanan produk",
        "Gaya hidup aktif dan dinamis",
        "Kebersamaan dengan pasangan/teman",
        "Kepercayaan diri dan penampilan",
        "Kesadaran akan nilai uang (value for money)"
      ],
      "personality_traits": [
        "Praktis",
        "Adventurous",
        "Socially-conscious",
        "Trend-aware",
        "Comfort-seeker",
        "Convenience-driven"
      ]
    },
    "behaviour": {
      "shopping_behavior": "Online-first (e-commerce, social commerce), riset review dan perbandingan produk sebelum beli, sensitif terhadap panduan ukuran dan kebijakan retur, tertarik pada produk multifungsi dan bernilai tambah tinggi.",
      "content_consumption_preferences": "Video pendek (TikTok, Reels), review produk di YouTube, konten visual di Instagram (feed & stories), blog/artikel perbandingan dan rekomendasi, komunitas online terkait hobi.",
      "response_to_promotions": "Responsif terhadap testimoni user-generated content (UGC), diskon periode tertentu (flash sale, hari besar), program referral, dan konten edukatif yang menyelesaikan masalah (how-to, problem-solution)."
    }
  },
  "priority_segments": [
    {
      "name": "Pasangan Muda Perkotaan (Active Urban Couples)",
      "reason": "Sesuai dengan persona awal dan diferensiasi <em>matching couple</em>. Segment ini memiliki buying trigger emosional (kebersamaan, gaya) dan rasional (efisiensi belanja untuk dua orang). Mereka aktif di media sosial, menjadi early adopters trend, dan memiliki daya beli untuk produk lifestyle. Prioritas tinggi karena langsung menyasar inti USP produk.",
      "prioritas_value": "Tinggi"
    },
    {
      "name": "Profesional Muda & Freelancer dengan Gaya Hidup Dinamis (Dynamic Young Professionals)",
      "reason": "Memiliki kebutuhan nyata akan kenyamanan seharian (banyak berdiri/berjalan) dan fleksibilitas untuk transisi dari kerja ke aktivitas santai/outdoor. Mereka mencari produk serba guna yang mendukung mobilitas tinggi, menghargai kualitas dan ketahanan, serta aktif dalam riset online. Budget lebih pasti dan motive rasional kuat.",
      "prioritas_value": "Tinggi"
    },
    {
      "name": "Pecinta Aktivitas Outdoor Rekreasi (Recreational Outdoor Enthusiasts)",
      "reason": "Memiliki pain point spesifik terkait keamanan (anti slip) dan ketahanan di medan outdoor. Mereka adalah pembeli solution-aware yang mencari sandal untuk hiking, camping, atau traveling. Segment ini mungkin lebih kecil volumenya, tetapi memiliki intent pembelian yang kuat dan loyalitas tinggi jika produk memenuhi performa yang dijanjikan.",
      "prioritas_value": "Sedang"
    }
  ],
  "channel_and_touchpoint": {
    "main_platform": [
      "Instagram (Feed, Reels, Stories)",
      "TikTok",
      "Google Search (SEM & SEO)",
      "Tokopedia",
      "Shopee",
      "YouTube",
      "Website/Blog (SEO Content)",
      "Email Marketing (Post-purchase, Newsletter)"
    ],
    "online_communities": [
      "Grup Facebook (Backpacker Indonesia, Hiking Indonesia, Pasangan Travel)",
      "Forum Kaskus (FJB Alas Kaki, Lifestyle)",
      "Subreddit r/indonesia atau r/backpacking",
      "Grup WhatsApp/Telegram komunitas pecinta alam lokal",
      "Komunitas digital streetwear/casual fashion"
    ],
    "relevan_influencers": [
      "Couple Travel Influencers",
      "Outdoor & Hiking Content Creators",
      "Lifestyle & Fashion Vloggers",
      "Reviewer Produk Alas Kaki (Footwear Review Channels)",
      "Content Creator dengan tema work-life balance dan kenyamanan"
    ]
  },
  "interest_and_keyword_targeting": {
    "interests": [
      "Hiking & Camping",
      "Traveling",
      "Streetwear Fashion",
      "Healthy Lifestyle",
      "Couple Activities",
      "Online Shopping",
      "Product Reviews"
    ],
    "keywords": [
      "sandal pria nyaman seharian",
      "sandal wanita anti slip",
      "sandal couple matching",
      "sandal untuk hiking ringan",
      "sandal unisex tahan air",
      "alas kaki nyaman kerja",
      "sandal empuk anti lelah",
      "review sandal outdoor",
      "sandal serbaguna casual outdoor",
      "beli sandal online panduan ukuran",
      "sandal bahan eva empuk",
      "sandal aman musim hujan"
    ]
  },
  "confidence_score": "78",
  "limitation": "Analisis berdasarkan data produk dan tren umum Indonesia. Tidak memiliki data spesifik market share kompetitor, harga pasti produk, atau data penjualan aktual. Segmentasi prioritas mengandalkan logika value proposition dan buying trigger, namun perlu validasi dengan data demografi pembeli nyata. Tren fashion cepat berubah, perlu adaptasi konten secara berkala."
}"""
DEFAULT_SPECIFIC_INSTRUCTION = """
REQUIRED JSON OUTPUT FORMAT:
```json
{
    "product": "{{product_name}}",
    "target_market": "{{target_market}}",
    "objective": "{{objective}}",

    "market_segmentation": {
      "demography": {
        "age": "...",
        "gender": "L/P",
        "location": "...",
        "occupation": "...",
        "income": "..."
      },
      "psychographics": {
        "interests": [
          "...",
          "...",
          "...",
          "..."
        ],
        "values_lifestyle": ["..."],
        "personality_traits": ["..."]
      },
      "behaviour": {
        "shopping_behavior": "...",
        "content_consumption_preferences": "...",
        "response_to_promotions": "..."
      }
    },

    "priority_segments": [
      {
        "name": "...",
        "reason": "...",
        "prioritas_value": ""
      },
      {
        "name": "...",
        "reason": "...",
        "prioritas_value": ""
      },
      {
        "name": "...",
        "reason": "...",
        "prioritas_value": ""
      }
    ],

    "channel_and_touchpoint": {
      "main_platform": [
        "LinkedIn", 
        "Google Search", 
        "YouTube", 
        "Website (SEO)", 
        "Email B2B", "..." ], # add more relevant platform for marketing
      "online_communities": [
        "...",
        "...",
        "..."
      ],
      "relevan_influencers": [
        "...",
        "...",
        "..."
      ]
    },

    "interest_and_keyword_targeting": {
      "interests": [
        "...",
        "...",
        "..."
      ],
      "keywords": [
        "...",
        "...",
        "..."
      ]
    },

    "confidence_score": "",
    "limitation": "..."
}
```
"""
class market_mapper(models.Model):
    _name = "vit.market_mapper"
    _inherit = "vit.market_mapper"

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
        
        if SIMULATE:
          self.output=SIMULATE_OUTPUT
        else:
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
    
    @api.onchange("product_value_analysis_id","lang_id","specific_instruction")
    def _get_input(self, ):
        """
        {
        "@api.depends":["product_value_analysis_id.output"]
        }
        """
        for rec in self:
            rec.name = f"MARKET MAP"
            rec.target_market = rec.product_value_analysis_id.target_market
            rec.specific_instruction = (
                rec.specific_instruction
                .replace('{{product_name}}', rec.product_value_analysis_id.name)
                .replace('{{target_market}}', rec.target_market or 'Indonesia')
                .replace('{{objective}}', rec.objective or 'Full map')
            )
            rec.input = f"""
# ✅ PROODUCT VALUE:
---
{rec.product_value_analysis_id.output}

# INSTRUCTIONS
---
{rec.general_instruction}

---
TrenScan otomatis sesuai SOP.
Response in {rec.lang_id.name} language.

{rec.specific_instruction or ''}
"""
            


    def action_generate_audience_profiler(self, ):
        output = self.clean_md(self.output)
        js = json.loads(output)
        _logger.info(js)
        
        if not 'priority_segments' in js:
          raise UserError('priority_segments not found')

        for i,x in enumerate(js['priority_segments'], start=1):
            ap = self.env['vit.audience_profiler'].create({
                'name':f'/',
                'audience_profile_no': i,
                'market_mapper_id': self.id,
                'description': x['name'],
                'alasan': x['reason'],
                'lang_id': self.lang_id.id,
                'gpt_model_id': self.gpt_model_id.id,
                'market_mapper_id': self.id
            })
         
            ap._get_input()
            if not ap.input:
              raise UserError(f'AP {i} Input empty')
            ap.action_generate()   

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