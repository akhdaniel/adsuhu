#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import json
from .libs.openai_lib import generate_content
SIMULATE=False
SIMULATE_OUTPUT="""{
  "big_ideas": [
    {
      "title": "Satu Sandal, Semua Cerita: Akhiri Ribetnya Ganti Sandal untuk Setiap Aktivitas Keluarga",
      "emotionsal_conflict": "Keinginan untuk memberikan pengalaman liburan yang sempurna vs frustasi dengan persiapan yang ribet dan peralatan yang tidak mendukung.",
      "insight": "Keluarga muda urban menghabiskan waktu berharga mereka untuk mempersiapkan dan membersihkan berbagai sandal untuk aktivitas berbeda, padahal yang mereka inginkan hanyalah fokus pada kebahagiaan bersama."
    },
    {
      "title": "Jaminan Aman, dari Kaki Hingga Dompet: Belanja Online Tanpa Ragu untuk Kebutuhan Keluarga",
      "emotionsal_conflict": "Kebutuhan akan solusi praktis vs ketakutan akan risiko salah beli online dan proses return yang menyulitkan.",
      "insight": "Rasa aman dalam berbelanja online sama pentingnya dengan keamanan produk itu sendiri. Keluarga butuh kepastian bahwa investasi mereka terlindungi, dari ukuran yang tepat hingga kebijakan pengembalian yang jelas."
    },
    {
      "title": "Kepintaran Orang Tua yang Terlihat: Solusi Praktis yang Bikin Keluarga Kompak dan Nyaman",
      "emotionsal_conflict": "Keinginan untuk diakui sebagai orang tua yang cerdas dan perhatian vs kekhawatiran terlihat boros atau salah pilih barang.",
      "insight": "Keputusan membeli produk yang tepat adalah bentuk kebanggaan dan pengakuan sosial bagi orang tua. Sandal yang serbaguna, awet, dan matching untuk keluarga adalah bukti nyata kepintaran mereka dalam mengatur kebutuhan rumah tangga."
    }
  ],
  "strategic_notes": {
    "ab_test": [
      "Fear vs Relief: Tampilkan visual anak hampir terpeleset di waterpark (fear) vs visual keluarga tertawa ceria dengan sandal aman (relief).",
      "Proof vs Promise: Video demo sandal digosok di permukaan licin dan basah (proof) vs narasi tentang <em>jaminan anti slip</em> (promise).",
      "Authority vs Empathy: Testimoni dari ahli podiatri atau review dari influencer keluarga besar (authority) vs cerita sehari-hari ibu yang frustasi cuci sandal (empathy).",
      "Hemat Individu vs Hemat Keluarga: Harga per pasang untuk diri sendiri vs harga paket keluarga 4 dengan diskon dan gratis ongkir."
    ],
    "platform_adaptation": {
      "meta": "Gunakan visual scroll-stopping: close-up sandal kotor vs bersih hanya dengan dilap. Headline singkat, manfaat jelas: <em>Gak Perlu Ganti Sandal, dari Mall ke Waterpark Aman!</em> Sertakan trust badges: <em>COD</em>, <em>Garansi Tukar Ukuran</em>.",
      "tiktok": "Buat skenario pendek: <em>Sound ON</em> suara anak mengeluh sandal basah dan bau. Cut ke orang tua dengan santai melap sandal GUIRENNIAO hingga bersih. Pakai trending audio tentang <em>life hack</em> atau solusi praktis ibu-ibu.",
      "youtube": "Video format <em>Unboxing & Real Test</em> oleh keluarga. Tunjukkan proses dari buka kotak, cek ukuran, dipakai ke taman (kering), lalu langsung ke area basah waterpark. Highlight momen <em>anti-slip test</em> dan kemudahan membersihkannya setelahnya."
    },
    "category_entry_points": [
      "Saat merencanakan itinerary liburan akhir pekan yang mencakup mall dan waterpark.",
      "Setelah pulang liburan dan melihat tumpukan sandal kotor dan bau yang harus dibersihkan.",
      "Melihat anak atau pasangan hampir terpeleset di lantai kamar mandi umum atau kolam renang.",
      "Saat merapikan gudang/rak sepatu dan menyadari terlalu banyak sandal sekali pakai yang sudah rusak.",
      "Ketika mendapat ajakan spontan jalan-jalan dan tidak punya sandal yang cocok untuk semua kemungkinan destinasi.",
      "Membuka marketplace dan melihat notifikasi diskon akhir bulan atau gajian, sambil ingat kebutuhan sandal baru."
    ]
  },
  "angles": [
    {
      "angle": "Solusi Orang Tua Pintar untuk Menghemat Waktu dan Tenaga",
      "pov": "Kami memahami betapa berharganya waktu luang Anda. Sandal ini dirancang untuk memangkas ritual ribet persiapan dan bersih-bersih setelah liburan, sehingga Anda bisa fokus pada momen kebersamaan.",
      "hooks": [
        {
          "text": "Lelah habiskan weekend cuma untuk cuci dan jemur sandal kotor?",
          "emotions": [
            "Kelelahan (Frustration)",
            "Kebosanan"
          ],
          "technique": "pertanyaan reflektif"
        },
        {
          "text": "Beli ini, simpan tenaga buat hal yang lebih seru sama anak.",
          "emotions": [
            "Kepuasan (Satisfaction/Relief)",
            "Harapan"
          ],
          "technique": "real-talk"
        },
        {
          "text": "Orang tua praktis pilih sandal yang tinggal lap, langsung kering.",
          "emotions": [
            "Kebanggaan (Pride)",
            "Kepuasan (Satisfaction/Relief)"
          ],
          "technique": "social proof"
        },
        {
          "text": "Stop jadi <em>tukang cuci sandal</em> setiap pulang liburan.",
          "emotions": [
            "Kelelahan (Frustration)",
            "Kebebasan"
          ],
          "technique": "contrast"
        },
        {
          "text": "Waktu Anda terbatas. Sandal Anda harus serba bisa.",
          "emotions": [
            "Tekanan",
            "Kepraktisan"
          ],
          "technique": "authority-based"
        }
      ]
    },
    {
      "angle": "Jaminan Keamanan yang Memberi Anda Ketengan Pikiran",
      "pov": "Keselamatan keluarga adalah prioritas utama. Kami menghilangkan kekhawatiran terselip di sela-sela kegembiraan, dengan teknologi grip yang teruji dan material yang aman, sehingga Anda bisa bernapas lega saat anak-anak berlarian.",
      "hooks": [
        {
          "text": "Jantung langsung deg-degan lihat anak lari di lantai basah waterpark?",
          "emotions": [
            "Kekhawatiran (Fear)",
            "Kecemasan"
          ],
          "technique": "fear-based"
        },
        {
          "text": "Biarkan mereka main bebas. Anda yang tenang.",
          "emotions": [
            "Ketenangan",
            "Kepuasan (Satisfaction/Relief)"
          ],
          "technique": "relief-based"
        },
        {
          "text": "Grip khusus ini kami desain agar Anda tidak perlu teriak <em>awas licin!</em> setiap saat.",
          "emotions": [
            "Kepercayaan",
            "Kepuasan (Satisfaction/Relief)"
          ],
          "technique": "proof-based"
        },
        {
          "text": "Bukan cuma tahan air. Tapi aman di atas air.",
          "emotions": [
            "Keamanan",
            "Kepercayaan Diri"
          ],
          "technique": "contrast"
        },
        {
          "text": "Investasi kecil untuk rasa aman yang besar selama liburan.",
          "emotions": [
            "Kepastian",
            "Kebijaksanaan"
          ],
          "technique": "real-talk"
        }
      ]
    },
    {
      "angle": "Kepastian Belanja Online Tanpa Drama Salah Ukuran",
      "pov": "Kami menghapus ketidakpastian dari belanja online. Dengan panduan ukuran centimeter-akurat dan jaminan tukar yang mudah, Anda bisa klik \"beli\" dengan percaya diri, bukan dengan doa.",
      "hooks": [
        {
          "text": "Kapok beli sandal online karena ukuran selalu meleset?",
          "emotions": [
            "Kekecewaan",
            "Kecurigaan"
          ],
          "technique": "pertanyaan reflektif"
        },
        {
          "text": "Ukur pakai penggaris, dapat pas di kaki. Garansi kami jamin.",
          "emotions": [
            "Kepastian",
            "Kepercayaan"
          ],
          "technique": "proof-based"
        },
        {
          "text": "Bayar pas barang sampai. Aman pakai COD, salah ukuran bisa tukar.",
          "emotions": [
            "Rasa Aman",
            "Kenyamanan"
          ],
          "technique": "real-talk"
        },
        {
          "text": "Ragu ukuran? CS kami bantu sampai yakin. Gak perlu nebak-nebak.",
          "emotions": [
            "Kepercayaan",
            "Kepuasan (Satisfaction/Relief)"
          ],
          "technique": "authority-based"
        },
        {
          "text": "Belanja untuk keluarga harusnya bikin senang, bukan bikin pusing.",
          "emotions": [
            "Kelelahan (Frustration)",
            "Harapan"
          ],
          "technique": "contrast"
        }
      ]
    },
    {
      "angle": "Hemat Cerdas dengan Investasi Produk Multi-Fungsi yang Awet",
      "pov": "Kami menawarkan logika keuangan yang sederhana: beli satu kali untuk segala kebutuhan, alih-alih berulang kali membeli barang khusus yang cepat rusak. Ini adalah keputusan hemat yang terlihat dari hari pertama hingga bertahun-tahun kemudian.",
      "hooks": [
        {
          "text": "Sudah habis berapa untuk beli sandal waterpark, sandal taman, sandal mall yang semuanya cepat rusak?",
          "emotions": [
            "Kekecewaan",
            "Pemborosan"
          ],
          "technique": "pertanyaan reflektif"
        },
        {
          "text": "Gak perlu boros beli 3 sandal berbeda. Cukup 1 yang bisa dipakai untuk semuanya.",
          "emotions": [
            "Kepuasan (Satisfaction/Relief)",
            "Kecerdasan"
          ],
          "technique": "contrast"
        },
        {
          "text": "Material EVA awet, gak gampang jebol meski dipakai ke mana-mana.",
          "emotions": [
            "Kepercayaan",
            "Kepastian"
          ],
          "technique": "proof-based"
        },
        {
          "text": "Beli sekeluarga, lebih hemat. Liburan kompak, budget juga tetap aman.",
          "emotions": [
            "Keharmonisan",
            "Kebanggaan (Pride)"
          ],
          "technique": "social proof"
        },
        {
          "text": "Ini sandal untuk besok, bulan depan, dan liburan tahun depan.",
          "emotions": [
            "Kepastian",
            "Perencanaan"
          ],
          "technique": "urgency"
        }
      ]
    }
  ]
}"""
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


    specific_instruction = fields.Text( string=("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_angle_hook", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "angle_hook")], limit=1
        ).id
    
    lang_id = fields.Many2one(comodel_name="res.lang", related="product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="product_value_analysis_id.partner_id")    

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=("GPT Prompt"), default=_get_default_prompt)

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
        try:
            self.output_html = self.md_to_html(
                self.json_to_markdown(
                    json.loads(self.clean_md(self.output)), level=3, max_level=4
                )
            )
        except Exception as e:
            _logger.error(self.output)
            raise UserError('Failed to generate Output HTML')