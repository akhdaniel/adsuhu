#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import re
from typing import List, Dict
import json

def strip_emoji(text: str) -> str:
    # Remove common emoji ranges (optional)
    return re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]", "", text)

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
    "name":"COPY D - AlgoCopy Ultra",
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
  }
}
```
"""
class ads_copy(models.Model):
    _name = "vit.ads_copy"
    _inherit = "vit.ads_copy"

    def action_generate(self, ):
        pass
    specific_instruction = fields.Text( string=_("Specific Instruction"), default=DEFAULT_SPECIFIC_INSTRUCTION)

    lang_id = fields.Many2one(comodel_name="res.lang", related="angle_hook_id.product_value_analysis_id.lang_id")

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_algo_copy", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "algo_copy")], limit=1
        ).id
    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("GPT Prompt"), default=_get_default_prompt)
    
    @api.onchange("audience_profiler_id","angle_hook_id","hook_id")
    def _get_input(self, ):
        """
        {
        @api.depends("audience_profiler_id","angle_hook_id")
        }
        """
        for rec in self:
            hook = len(rec.angle_hook_id.ads_copy_ids)+1
            rec.hook_no = hook
            rec.name = f"AD COPY - ANGLE {rec.angle_hook_id.angle_no} - HOOK {hook}"
            rec.input = f"""

# HOOK:
---
Langsung buat Ads copy nya, focus pada hook ini dulu: 
{rec.hook_id.output}.

Setelah itu langsung buat LP 8 section.

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


    def action_split_images_md(self):
        def extract_copies(text: str) -> List[Dict]:
            copies = []
            clean_text = strip_emoji(text)

            # Match ANY "### ... Copy ... — ..." (emoji & letter agnostic)
            copy_pattern = re.compile(
                r"(###\s+.*?\bcopy\b.*?—[^\n]+)\n\n(.*?)(?=\n\n---|\n\n###|\Z)",
                re.DOTALL | re.IGNORECASE
            )

            for idx, match in enumerate(copy_pattern.finditer(clean_text)):
                copy_header = match.group(1).strip()
                copy_block = match.group(2).strip()

                # Primary Text
                primary_text_match = re.search(
                    r"\*\*\s*primary\s+text.*?\*\*:?[\s\n]+(.*?)(?=\n\n\*\*\s*headline|\Z)",
                    copy_block,
                    re.DOTALL | re.IGNORECASE
                )

                # Headline
                headline_match = re.search(
                    r"\*\*\s*headline.*?\*\*:?[\s\n]+(.*?)(?=\n\n\*\*\s*cta|\Z)",
                    copy_block,
                    re.DOTALL | re.IGNORECASE
                )

                # CTA
                cta_match = re.search(
                    r"\*\*\s*cta\s*:\*\*\s*(.*)",
                    copy_block,
                    re.IGNORECASE
                )

                copies.append({
                    "index": idx,                      # 0,1,2,3
                    "copy": copy_header,               # FULL header line
                    "primary_text": primary_text_match.group(1).strip() if primary_text_match else "",
                    "headline": headline_match.group(1).strip() if headline_match else "",
                    "cta": cta_match.group(1).strip() if cta_match else ""
                })

            return copies

        extracted_copies = extract_copies(self.output)
        from pprint import pprint
        pprint(extracted_copies)
        self.image_generator_ids = [(0,0,{
            'name': f'Ads Image {i+1}',
            'description': cop['headline'],
            'hook_id': self.hook_id.id,
            'output': f"""## Create PNG image, ratio 1:1.

{cop['copy']}

## Headline:
{cop['headline']}

## Primary_text:
{cop['primary_text']}

## CTA:
{cop['cta']}

"""
        }) for i,cop in enumerate(extracted_copies)]


    def action_create_lp_md(self):

        def capture_landing_page(text: str) -> Dict:
            result: Dict = {
                "page_title": "",
                "sections": []
            }

            clean_text = strip_emoji(text)

            # ---- page title (flexible): first H1 that contains "LANDING PAGE"
            for line in clean_text.splitlines():
                if re.match(r"^\s*#\s+.*landing\s+page", line, flags=re.IGNORECASE):
                    result["page_title"] = re.sub(r"^\s*#\s+", "", line).strip()
                    break

            # ---- find section headings (## ...)
            lines = clean_text.splitlines()
            header_idx: List[int] = []
            header_info: List[Dict] = []

            heading_re = re.compile(r"^\s*##\s+(.*)$")

            for i, line in enumerate(lines):
                m = heading_re.match(line)
                if not m:
                    continue

                heading_text = m.group(1).strip()

                # Extract section number anywhere in heading (handles: "1", "1.", "1 HERO", "1️⃣ HERO")
                num_match = re.search(r"\b(\d{1,2})\b", heading_text)
                if not num_match:
                    continue

                section_no = int(num_match.group(1))

                # Title = heading text with the number removed + cleanup
                title = heading_text
                title = re.sub(r"\b\d{1,2}\b", "", title, count=1).strip()
                title = re.sub(r"^[\.\-\)\s]+", "", title).strip()  # remove leading ".-)" etc

                header_idx.append(i)
                header_info.append({"section_no": section_no, "section_title": title})

            # ---- slice content between headings
            for j, start_i in enumerate(header_idx):
                end_i = header_idx[j + 1] if j + 1 < len(header_idx) else len(lines)

                content_lines = lines[start_i + 1:end_i]
                content = "\n".join(content_lines).strip()

                result["sections"].append({
                    "section_no": header_info[j]["section_no"],
                    "section_title": header_info[j]["section_title"],
                    "content": content
                })

            # Optional: sort by section_no (keeps order even if headings shuffled)
            result["sections"].sort(key=lambda x: x["section_no"])

            return result



        landing_page = capture_landing_page(self.output)



        output = f"""# {landing_page['page_title']}
---
"""
        for section in landing_page['sections']:
            output += f"### SECTION {section['section_no']}\n\n"
            output += f"### {section['section_title']}\n\n"
            output += f"{section['content']}\n"
        
        self.landing_page_builder_ids = [(0,0,{
            'name': 'LP 1',
            'output': output
        })]

    def action_split_images(self):
        js = json.loads(self.clean_md(self.output))
        print(js)

    def action_create_lp(self):
        js = json.loads(self.clean_md(self.output))
        print(js)
