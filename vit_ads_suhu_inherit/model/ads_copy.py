#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import re
from typing import List, Dict
import json
from .libs.openai_lib import generate_content

def strip_emoji(text: str) -> str:
    # Remove common emoji ranges (optional)
    return re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]", "", text)

SIMULATE=False
SIMULATE_OUTPUT="""{
  "angle": "Hemat Cerdas dengan Investasi Produk Multi-Fungsi yang Awet",
  "hook": "Material EVA awet, gak gampang jebol meski dipakai ke mana-mana.",
  "ads_copy": [
    {
      "name": "COPY A - Relevance Boost",
      "primary_text": "Kalau kamu dan pasangan suka jalan-jalan dari mall ke taman, lalu ke waterpark, pasti butuh sandal yang tahan banting. Sandal GUIRENNIAO pakai material EVA yang awet, gak gampang rusak meski dipakai untuk semua aktivitas itu. Cocok untuk gaya hidup aktif kalian.",
      "headline": "1 Sandal untuk Semua Aktivitas Bersama",
      "cta": "Lihat Panduan Ukuran",
      "visual_suggestion": "Visual split-screen: kiri, tumpukan sandal kotor dan rusak (waterpark, taman, mall). Kanan, satu pasang sandal GUIRENNIAO bersih di atas peta dengan pin lokasi mall, taman, dan waterpark."
    },
    {
      "name": "COPY B - Intent Boost",
      "primary_text": "Lelah beli sandal waterpark, sandal taman, sandal mall yang semuanya cepat rusak? Solusinya bukan beli lebih banyak, tapi beli yang lebih awet. Sandal GUIRENNIAO dengan material EVA didesain untuk penggunaan intensif. Satu pasang, ganti semua kebutuhan.",
      "headline": "Stop Boros Ganti Sandal Terus",
      "cta": "Cek Varian Warna",
      "visual_suggestion": "Visual close-up tangan memegang 3 pasang sandal berbeda yang sudah rusak (sol terkelupas, tali putus). Lalu tangan tersebut mengambil 1 pasang sandal GUIRENNIAO yang masih baru dan kokoh."
    },
    {
      "name": "COPY C - Emotional Boost",
      "primary_text": "Rasanya kesal banget beli sandal mahal, eh cuma bertahan beberapa bulan. Investasi yang sia-sia. Sekarang, rasakan kepastian. Material EVA pada sandal GUIRENNIAO terbukti awet, gak gampang jebol meski dipakai ke mana-mana. Beli sekali, pakai bertahun-tahun.",
      "headline": "Akhiri Frustasi Sandal Cepat Rusak",
      "cta": "Dapatkan Jaminan Kepuasan",
      "visual_suggestion": "Visual testimoni style: Orang memegang sandal GUIRENNIAO yang sudah terlihat dipakai (sedikit kotor), lalu menunjukkan sol dan material yang masih utuh dan tidak rusak. Ekspresi wajah puas dan lega."
    },
    {
      "name": "COPY D - Ultra",
      "primary_text": "Untuk pasangan yang aktif: butuh sandal untuk date di mall, piknik di taman, dan main air di waterpark. Jangan buang uang untuk 3 sandal berbeda yang cepat rusak. Sandal GUIRENNIAO pakai material EVA awet, didesain tahan untuk semua kegiatan itu. Hemat, praktis, dan pasti awet.",
      "headline": "Hemat Cerdas: 1 Sandal, Semua Aktivitas",
      "cta": "Pilih Warna Matching",
      "visual_suggestion": "Visual carousel 3 adegan singkat: 1. Pasangan jalan di mall pakai sandal GUIRENNIAO. 2. Duduk di taman pakai sandal yang sama. 3. Tertawa di waterpark pakai sandal yang sama. Highlight logo/desain sandal yang konsisten di setiap adegan."
    }
  ],
  "angle_library": [
    "Hemat Cerdas dengan Investasi Produk Multi-Fungsi yang Awet",
    "Satu Sandal, Semua Cerita: Akhiri Ribetnya Ganti Sandal untuk Setiap Aktivitas",
    "Jaminan Aman, dari Kaki Hingga Dompet: Belanja Online Tanpa Ragu untuk Kebutuhan Keluarga",
    "Kepintaran Orang Tua yang Terlihat: Solusi Praktis yang Bikin Keluarga Kompak",
    "Nyaman Sepanjang Hari, Aman di Segala Medan: Sandal untuk Gaya Hidup Dinamis",
    "Investasi Kaki: Kenyamanan dan Keamanan yang Bertahan Lama",
    "Matching Style, Maximum Function: Sandal Pasangan untuk Petualangan Sehari-hari",
    "Dari Kafe ke Hiking: Fleksibilitas Tanpa Kompromi dalam Satu Desain",
    "Belanja Online yang Pasti: Sandal dengan Panduan Ukuran Akurat dan Jaminan",
    "Minimalisir Risiko, Maksimalkan Pengalaman: Alas Kaki yang Didukung Layanan Lengkap"
  ],
  "hook_library": [
    "Sudah habis berapa untuk beli sandal waterpark, sandal taman, sandal mall yang semuanya cepat rusak?",
    "Gak perlu boros beli 3 sandal berbeda. Cukup 1 yang bisa dipakai untuk semuanya.",
    "Material EVA awet, gak gampang jebol meski dipakai ke mana-mana.",
    "Beli sekeluarga, lebih hemat. Liburan kompak, budget juga tetap aman.",
    "Ini sandal untuk besok, bulan depan, dan liburan tahun depan.",
    "Kaki pegal dan takut slip? Itu tanda sandal lama sudah tidak layak pakai.",
    "Bayangin, dari kafe langsung ke taman basah tanpa ganti sandal. Bisa.",
    "Gak ada lagi drama salah ukuran dan ribet return. Panduan kami bikin pasti.",
    "Tampil kompak dengan pasangan, tanpa perlu keluar duit ekstra untuk desain matching.",
    "Bahan empuk yang bikin jalan seharian terasa seperti berjalan di awan.",
    "Sol yang mencengkeram, biar kamu jalan di trotoar licin pun percaya diri.",
    "Cukup dilap, bersih. Sandal ini dibuat untuk yang gak suka ribet.",
    "Investasi sekali, kebahagiaan berkali-kali. Sandal yang menemani setiap momen.",
    "Jangan biarkan sandal biasa menghalangi petualangan spontan kamu akhir pekan ini.",
    "Rasanya lega banget pas audit barang di lemari, sandal ini masih bagus padahal udah setahun.",
    "Dibanding beli sepatu sneaker mahal, sandal ini lebih versatile untuk aktivitas kota.",
    "Anak-anak main air kotor? Tenang, sandal ini gampang banget dibersihin.",
    "Gak perlu mikir <em>sandal apa yang harus aku pakai hari ini?</em> Jawabannya selalu ini.",
    "Bukan cuma gaya, ini soal keputusan finansial yang pintar untuk jangka panjang.",
    "Perlindungan lengkap: untuk kaki kamu, dompet kamu, dan ketenangan pikiran kamu."
  ],
  "landing_page": {
    "section_1_hero": {
      "name": "Hero - Reframing + Output",
      "headline": "Hemat Itu Bukan Harga Murah, Tapi Nilai yang Bertahan Lama",
      "subheadline": "Stop lingkaran beli sandal baru tiap musim. Sandal GUIRENNIAO dengan material EVA awet adalah investasi sekali untuk semua aktivitas kamu dan pasangan.",
      "primary_cta": "Temukan Sandal Pasangan Kamu"
    },
    "section_2_proof": {
      "name": "PROOF OF REALITY - Bikin <em>ini beneran</em>",
      "title": "Apa yang Sebenarnya Terjadi dengan Sandal Biasa?",
      "points": [
        "Sandal waterpark cepat bau dan lapuk karena terus basah.",
        "Sandal taman solnya cepat aus dan licin setelah beberapa bulan dipakai.",
        "Sandal mall nyaman di awal, tapi bikin kaki pegal kalau dipakai jalan lama.",
        "Hasilnya: lemari penuh sandal, dompet terkuras, tapi tetap tidak punya solusi ideal."
      ]
    },
    "section_3_problem": {
      "name": "PROBLEM CALLOUT - Mirror Moment",
      "title": "Masalahnya Bukan di Aktivitas Kamu, Tapi di Kualitas Sandalnya",
      "description": "Kamu dan pasangan punya gaya hidup yang dinamis. Masalah muncul ketika sandal yang ada tidak dirancang untuk mengimbangi ritme itu. Bukan salah kamu sering jalan-jalan, tapi sandalnya yang gampang nyerah."
    },
    "section_4_solution": {
      "name": "SOLUTION - Reframe + Path",
      "title": "Perkenalkan, Logika Baru: Satu Sandal, Segala Medan",
      "description": "Sandal GUIRENNIAO. Dibangun dengan material EVA berkualitas yang awet, menggabungkan kenyamanan insole empuk untuk seharian dengan performa sol anti slip untuk keamanan. Satu desain unisex yang stylish, siap menemani dari kafe hingga trail hiking ringan."
    },
    "section_5_value_stack": {
      "name": "VALUE STACK - Bikin <em>worth it</em>",
      "title": "Apa yang Membuat Sandal Ini Berbeda?",
      "values": [
        "Material EVA Awet: Tahan aus, anti air, dan tidak gampang jebol meski untuk penggunaan intensif.",
        "Kenyamanan Maksimal: Insole empuk dan bahan halus elastis mengurangi kelelahan kaki sepanjang hari.",
        "Keamanan Terjamin: Sol dengan pola cengkeraman kuat untuk traction yang baik di berbagai permukaan.",
        "Kepraktisan Total: Mudah dibersihkan, cepat kering, dan desain versatile untuk banyak kesempatan.",
        "Kepastian Belanja: Panduan ukuran akurat dan kebijakan pengembalian yang jelas untuk rasa aman bertransaksi."
      ]
    },
    "section_6_objection_handling": {
      "name": "OBJECTION HANDLING - Turunin Risk",
      "title": "Masih Ragu? Ini Jawaban Kami",
      "description": "<em>Material EVA tahan lama gak sih?</em> - Ya. EVA dikenal karena ketahanan dan elastisitasnya, digunakan pada alas kaki premium. Kami pilih grade terbaik.<br><em>Kalau ukuran tidak pas?</em> - Kami sediakan tabel konversi detail. Masih ragu? Chat CS kami untuk konsultasi. Dilindungi kebijakan tukar ukuran.<br><em>Harganya lebih mahal dari sandal biasa?</em> - Bayangkan kamu menghemat 2-3 pembelian sandal khusus yang cepat rusak. Ini investasi nilai, bukan hanya harga."
    },
    "section_7_super_benefit": {
      "name": "SUPER BENEFIT - Emotional Payoff",
      "title": "Manfaat Terbesar: Kebebasan dan Kepastian",
      "description": "Ini lebih dari sepasang sandal. Ini adalah kartu bebas untuk petualangan spontan bersama pasangan tanpa pusing mikirin alas kaki. Ini adalah kepastian bahwa uang kamu diinvestasikan pada sesuatu yang tahan lama. Ini adalah rasa percaya diri bahwa pilihan kamu adalah pilihan yang cerdas."
    },
    "section_8_final_cta": {
      "name": "FINAL CTA - Calm Conversion",
      "headline": "Pilih Warna, Konfirmasi Ukuran, dan Mulai Petualangan Tanpa Khawatir",
      "cta": "Beli Sekarang dengan Jaminan Kepuasan"
    }
  },
  "video_script": {
    "length": "30-45s",
    "scripts": [
      {
        "name": "hook (stop scroll)",
        "duration": "0-3s",
        "visuals": [
          "Close-up cepat: sepasang sandal GUIRENNIAO diinjak di atas genangan air di trotoar, lalu diangkat. Solnya basah tapi tampak kokoh."
        ],
        "text_overlay": "Material EVA yang gak gampang jebol.",
        "voice_over": "(Sound effect: cipratan air) Gak percaya sandal bisa se-awet ini?"
      },
      {
        "name": "problem mapping",
        "duration": "4-10s",
        "visuals": [
          "Montase cepat: wanita melihat tumpukan sandal kotor di teras (sandal waterpark, sandal taman). Pria mengeluh kaki pegal sambil melepas sandal mall. Ekspresi frustasi."
        ],
        "text_overlay": "Sandal waterpark... sandal taman... sandal mall...",
        "voice_over": "Aktivitas sama pasangan seru, tapi persiapan sandalnya bikin pusing. Beli terpisah, cepat rusak, dan akhirnya numpuk."
      },
      {
        "name": "insight shift",
        "duration": "11-18s",
        "visuals": [
          "Tampak atas: tangan menyapu semua sandal lama ke samping. Lalu, dengan tenang menempatkan sepasang sandal GUIRENNIAO (pria & wanita) di tengah layar."
        ],
        "text_overlay": "Solusinya: BUKAN beli lebih banyak.",
        "voice_over": "Masalahnya bukan butuh lebih banyak sandal. Tapi butuh SANDAL YANG LEBIH BAIK. Yang satu bisa untuk semuanya."
      },
      {
        "name": "solution",
        "duration": "19-27s",
        "visuals": [
          "Visual produk spin 360 derajat. Lalu split screen: kiri, diagram material EVA dengan ikon ketahanan. Kanan, close-up pola sol anti slip."
        ],
        "text_overlay": "Sandal GUIRENNIAO. Material EVA Awet. Sol Anti Slip.",
        "voice_over": "Ini dia Sandal GUIRENNIAO. Intinya: material EVA pilihan yang awet dan tahan banting, ditambah sol yang mencengkeram untuk keamanan kamu."
      },
      {
        "name": "kill effort + proof",
        "duration": "28-34s",
        "visuals": [
          "Adegan singkat berurutan: 1. Sandal dicuci dengan semprotan air, langsung bersih. 2. Sandal ditekan-tekan, kembali ke bentuk semula. 3. Pasangan memakainya, berjalan dari lantai kering (kafe) ke lantai basah (kolam) dengan muka percaya diri."
        ],
        "text_overlay": "Praktis. Elastis. Siap untuk apa aja.",
        "voice_over": "Gampang dibersihkan, bahannya elastis nyaman. Dan yang paling penting: siap untuk diajak dari kafe, ke taman, langsung ke waterpark. Gak perlu ganti."
      },
      {
        "name": "reset failure",
        "duration": "35-41s",
        "visuals": [
          "Close-up wajah pasangan tersenyum lega, saling pandang. Kamera pan ke bawah, memperlihatkan sandal matching mereka yang dipakai."
        ],
        "text_overlay": "Hemat uang. Hemat waktu. Tenang pikiran.",
        "voice_over": "Jadi, lupakan rasa takut sandal cepat rusak. Dengan Sandal GUIRENNIAO, kamu investasi sekali untuk kenyamanan dan keamanan yang bertahan lama."
      },
      {
        "name": "cta (soft, meta-safe)",
        "duration": "42-45s",
        "visuals": [
          "Produk diam di atas background putih bersih. Logo GUIRENNIAO. Tombol CTA <em>Pilih Warna Matching</em> muncul."
        ],
        "text_overlay": "Sandal GUIRENNIAO. Untuk gaya hidup tanpa batas.",
        "voice_over": "Pilih warna favorit kamu dan pasangan. Cek panduan ukuran kami yang akurat di link bawah ini."
      }
    ]
  },
  "catatan_produksi": [
    "format: 9:16 (Vertical Video)",
    "subtitle wajib untuk setiap scene",
    "hook teks muncul di detik ke-0-2",
    "Gunakan musik background upbeat dan modern, namun tidak terlalu keras agar voice over jelas.",
    "Pastikan visual produk (warna, detail) konsisten dan terlihat premium di semua shot.",
    "Untuk scene proof (durasi 28-34s), gunakan transisi cepat dan dynamic untuk menunjukkan kegunaan multifungsi.",
    "Aktor harus merepresentasikan pasangan muda urban (20-35 thn) dengan gaya relatable."
  ]
}"""

