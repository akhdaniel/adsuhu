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
  "main_target_segment": "Pasangan Muda Perkotaan (Active Urban Couples), usia 20-35 tahun, berpenghasilan menengah ke atas, tinggal di kota besar, dengan gaya hidup aktif dan dinamis.",
  "customer_empathy_profile": {
    "think_and_feel": [
      "Kami ingin produk yang praktis untuk aktivitas kami berdua, tidak mau repot beli terpisah.",
      "Sedang mencari cara untuk mengekspresikan kebersamaan kami lewat gaya, tapi yang tidak norak.",
      "Khawatir kalau beli online, ukurannya tidak pas untuk kami berdua dan proses retur ribet.",
      "Merasa lelah kalau harus berdiri lama atau jalan-jalan keliling mall, butuh alas kaki yang benar-benar nyaman.",
      "Ingin investasi di produk yang tahan lama, tidak cepat rusak sehingga hemat dalam jangka panjang.",
      "Pikirkan, <em>apakah sandal ini cukup stylish untuk dipakai nongkrong di kafe, tapi juga aman untuk jalan di trotoar basah?</em>",
      "Merasa senang dan bangga ketika bisa tampil matching dengan pasangan di foto-foto media sosial.",
      "Takut salah pilih dan akhirnya produknya menganggur di lemari, uang terbuang percuma."
    ],
    "look": [
      "Feed Instagram dan TikTok yang dipenuhi pasangan lain dengan gaya matching outfit.",
      "Teman-teman sepergaulan yang selalu update dengan produk lifestyle terbaru.",
      "Banyak pilihan sandal di e-commerce, tapi bingung memilih yang benar-benar berkualitas.",
      "Kondisi jalanan kota yang tidak rata, basah, atau licin saat musim hujan.",
      "Pasangan mereka sendiri yang mungkin mengeluh kaki lelah setelah seharian beraktivitas.",
      "Review produk di YouTube yang menunjukkan uji ketahanan dan kenyamanan.",
      "Iklan-iklan flash sale yang menawarkan diskon besar, tapi membuat ragu soal kualitas."
    ],
    "listen": [
      "<em>Kita cari yang bisa dipakai buat banyak acara, biar gak bolak-balik ganti sandal</em> - dari pasangan.",
      "<em>Produk couple itu biasanya harganya lebih mahal, worth it gak sih?</em> - dari teman atau forum online.",
      "<em>Cari yang bahannya empuk dan ringan, biar gak bikin kaki capek</em> - rekomendasi dari influencer lifestyle.",
      "<em>Baca dulu review-nya, jangan langsung beli</em> - saran umum di komunitas belanja online.",
      "<em>Sandal yang bagus itu yang anti slip, apalagi kalo lagi hujan</em> - pengalaman dari pecinta outdoor.",
      "<em>Ini lucu banget pasangannya, cocok buat kalian</em> - komentar di media sosial.",
      "<em>Harga segitu dapet dua? Lumayan juga</em> - pertimbangan rasional tentang value for money."
    ],
    "say_and_do": [
      "<em>Kita cari sandal yang nyaman buat jalan-jalan sekaligus gaya ya</em> - berdiskusi dengan pasangan.",
      "Membuka Tokopedia/Shopee dan langsung mencari filter <em>pasangan</em> atau <em>couple</em> di kategori alas kaki.",
      "Menonton video review lengkap, terutama yang menampilkan pasangan sebagai pengguna.",
      "Membandingkan harga, kebijakan retur, dan panduan ukuran di beberapa toko online sebelum checkout.",
      "Mengunggah foto atau story saat memakai produk matching, men-tag brand-nya.",
      "Bertanya di kolom komentar atau live chat penjual: <em>Ini ukurannya sama kayak brand X gak?</em>",
      "Menunggu momen diskon seperti flash sale atau hari belanja online nasional untuk membeli.",
      "Merekomendasikan produk ke pasangan lain jika merasa puas."
    ],
    "pain_points": [
      "Kesulitan menemukan sandal couple yang benar-benar nyaman untuk kedua pasangan, karena bentuk kaki berbeda.",
      "Frustasi dengan sandal yang cepat aus atau rusak, padahal harganya tidak murah.",
      "Takut terpeleset saat musim hujan atau berjalan di permukaan licin.",
      "Proses retur yang rumit dan memakan waktu jika ukuran tidak pas.",
      "Merasa tidak percaya diri karena penampilan kurang matching atau produk terlihat murahan.",
      "Harus membeli dua pasang sandal terpisah dengan desain yang cocok, yang memakan waktu dan biaya lebih.",
      "Sandal yang nyaman biasanya kurang stylish, sedangkan yang stylish seringkali tidak nyaman untuk dipakai lama."
    ],
    "aspirations_and_goals": [
      "Memiliki gaya hidup yang praktis dan efisien bersama pasangan.",
      "Tampil kompak dan menarik di setiap momen bersama, baik offline maupun di media sosial.",
      "Berinvestasi pada produk berkualitas yang tahan lama dan multifungsi.",
      "Meningkatkan kenyamanan dalam aktivitas sehari-hari dan rekreasi.",
      "Dikenal sebagai pasangan yang stylish dan update dengan tren oleh lingkaran pertemanan.",
      "Menghemat waktu dan tenaga dalam berbelanja kebutuhan lifestyle.",
      "Merasa aman dan nyaman dalam berbagai kondisi, dari jalan kota hingga destinasi wisata alam ringan."
    ],
    "barriers_and_objections": [
      "<em>Harganya lebih mahal dibanding beli sandal biasa satuan</em> - kekhawatiran budget.",
      "<em>Jangan-jangan cuma tren sesaat, nanti cepat bosan</em> - keraguan akan nilai jangka panjang.",
      "<em>Kalau salah ukuran, repot ngurus returnya</em> - ketakutan akan risiko belanja online.",
      "<em>Bahan EVA itu tahan lama gak sih? Atau cuma empuk di awal?</em> - keraguan terhadap kualitas material.",
      "<em>Desainnya terlalu mencolok, nggak bisa dipakai untuk acara formal-informal</em> - kekhawatiran tentang fleksibilitas.",
      "<em>Mending beli sepatu sneaker yang lebih terjamin kualitasnya</em> - perbandingan dengan kategori produk lain.",
      "<em>Brand-nya baru, belum banyak yang review</em> - keengganan menjadi early adopter."
    ]
  },
  "communication_tone_and_language": {
    "key_phrases_and_expressions": [
      "Nyaman dipakai seharian",
      "Bahan empuk dan ringan",
      "Anti slip untuk keamanan",
      "Desain matching couple",
      "Tahan lama dan awet",
      "Multifungsi: dari casual ke outdoor",
      "Harga bersaing untuk kualitas premium",
      "Gampang perawatannya",
      "Cocok untuk berbagai aktivitas",
      "Investasi yang worth it"
    ],
    "speaking_style": "Praktis, informatif, dan relatable. Menggunakan bahasa sehari-hari yang mudah dipahami anak muda perkotaan, namun tetap menyampaikan keunggulan produk dengan data dan fakta (contoh: ketebalan sol, jenis material). Hindasi jargon teknis yang berlebihan. Tone-nya bersahabat, seolah merekomendasikan ke teman, bukan menjual dengan keras."
  },
  "emotion_triggers": [
    {
      "emotion": "Kebahagiaan dan Kebersamaan",
      "situation_example": "Mendapatkan banyak likes dan komentar positif saat mengunggah foto bersama pasangan dengan sandal matching di media sosial."
    },
    {
      "emotion": "Kepercayaan Diri",
      "situation_example": "Merasa tampil kompak dan stylish saat jalan-jalan di mall atau nongkrong di kafe favorit, tanpa khawatir sandal tidak nyaman."
    },
    {
      "emotion": "Kenyamanan dan Kelegaan",
      "situation_example": "Setelah seharian berjalan di acara piknik atau city tour, kaki tidak terasa pegal atau lelah berkat sandal yang empuk."
    },
    {
      "emotion": "Rasa Aman",
      "situation_example": "Berjalan dengan percaya diri di trotoar yang basah atau licin setelah hujan, tanpa takut terpeleset."
    },
    {
      "emotion": "Kepuasan dan Kebanggaan",
      "situation_example": "Setelah menggunakan sandal selama berbulan-bulan, kondisi masih bagus dan nyaman, merasa pembeliannya adalah keputusan yang tepat."
    },
    {
      "emotion": "Kegelisahan dan Ketakutan",
      "situation_example": "Hampir terpeleset di lantai basah mall karena memakai sandal lama yang solnya sudah aus, langsung berpikir butuh pengganti yang lebih aman."
    }
  ]
}
"""
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

        if SIMULATE:
            self.output = SIMULATE_OUTPUT
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
