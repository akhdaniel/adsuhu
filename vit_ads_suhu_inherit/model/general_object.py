#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import re
import unicodedata
import markdown

import logging
_logger = logging.getLogger(__name__)

UNICODE_ASCII_MAP = {
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2015": "-",  # horizontal bar
    "\u2212": "-",  # minus sign
    "\u2010": "-",  # hyphen
    "\u2011": "-",  # non-breaking hyphen
    "\u00a0": " ",  # non-breaking space
    "\u200b": "",   # zero width space
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u2026": "...",  # ellipsis
}
DEFAULT_GENERAL_INSTRUCTION="""You MUST respond with ONLY valid JSON with no errors.
ONLY plain ASCII, No Unicode characters.
Do NOT include explanations or extra text.
If you cannot comply, return an empty JSON object {}.
You a free to add list element in the json list as many as needed.
Ensure all strings are properly double-quoted and all keys are quoted.
Do not use trailing commas or single quotes.
DO NOT quote text inside any JSON values, use <em></em> tags instead if you return quoted texts, 
e.g. {"key","the value text <em>the bold text</em>, normal text"}
"""
class general_object(models.Model):
    """
    {
    "sequence": 0
    }
    """

    _name = "vit.general_object"
    _inherit = "vit.general_object"
    
    status = fields.Selection(
        [
            ("idle", "Idle"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        string=_("Status"),
        default="idle",
        copy=False,
    )
    general_instruction = fields.Text(default=DEFAULT_GENERAL_INSTRUCTION,  string=_("General Instruction"))

    def clean_md(self, text):
        text = text or ""
        text = text.replace("```json","").replace("```","")
        # Convert escaped unicode sequences like "\\u2013" into real characters
        text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
        # Normalize to ASCII by decomposing unicode characters and mapping common symbols
        normalized = unicodedata.normalize("NFKD", text)
        translated = []
        for ch in normalized:
            if ord(ch) < 128:
                translated.append(ch)
                continue
            replacement = UNICODE_ASCII_MAP.get(ch, "")
            translated.append(replacement)
        return "".join(translated)

    def fix_json(self, text):
        """
        Best-effort cleanup for common JSON errors (e.g. stray backslashes).
        Example: "\\Ini ..." -> "Ini ..."
        """
        text = text or ""
        # Normalize smart quotes to ASCII quotes.
        text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
        # Remove backslashes that are not valid JSON escapes.
        text = re.sub(r'\\(?!["\\/bfnrtu])', "", text)
        # If invalid \u sequences exist, strip the backslash so JSON parsing can proceed.
        text = re.sub(r'\\u(?![0-9a-fA-F]{4})', "u", text)
        # Remove trailing commas before } or ]
        text = re.sub(r",\s*([}\]])", r"\1", text)
        # Quote unquoted object keys: { key: "value" } -> { "key": "value" }
        text = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', text)
        # Convert single-quoted keys/values to double-quoted (simple cases only).
        text = re.sub(r"\'([^\']*)\'", r'"\1"', text)
        return text
    
    def wrap_md(self, text):
        return json.dumps(text, indent=3) 
    
    def reformat_output(self, ):
        outputs = []
        for rec in self:
            if not rec.output:
                outputs.append("")
                continue
            cleaned = rec.clean_md(rec.output)
            try:
                parsed = json.loads(cleaned)
                formatted = json.dumps(parsed, indent=3)
            except json.JSONDecodeError:
                formatted = cleaned
            rec.output = formatted
            outputs.append(formatted)
        return outputs[0] if len(outputs) == 1 else outputs

    def json_to_markdown(self, data, prefix=1, level=3, max_level=4):
        """
        Convert JSON/dict into Markdown with controlled heading depth.

        Rules:
        - Starting heading level = 3 (###)
        - Maximum heading level = 4 (####)
        - Deeper levels (> max_level):
            **Key**: value
        - Keys converted to Title Case
        - List of primitives -> bullet points (-)
        - List of objects (list of dict) -> Markdown table
        """


        if isinstance(data, str):
            _logger.error(f"isinstance str data={data}")
            data = self.clean_md(data)

        md_lines = []

        def title_case_key(key):
            replacements=[
                ('Dan','dan'),
                ('Dari','dari'),
                ('Ke','ke'),
                ('And','and'),
                ('For','for'),
                ('To','to'),
                ('From','from'),
                ('Cta','CTA'),
                ('cta','CTA'),
                ('Pov','POV'),
                ('pov','POV'),
                ('ab_test','A/B Test'),
                ('Ab Test','A/B Test'),
                ('keyword','Keyword'),
                ('keterbatasan','Keterbatasan'),
                ('kepribadian','Kepribadian'),
                ('key','Key'),
            ]

            res = key.replace("_", " ").title()
            for rep in replacements:
                res = res.replace(rep[0], rep[1])

            return res 

        def is_list_of_dicts(value):
            return (
                isinstance(value, list)
                and value
                and all(isinstance(item, dict) for item in value)
            )

        def render_table(key, value):
            # md_lines.append(f"**{title_case_key(key)}**")
            def format_cell(cell):
                text = "" if cell is None else str(cell)
                # Keep table rows intact by replacing line breaks with <br>.
                return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")

            headers = list(value[0].keys())
            header_row = "| " + " | ".join(title_case_key(h) for h in headers) + " |"
            separator_row = "| " + " | ".join("---" for _ in headers) + " |"

            md_lines.append(header_row)
            md_lines.append(separator_row)

            for row in value:
                row_line = "| " + " | ".join(format_cell(row.get(h, "")) for h in headers) + " |"
                md_lines.append(row_line)

            md_lines.append("\n")

        def render_value(key, value, level):
            # Beyond max heading depth → paragraph format
            if level > max_level:
                if is_list_of_dicts(value):
                    render_table(key, value)
                elif isinstance(value, list):
                    md_lines.append(f"**{title_case_key(key)}**:")
                    for item in value:
                        md_lines.append(f"- {item}")
                else:
                    md_lines.append(f"- **{title_case_key(key)}**: {value}")
                return

            heading_prefix = "#" * level
            md_lines.append(f"{heading_prefix} {title_case_key(key)}")

            j=1
            if isinstance(value, dict):
                for k, v in value.items():
                    render_value(k, v, level + 1)
                    j+=1

            elif is_list_of_dicts(value):
                render_table(key, value)

            elif isinstance(value, list):
                for item in value:
                    md_lines.append(f"- {item}")

            else:
                md_lines.append(str(value))

        i=1
        if isinstance(data, dict):
            for key, value in data.items():
                render_value(key, value, level)
                i+=1

        elif isinstance(data, list):
            for item in data:
                md_lines.append(f"- {item}")

        return "\n".join(md_lines)


    def list_to_bullet(self, lst):
        res=[]
        for l in lst:
            res.append(f"* {l}")
        return "\n".join(res)
    
    # Function to read markdown file and convert it to HTML
    def md_to_html(self, md_content):
        # Replace underscores in /web/image URLs with HTML entities to avoid Markdown emphasis.
        def escape_web_image_underscores(match):
            url = match.group(1)
            return url.replace("_", "&#95;")

        md_content = re.sub(r'(/web/image/[^\s)]+)', escape_web_image_underscores, md_content)
        # Enable tables so Markdown tables render into HTML for downstream DOCX conversion
        html_content = markdown.markdown(md_content, extensions=['tables'])
        # Ensure tables have Bootstrap classes and wrap them to be responsive in the frontend.
        def add_table_classes(match):
            attrs = match.group(1) or ""
            if re.search(r"\bclass\s*=", attrs, flags=re.IGNORECASE):
                attrs = re.sub(
                    r'class\s*=\s*"([^"]*)"',
                    lambda m: f'class="{m.group(1)} table table-striped"',
                    attrs,
                    flags=re.IGNORECASE,
                )
                attrs = re.sub(
                    r"class\s*=\s*'([^']*)'",
                    lambda m: f"class='{m.group(1)} table table-striped'",
                    attrs,
                    flags=re.IGNORECASE,
                )
                return f"<table{attrs}>"
            return f'<table class="table table-striped"{attrs}>'

        html_content = re.sub(
            r"<table\b([^>]*)>",
            add_table_classes,
            html_content,
            flags=re.IGNORECASE,
        )
        html_content = re.sub(
            r'(<table\b[^>]*>.*?</table>)',
            r'<div class="table-responsive">\1</div>',
            html_content,
            flags=re.DOTALL,
        )
        return html_content    