DEFAULT_SPECIFIC_INSTRUCTION ="""
REQUIRED JSON OUTPUT FORMAT:

```json
{
  "angle": "...",
  "hook": "...",

  "ads_copy": [{
    "name":"COPY A - Relevance Boost",
    "primary_text": "...",
    "headline": "...",
    "cta": "...",
    "visual_suggestion": "...."
  },{
    "name":"COPY B - Intent Boost",
    "primary_text": "...",
    "headline": "...",
    "cta": "...",
    "visual_suggestion": "...."    
  },{
    "name":"COPY C - Emotional Boost",
    "primary_text": "...",
    "headline": "...",
    "cta": "...",
    "visual_suggestion": "...."    
  },{
    "name":"COPY D - Ultra",
    "primary_text": "...",
    "headline": "...",
    "cta": "...",
    "visual_suggestion": "...."    
  }],
  "angle_library":[
    "...",
    "...",
    "...",
    "...", 
    ... # 10 angles
  ],
  "hook_library":[
    "...",
    "...",
    "...",
    "...",
    # 20 hooks
  ],
  "landing_page": {
    "section_1_hero": {
      "name":"Hero - Reframing + Output",
      "headline": "Tenang Saat Audit Bukan Kebetulan",
      "subheadline": "Bukan auditor yang bikin stres, tapi sistem aset yang tidak siap diperiksa kapan saja.",
      "primary_cta": "Minta Demo Sistem"
    },
    "section_2_proof": {
      "name":"PROOF OF REALITY — Bikin “ini beneran”",
      "title": "Kenapa Audit Selalu Terasa Berat?",
      "points": [
        "Data aset tersebar di banyak unit",
        "Pencatatan manual rawan selisih",
        "Histori aset sulit ditelusuri saat diminta auditor"
      ]
    },
    "section_3_problem": {
      "name":"PROBLEM CALLOUT — Mirror Moment",
      "title": "Masalah Utamanya Ada di Sistem",
      "description": "Selama aset tidak dikelola dalam satu sumber data yang konsisten, audit akan selalu jadi momok. Bukan karena tim tidak kompeten, tapi karena sistemnya tidak mendukung kesiapan audit."
    },
    "section_4_solution": {
      "name":"SOLUTION — Reframe + Path",
      "title": "Satu Platform EAM yang Siap Audit",
      "description": "Semua data aset, histori, nilai buku, dan pergerakan tercatat otomatis dalam satu sistem terpusat yang mudah diperiksa kapan saja."
    },
    "section_5_value_stack": {
      "name":"VALUE STACK — Bikin “worth it”",
      "title": "Apa yang Anda Dapatkan",
      "values": [
        "Satu sumber data aset yang akurat",
        "Jejak audit dan histori aset lengkap",
        "Pelacakan aset real-time lintas lokasi",
        "Depresiasi dan nilai buku otomatis"
      ]
    },
    "section_6_objection_handling": {
      "name":"OBJECTION HANDLING — Turunin Risk",
      "title": "Takut Implementasi Ribet?",
      "description": "Sistem dirancang fleksibel, bisa cloud atau on-premise, dan terintegrasi dengan ERP yang sudah ada tanpa mengganggu operasional berjalan."
    },
    "section_7_super_benefit": {
      "name":"SUPER BENEFIT — Emotional Payoff",
      "title": "Manfaat Terbesarnya: Rasa Aman",
      "description": "Audit datang mendadak tidak lagi jadi sumber kecemasan. Data sudah rapi, tim lebih percaya diri, dan reputasi institusi tetap terjaga."
    },
    "section_8_final_cta": {
      "name":"FINAL CTA — Calm Conversion",
      "headline": "Siapkan Sistem Aset Anda Sebelum Audit Berikutnya",
      "cta": "Jadwalkan Demo Sekarang"
    }
  },
  "video_script":{
    "length":"30-45s",
    "scripts":[
      {
        "name":"hook (stop scroll)",
        "duration":"0-3s",
        "visuals":["...","..."],
        "text_overlay":"...",
        "voice_over":"..."
      },
      {
        "name":"problem mapping",
        "duration":"4-10s",
        "visuals":["...","..."],
        "text_overlay":"...",
        "voice_over":"..."
      },
      {
        "name":"insight shift",
        "duration":"11-18s",
        "visuals":["...","..."],
        "text_overlay":"...",
        "voice_over":"..."
      },{
        "name":"solution",
        "duration":"11-18s",
        "visuals":["...","..."],
        "text_overlay":"...",
        "voice_over":"..."
      },{
        "name":"kill effort + proof",
        "duration":"28-34s",
        "visuals":["...","..."],
        "text_overlay":"...",
        "voice_over":"..."
      },{
        "name":"reset failure",
        "duration":"35-41s",
        "visuals":["...","..."],
        "text_overlay":"...",
        "voice_over":"..."
      },{
        "name":"cta (soft, meta-safe)",
        "duration":"42-45s",
        "visuals":["...","..."],
        "text_overlay":"...",
        "voice_over":"..."
      },
    ]
  },
  "catatan_produksi":[
    "format: 9:16",
    "subtitle wajib",
    "hook teks muncul <2 detik"
  ]
}
```
"""

