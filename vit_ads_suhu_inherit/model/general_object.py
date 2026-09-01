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
DEFAULT_GENERAL_INSTRUCTION="""CRITICAL JSON FORMATTING RULES — follow these exactly, no exceptions:

1. Respond with ONLY valid, parseable JSON. No markdown, no code fences, no explanations.
2. Use ONLY plain ASCII characters. No Unicode, no smart quotes ("" ''), no em-dashes.
3. All JSON keys and string values must be wrapped in standard double quotes: "key": "value".
4. NEVER put unescaped double quotes inside a string value. This breaks JSON parsing.
   WRONG: {"note": "He said "hello""}        <- INVALID JSON, unescaped inner quotes
   RIGHT: {"note": "He said hello"}           <- remove the inner quotes entirely
   RIGHT: {"note": "He said <em>hello</em>"}  <- replace inner quotes with <em></em> tags
5. If a string value needs emphasis or quoting, use HTML tags instead of quote marks:
   - Emphasis: <em>text</em> or <strong>text</strong>
   - Quoted terms: write them plainly, or wrap in <em></em>
   - Never use single or double quote marks around words inside a JSON string value.
6. No trailing commas. No single quotes anywhere. No comments.
7. If you cannot comply and produce valid JSON, return an empty object: {}
8. You are free to add as many list elements as needed — quality and completeness matter more than brevity."""

class general_object(models.Model):
    """
    {
    "sequence": 0
    }
    """

    _name = "vit.general_object"
    _inherit = "vit.general_object"

    @api.model
    def _fix_stale_failed_statuses(self):
        """One-time cleanup: reset 'failed' records that actually have content
        and no real error message. Called via shell or post-migration."""
        fixed = 0
        for model_name in (
            "vit.product_value_analysis",
            "vit.market_mapper",
            "vit.audience_profiler",
            "vit.angle_hook",
            "vit.hook",
            "vit.ads_copy",
            "vit.image_generator",
            "vit.video_director",
            "vit.landing_page_builder",
        ):
            recs = self.env[model_name].sudo().search([
                ("status", "=", "failed"),
                ("output_html", "!=", False),
                ("output_html", "!=", ""),
                "|",
                ("error_message", "=", False),
                ("error_message", "=", ""),
            ])
            if recs:
                recs.write({"status": "done"})
                _logger.info("_fix_stale_failed_statuses: reset %d %s records", len(recs), model_name)
                fixed += len(recs)
        return fixed
    
    status = fields.Selection(
        [
            ("idle", "Idle"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        string=("Status"),
        default="idle",
        copy=False,
    )
    error_message = fields.Text(string=("Error Message"), copy=False)
    general_instruction = fields.Text(default=DEFAULT_GENERAL_INSTRUCTION,  string=("General Instruction"))

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
        return self.fix_json("".join(translated))

    def fix_json(self, text):
        """
        Best-effort cleanup for common JSON errors (e.g. stray backslashes).
        Example: "\\Ini ..." -> "Ini ..."
        """
        text = text or ""
        # Normalize smart quotes to ASCII quotes.
        text = text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
        # Escape inner quotes inside string values when they don't close the string.
        text = self._escape_inner_quotes(text)
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

    def _escape_inner_quotes(self, text):
        result = []
        in_string = False
        escape = False
        string_is_key = False
        i = 0
        length = len(text)

        def last_sig_char(out):
            for ch in reversed(out):
                if not ch.isspace():
                    return ch
            return ""

        while i < length:
            ch = text[i]
            if escape:
                result.append(ch)
                escape = False
                i += 1
                continue
            if ch == "\\":
                result.append(ch)
                escape = True
                i += 1
                continue
            if ch == '"':
                if not in_string:
                    in_string = True
                    prev_sig = last_sig_char(result)
                    string_is_key = prev_sig in ["{", ","]
                    result.append(ch)
                    i += 1
                    continue
                # We're inside a string; decide if this should close or be escaped.
                j = i + 1
                while j < length and text[j].isspace():
                    j += 1
                if string_is_key:
                    should_close = j >= length or text[j] in [",", "}", "]", ":"]
                else:
                    should_close = j >= length or text[j] in [",", "}", "]"]
                if should_close:
                    in_string = False
                    result.append(ch)
                else:
                    result.append('\\"')
                i += 1
                continue
            result.append(ch)
            i += 1
        return "".join(result)
    
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
