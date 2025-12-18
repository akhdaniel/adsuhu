#!/usr/bin/python
#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import html
import json
import logging
import re
import requests

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - optional dependency
    BeautifulSoup = None

try:
    import html2text as html2text_lib
except Exception:  # pragma: no cover - optional dependency
    html2text_lib = None

_logger = logging.getLogger(__name__)

class product_value_analysis(models.Model):
    _name = "vit.product_value_analysis"
    _inherit = "vit.product_value_analysis"

    def _get_default_prompt(self):
        prompt = self.env.ref("vit_ads_suhu_inherit.gpt_product_value_analysis", raise_if_not_found=False)
        if prompt:
            return prompt.id
        return self.env["vit.gpt_prompt"].search(
            [("name", "=", "product_value_analysis")], limit=1
        ).id

    gpt_prompt_id = fields.Many2one(comodel_name="vit.gpt_prompt",  string=_("Gpt Prompt"), default=_get_default_prompt)

    @api.onchange("description","features")
    def _get_input(self, ):
        """
        {
        }
        """
        for rec in self:
            rec.input = f"""

# ✅ DESCRIPTION:
================
{rec.description}

# PRODUCT FEATURES:
================
{rec.features}



"""


    def action_fetch_product_description(self, ):
        for record in self:
            if not record.product_url:
                raise UserError(_("Please provide a product URL before fetching the description."))

            html_content = record._get_product_content(record.product_url)
            cleaned_html = record._clean_html_content(html_content)
            markdown_content = record._html_to_markdown(cleaned_html)
            record.description = markdown_content or cleaned_html or ""

        return True


    def action_generate(self, ):
        pass

    def _get_product_content(self, url):
        if "shopee." in url:
            shopee_content = self._fetch_shopee_product_content(url)
            if shopee_content:
                return shopee_content
        return self._fetch_product_page(url)

    def _fetch_product_page(self, url):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            _logger.exception("Failed to download product page %s", url)
            raise UserError(
                _("Unable to fetch the product page.\n\n%(error)s") % {"error": str(exc)}
            )

    def _clean_html_content(self, html_text):
        if not html_text or not BeautifulSoup:
            return html_text
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        body = soup.body or soup
        return body.prettify()

    def _html_to_markdown(self, html_text):
        if not html_text:
            return ""
        if html2text_lib:
            converter = html2text_lib.HTML2Text()
            converter.ignore_links = False
            converter.body_width = 0
            return converter.handle(html_text)
        if BeautifulSoup:
            soup = BeautifulSoup(html_text, "html.parser")
            return soup.get_text("\n", strip=True)
        return html_text

    # Shopee scraper
    def _fetch_shopee_product_content(self, url):
        ids = self._extract_shopee_ids(url)
        if not ids:
            _logger.info("Unable to extract Shopee identifiers from url %s", url)
            return ""
        shop_id, item_id = ids
        product_data = self._call_shopee_api(shop_id, item_id, url)
        if product_data:
            return self._build_shopee_product_html(product_data)

        html_page = self._fetch_product_page(url)
        structured_html = self._extract_shopee_content_from_html(html_page)
        return structured_html or html_page or ""

    def _call_shopee_api(self, shop_id, item_id, referer_url):
        api_url = f"https://shopee.co.id/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": referer_url,
            "X-Requested-With": "XMLHttpRequest",
            "X-API-SOURCE": "pc",
        }
        try:
            response = requests.get(api_url, headers=headers, timeout=20)
            if response.status_code == 403:
                _logger.warning("Shopee API request blocked with 403 for %s", api_url)
                return None
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            _logger.warning("Shopee API request failed: %s", exc)
            return None
        except ValueError:
            _logger.warning("Shopee API returned non JSON response for %s", api_url)
            return None

        item = payload.get("data") or payload.get("item") or {}
        if not item:
            _logger.info("Shopee API returned empty item for url %s", url)
            return None
        return item

    def _build_shopee_product_html(self, item):
        title = item.get("name") or ""
        description = (item.get("description") or "").replace("\r\n", "\n")
        attributes = item.get("attributes") or []
        price = item.get("price") or item.get("price_min") or item.get("price_max") or ""

        html_parts = []
        if title:
            html_parts.append(f"<h1>{html.escape(title)}</h1>")
        if price:
            if isinstance(price, (int, float)):
                price = price / 100000
                price_display = f"Rp {price:,.0f}"
            else:
                price_display = str(price)
            html_parts.append(f"<p><strong>Price:</strong> {html.escape(price_display)}</p>")
        if description:
            paragraphs = "".join(
                f"<p>{html.escape(line)}</p>" for line in description.split("\n") if line.strip()
            )
            html_parts.append(paragraphs)
        if attributes:
            html_parts.append("<ul>")
            for attr in attributes:
                name = attr.get("name") or attr.get("attribute_name") or ""
                value_list = attr.get("values") or attr.get("attribute_value") or []
                if isinstance(value_list, list):
                    parsed_values = []
                    for val in value_list:
                        if isinstance(val, dict):
                            parsed_values.append(val.get("name") or val.get("value") or "")
                        else:
                            parsed_values.append(str(val))
                    value = ", ".join(filter(None, parsed_values))
                else:
                    value = value_list or ""
                if name or value:
                    html_parts.append(
                        f"<li><strong>{html.escape(name)}:</strong> {html.escape(str(value))}</li>"
                    )
            html_parts.append("</ul>")
        return "".join(html_parts)

    def _extract_shopee_content_from_html(self, html_text):
        if not html_text:
            return ""
        if not BeautifulSoup:
            return html_text
        soup = BeautifulSoup(html_text, "html.parser")
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for script in scripts:
            raw = script.string
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except ValueError:
                continue
            if isinstance(data, list):
                product_data = next((item for item in data if isinstance(item, dict) and item.get("@type") == "Product"), None)
            elif isinstance(data, dict) and data.get("@type") == "Product":
                product_data = data
            else:
                product_data = None
            if not product_data:
                continue
            title = product_data.get("name") or ""
            description = product_data.get("description") or ""
            offers = product_data.get("offers") or {}
            price = offers.get("price")
            attributes = product_data.get("additionalProperty") or []

            html_parts = []
            if title:
                html_parts.append(f"<h1>{html.escape(title)}</h1>")
            if price:
                html_parts.append(f"<p><strong>Price:</strong> {html.escape(str(price))}</p>")
            if description:
                html_parts.append(f"<div>{description}</div>")
            if attributes:
                html_parts.append("<ul>")
                for prop in attributes:
                    name = prop.get("name")
                    value = prop.get("value")
                    if name or value:
                        html_parts.append(
                            f"<li><strong>{html.escape(str(name or ''))}:</strong> {html.escape(str(value or ''))}</li>"
                        )
                html_parts.append("</ul>")
            if html_parts:
                return "".join(html_parts)
        return ""

    def _extract_shopee_ids(self, url):
        patterns = [
            r"/product/(\d+)/(\d+)",
            r"-i\.(\d+)\.(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        return None