class ads_copy(models.Model):
    _name = "vit.ads_copy"
    _inherit = "vit.ads_copy"


    @api.depends("output_html")
    def _get_output_html_trimmed(self):
        for rec in self:
            output_html = rec.output_html or ""
            marker = "<h3>Landing Page</h3>"
            idx = output_html.find(marker)
            trimmed = output_html[:idx] if idx != -1 else output_html
            rec.output_html_trimmed = trimmed
    output_html_trimmed = fields.Text('Trimmed Output HTML', compute="_get_output_html_trimmed")

    def action_generate(self, ):

        if not self.gpt_prompt_id:
            raise UserError('Ads Copy GPT empty')
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

    lang_id = fields.Many2one(comodel_name="res.lang",    related="angle_hook_id.product_value_analysis_id.lang_id")
    partner_id = fields.Many2one(comodel_name="res.partner", related="angle_hook_id.product_value_analysis_id.partner_id")
    
    def _get_default_prompt(self):
        
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_algo_copy", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "algo_copy")], limit=1
        ).id
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    
    @api.onchange("hook_id")
    def _get_input(self, ):
        """

        """
        for rec in self:
            hook = rec.hook_id.hook_no
            rec.hook_no = hook
            rec.name = f"AP {rec.audience_profiler_id.audience_profile_no} - ANGLE {rec.hook_id.angle_no} - HOOK {hook} "
            rec.input = f"""

# HOOK:
---
Langsung buat Ads copy nya, focus pada hook ini dulu: 
{rec.hook_id.output}.

Setelah itu langsung buat LP 8 section.

Lalu buat video script nya.

# ANGLE dan HOOK lengkap:
---
{rec.angle_hook_id.output}

# AUDIENCE PROFILE:
---
{rec.audience_profiler_id.output}

# PRODUCT VALUE:
---
{rec.product_value_analysis_id.output}

# INSTRUCTIONS:
---
{rec.general_instruction}

{rec.specific_instruction or ''}

Response in {self.lang_id.name} language.
"""

    # def action_create_images(self):
    #     def extract_copywriting_variants(text: str):
    #         """
    #         Extract paragraphs under '=== COPYWRITING VARIASI ==='
    #         starting with 1., 2., 3. and return them as a list.
    #         """

    #         # Step 1: isolate section COPYWRITING VARIASI
    #         section_match = re.search(
    #             r"=== COPYWRITING VARIASI ===(.*?)(?:Optional_|$)",
    #             text,
    #             flags=re.S
    #         )

    #         if not section_match:
    #             return []

    #         section_text = section_match.group(1)

    #         # Step 2: split by numbered items (1., 2., 3.)
    #         variants = re.findall(
    #             r"\n\s*\d+\.\s*(.*?)(?=\n\s*\d+\.|\Z)",
    #             section_text,
    #             flags=re.S
    #         )

    #         # Step 3: clean whitespace
    #         return [v.strip() for v in variants]
        
    #     images = extract_copywriting_variants(self.output)
    #     self.image_generator_ids = [(0,0,{
    #         'ads_copy_id': self.id,
    #         'name':'/',
    #         'description': x
    #     }) for x in images]

    #     self.image_generator_ids._get_input()


#     def action_split_images_md(self):
#         def extract_copies(text: str) -> List[Dict]:
#             copies = []
#             clean_text = strip_emoji(text)

#             # Match ANY "### ... Copy ... — ..." (emoji & letter agnostic)
#             copy_pattern = re.compile(
#                 r"(###\s+.*?\bcopy\b.*?—[^\n]+)\n\n(.*?)(?=\n\n---|\n\n###|\Z)",
#                 re.DOTALL | re.IGNORECASE
#             )

#             for idx, match in enumerate(copy_pattern.finditer(clean_text)):
#                 copy_header = match.group(1).strip()
#                 copy_block = match.group(2).strip()

#                 # Primary Text
#                 primary_text_match = re.search(
#                     r"\*\*\s*primary\s+text.*?\*\*:?[\s\n]+(.*?)(?=\n\n\*\*\s*headline|\Z)",
#                     copy_block,
#                     re.DOTALL | re.IGNORECASE
#                 )

#                 # Headline
#                 headline_match = re.search(
#                     r"\*\*\s*headline.*?\*\*:?[\s\n]+(.*?)(?=\n\n\*\*\s*cta|\Z)",
#                     copy_block,
#                     re.DOTALL | re.IGNORECASE
#                 )

#                 # CTA
#                 cta_match = re.search(
#                     r"\*\*\s*cta\s*:\*\*\s*(.*)",
#                     copy_block,
#                     re.IGNORECASE
#                 )

#                 copies.append({
#                     "index": idx,                      # 0,1,2,3
#                     "copy": copy_header,               # FULL header line
#                     "primary_text": primary_text_match.group(1).strip() if primary_text_match else "",
#                     "headline": headline_match.group(1).strip() if headline_match else "",
#                     "cta": cta_match.group(1).strip() if cta_match else ""
#                 })

#             return copies

#         extracted_copies = extract_copies(self.output)
#         from pprint import pprint
#         pprint(extracted_copies)
#         self.image_generator_ids = [(0,0,{
#             'name': f'Ads Image {i+1}',
#             'description': cop['headline'],
#             'hook_id': self.hook_id.id,
#             'output': f"""## Create PNG image, ratio 1:1.

# {cop['copy']}

# ## Headline:
# {cop['headline']}

# ## Primary_text:
# {cop['primary_text']}

# ## CTA:
# {cop['cta']}

# """
#         }) for i,cop in enumerate(extracted_copies)]


#     def action_create_lp_md(self):

#         def capture_landing_page(text: str) -> Dict:
#             result: Dict = {
#                 "page_title": "",
#                 "sections": []
#             }

#             clean_text = strip_emoji(text)

#             # ---- page title (flexible): first H1 that contains "LANDING PAGE"
#             for line in clean_text.splitlines():
#                 if re.match(r"^\s*#\s+.*landing\s+page", line, flags=re.IGNORECASE):
#                     result["page_title"] = re.sub(r"^\s*#\s+", "", line).strip()
#                     break

#             # ---- find section headings (## ...)
#             lines = clean_text.splitlines()
#             header_idx: List[int] = []
#             header_info: List[Dict] = []

#             heading_re = re.compile(r"^\s*##\s+(.*)$")

#             for i, line in enumerate(lines):
#                 m = heading_re.match(line)
#                 if not m:
#                     continue

#                 heading_text = m.group(1).strip()

#                 # Extract section number anywhere in heading (handles: "1", "1.", "1 HERO", "1️⃣ HERO")
#                 num_match = re.search(r"\b(\d{1,2})\b", heading_text)
#                 if not num_match:
#                     continue

#                 section_no = int(num_match.group(1))

#                 # Title = heading text with the number removed + cleanup
#                 title = heading_text
#                 title = re.sub(r"\b\d{1,2}\b", "", title, count=1).strip()
#                 title = re.sub(r"^[\.\-\)\s]+", "", title).strip()  # remove leading ".-)" etc

#                 header_idx.append(i)
#                 header_info.append({"section_no": section_no, "section_title": title})

#             # ---- slice content between headings
#             for j, start_i in enumerate(header_idx):
#                 end_i = header_idx[j + 1] if j + 1 < len(header_idx) else len(lines)

#                 content_lines = lines[start_i + 1:end_i]
#                 content = "\n".join(content_lines).strip()

#                 result["sections"].append({
#                     "section_no": header_info[j]["section_no"],
#                     "section_title": header_info[j]["section_title"],
#                     "content": content
#                 })

#             # Optional: sort by section_no (keeps order even if headings shuffled)
#             result["sections"].sort(key=lambda x: x["section_no"])

#             return result



#         landing_page = capture_landing_page(self.output)



#         output = f"""# {landing_page['page_title']}
# ---
# """
#         for section in landing_page['sections']:
#             output += f"### SECTION {section['section_no']}\n\n"
#             output += f"### {section['section_title']}\n\n"
#             output += f"{section['content']}\n"
        
#         self.landing_page_builder_ids = [(0,0,{
#             'name': 'LP 1',
#             'output': output
#         })]

    def action_split_images(self):
        def grep_copy_type(text: str):
            """
            Detect COPY type (A, B, C, or D) from text.
            Returns 'A', 'B', 'C', 'D', or None if not found.
            """
            match = re.search(r'\bCOPY\s*([ABCD])\b', text, re.IGNORECASE)
            return match.group(1).upper() if match else None
        
        if not self.output:
              raise UserError('Output empty: please regenerate output')
        
        js = json.loads(self.clean_md(self.output))
        if 'ads_copy' not in js:
            raise UserError('ads_copy key not found. regenerate output')
        
        for i,ad in enumerate(js['ads_copy']):
            img=self.env['vit.image_generator'].create({
                'ads_copy_id': self.id, 
                'name': f'Ads Image {i+1}: {ad['name']}',
                'description': ad['headline'],
                'hook_id': self.hook_id.id,
                'ads_copy_no': grep_copy_type(ad['name']),
                'gpt_model_id': self.gpt_model_id.id
            })
            output={
                'instruction':img.specific_instruction,
                'headline':ad['headline'],
                'primary_text':ad['primary_text'],
                'cta':ad['cta'],
                'visual_suggestion':ad['visual_suggestion'],
                'angle_library': js['angle_library'],
                'hook_library': js['hook_library']
            }
            img.output = json.dumps(output, indent=3)
            img.generate_output_html()

    def action_create_lp(self):
        js = json.loads(self.clean_md(self.output))
        if 'landing_page' not in js:
            raise UserError('landing_page key not found. regenerate output')

        output = js['landing_page']
        output.update({'angle_library': js['angle_library']})
        output.update({'hook_library': js['hook_library']})

        self.landing_page_builder_ids = [(0,0,{
            'name': 'LP 1',
            'output': self.wrap_md(output),
            'gpt_model_id': self.gpt_model_id.id
        })]

        for lp in self.landing_page_builder_ids:
            lp.generate_output_html()

    def action_create_video(self):
        js = json.loads(self.clean_md(self.output))
        if 'video_script' not in js:
            raise UserError('video_script key not found. regenerate output')
        
        output=js['video_script']

        video_script_ids = []

        for x in output['scripts']:
          script = "Visuals: " + ",".join(x['visuals']) + "\nText Overlay: " + x['text_overlay'] + "\nVoice Over: " +x['voice_over'] 
          video_script_ids.append((0,0,{
                'name': x['name'],
                'duration': x['duration'],
                'script': script,
                'prompt': '' ,
            }))
          
        self.video_director_ids = [(0,0,{
            'name': 'VIDEO DIRECTOR 1',
            'output': self.wrap_md(output),
            'video_script_ids': video_script_ids,
            'gpt_model_id': self.gpt_model_id.id
        })]
  
        for vid in self.video_director_ids:
            vid.generate_output_html()  

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