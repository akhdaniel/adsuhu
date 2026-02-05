# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError
import json
import html
import re
import logging

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

_logger = logging.getLogger(__name__)


class ProductValueAnalysis(models.Model):
    _inherit = "vit.product_value_analysis"

    def action_fetch_product_description(self):
        for rec in self:
            if not rec.product_url:
                raise UserError(_("Please provide a product URL before fetching the description."))
            url = rec.product_url or ""
            url_lower = url.lower()
            if "shopee." in url_lower:
                html_content = rec._fetch_shopee_product_content(url)
            elif "tokopedia." in url_lower:
                html_content = rec._fetch_tokopedia_product_content(url)
            else:
                html_content = rec._fetch_product_page(url)
            cleaned_html = rec._clean_html_content(html_content)
            markdown_content = rec._html_to_markdown(cleaned_html)
            rec.description = markdown_content or cleaned_html or ""

    def _fetch_product_page(self, url):
        try:
            import tls_client
        except Exception:
            raise UserError(
                _("tls-client belum terpasang. Install dulu: pip install tls-client")
            )

        session = tls_client.Session(client_identifier="firefox_120")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            response = session.get(url, headers=headers, timeout_seconds=20, allow_redirects=True)
        except Exception as exc:
            raise UserError(_("Failed to download product page: %s") % (exc,))

        if response.status_code != 200:
            raise UserError(
                _("Unable to fetch the product page. HTTP %s") % (response.status_code,)
            )

        return response.text

    def _get_product_content(self, url):
        if "shopee." in url:
            shopee_content = self._fetch_shopee_product_content(url)
            if shopee_content:
                return shopee_content
        if "tokopedia." in url:
            tokopedia_content = self._fetch_tokopedia_product_content(url)
            if tokopedia_content:
                return tokopedia_content
        return self._fetch_product_page(url)
    
    def _extract_tokopedia_json(self, soup):
        # Preferred: script id="__NEXT_DATA__" containing JSON
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                return json.loads(script.string)
            except Exception:
                pass
        # Fallback: assignment inside script tag
        for script in soup.find_all("script"):
            text = script.string or ""
            if "__NEXT_DATA__" in text and "=" in text:
                try:
                    json_text = text.split("=", 1)[1].strip().rstrip(";")
                    return json.loads(json_text)
                except Exception:
                    return None
        return None

    def _collect_tokopedia_attributes(self, data):
        attributes = []
        seen = set()

        def add_item(key, value):
            if key is None or value is None:
                return
            key = str(key).strip()
            value = str(value).strip()
            if not key or not value:
                return
            pair = (key, value)
            if pair in seen:
                return
            seen.add(pair)
            attributes.append(pair)

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    lk = str(k).lower()
                    if lk in {
                        "attributes",
                        "productattributes",
                        "specification",
                        "specifications",
                        "productdetail",
                        "productdetails",
                        "product_detail",
                        "detail",
                        "productinfo",
                        "product_info",
                    }:
                        if isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict):
                                    name = (
                                        item.get("name")
                                        or item.get("label")
                                        or item.get("title")
                                        or item.get("key")
                                    )
                                    value = (
                                        item.get("value")
                                        or item.get("val")
                                        or item.get("text")
                                        or item.get("desc")
                                    )
                                    if not (name and value) and isinstance(item.get("attribute"), dict):
                                        name = name or item["attribute"].get("name")
                                        value = value or item["attribute"].get("value")
                                    if name and value:
                                        add_item(name, value)
                        elif isinstance(v, dict):
                            for kk, vv in v.items():
                                add_item(kk, vv)
                    walk(v)
            elif isinstance(obj, list):
                for it in obj:
                    walk(it)

        if data:
            walk(data)
        return attributes

    def _fetch_tokopedia_product_content(self, url):
        html_page = self._fetch_product_page(url)
        if not html_page:
            return ""
        
        if not BeautifulSoup:
            return html_page
        
        soup = BeautifulSoup(html_page, "html.parser")
        
        # Extract data from the embedded JSON in script tag
        script_tag = soup.find("script", string=lambda t: t and "window.__cache=" in t if t else False)
        
        title = ""
        price = ""
        details = []
        description = ""
        
        if script_tag:
            try:
                # Extract JSON data from script
                script_content = script_tag.string
                json_start = script_content.find("window.__cache=") + len("window.__cache=")
                json_end = script_content.find(";", json_start)
                json_str = script_content[json_start:json_end]
                data = json.loads(json_str)
                
                # Navigate through the complex JSON structure
                # Find product content data
                for key, value in data.items():
                    if isinstance(value, dict):
                        # Look for product content
                        if value.get("__typename") == "pdpDataProductContent":
                            title = value.get("name", "")
                            price_data = value.get("price", {})
                            if isinstance(price_data, dict):
                                price = price_data.get("priceFmt", "")
                        
                        # Look for product detail
                        if value.get("__typename") == "pdpDataProductDetail":
                            content_list = value.get("content", [])
                            for item in content_list:
                                if isinstance(item, dict):
                                    item_data = data.get(item.get("id"), item)
                                    detail_title = item_data.get("title", "")
                                    detail_subtitle = item_data.get("subtitle", "")
                                    if detail_title and detail_subtitle:
                                        details.append((detail_title, detail_subtitle))
                            
                            # Get description
                            desc_data = value.get("productDetailDescription", {})
                            if isinstance(desc_data, dict):
                                desc_id = desc_data.get("id") if isinstance(desc_data, dict) and "id" in desc_data else None
                                if desc_id:
                                    desc_obj = data.get(desc_id, desc_data)
                                else:
                                    desc_obj = desc_data
                                description = desc_obj.get("content", "")
            
            except Exception as e:
                print(f"Error parsing JSON: {e}")
        
        # Fallback: try meta tags if JSON parsing failed
        if not title:
            def get_meta(name=None, prop=None):
                attrs = {}
                if name:
                    attrs["name"] = name
                if prop:
                    attrs["property"] = prop
                tag = soup.find("meta", attrs=attrs)
                return tag.get("content") if tag else ""
            
            title = get_meta(prop="og:title") or get_meta(name="twitter:title") or ""
            description = (
                get_meta(prop="og:description")
                or get_meta(name="description")
                or get_meta(name="twitter:description")
                or ""
            )
        
        # Build HTML output
        html_parts = []
        
        if title:
            html_parts.append(f"<h1>{html.escape(title)}</h1>")
        
        if price:
            html_parts.append(f"<p><strong>Harga:</strong> {html.escape(str(price))}</p>")
        
        if details:
            html_parts.append("<h3>Detail Produk</h3>")
            html_parts.append("<ul>")
            for key, val in details:
                html_parts.append(
                    f"<li><strong>{html.escape(key)}:</strong> {html.escape(val)}</li>"
                )
            html_parts.append("</ul>")
        
        if description:
            html_parts.append("<h3>Deskripsi</h3>")
            desc_lines = [l.rstrip() for l in description.splitlines()]
            bullets = [l[1:].strip() for l in desc_lines if l.strip().startswith("-")]
            paragraphs = [l for l in desc_lines if l.strip() and not l.strip().startswith("-")]
            
            if paragraphs:
                html_parts.append("<p>" + "<br/>".join(html.escape(p) for p in paragraphs) + "</p>")
            if bullets:
                html_parts.append("<ul>")
                for b in bullets:
                    html_parts.append(f"<li>{html.escape(b)}</li>")
                html_parts.append("</ul>")
        
        return "\n".join(html_parts) if html_parts else html_page

    # Shopee formatter (override)
    # def _build_shopee_product_html(self, item):
    #     title = item.get("name") or ""
    #     description = (item.get("description") or "").replace("\r\n", "\n")
    #     attributes = item.get("attributes") or []
    #     price = item.get("price") or item.get("price_min") or item.get("price_max") or ""

    #     html_parts = []
    #     if title:
    #         html_parts.append(f"<h1>{html.escape(title)}</h1>")
    #     if price:
    #         if isinstance(price, (int, float)):
    #             price = price / 100000
    #             price_display = f"Rp {price:,.0f}"
    #         else:
    #             price_display = str(price)
    #         html_parts.append(f"<p><strong>Price:</strong> {html.escape(price_display)}</p>")

    #     if attributes:
    #         html_parts.append("<h3>Detail Produk</h3>")
    #         html_parts.append("<ul>")
    #         for attr in attributes:
    #             name = attr.get("name") or attr.get("attribute_name") or ""
    #             value_list = attr.get("values") or attr.get("attribute_value") or []
    #             if isinstance(value_list, list):
    #                 value = ", ".join(str(v) for v in value_list if v)
    #             else:
    #                 value = str(value_list or "")
    #             if name and value:
    #                 html_parts.append(
    #                     f"<li><strong>{html.escape(name)}:</strong> {html.escape(value)}</li>"
    #                 )
    #         html_parts.append("</ul>")

    #     if description:
    #         html_parts.append("<h3>Deskripsi Produk</h3>")
    #         lines = [l.strip() for l in description.split("\n") if l.strip()]
    #         paragraphs = []
    #         bullets = []
    #         for line in lines:
    #             if re.match(r"^\\d+[\\).]", line):
    #                 bullets.append(re.sub(r"^\\d+[\\).]\\s*", "", line))
    #             elif line.endswith(":") or line.lower().startswith("pengenalan") or line.lower().startswith("ketentuan") or line.lower().startswith("garansi"):
    #                 # flush pending paragraphs/bullets
    #                 if paragraphs:
    #                     html_parts.append("<p>" + "<br/>".join(html.escape(p) for p in paragraphs) + "</p>")
    #                     paragraphs = []
    #                 if bullets:
    #                     html_parts.append("<ul>")
    #                     for b in bullets:
    #                         html_parts.append(f"<li>{html.escape(b)}</li>")
    #                     html_parts.append("</ul>")
    #                     bullets = []
    #                 html_parts.append(f"<h4>{html.escape(line)}</h4>")
    #             elif line.startswith("-"):
    #                 bullets.append(line[1:].strip())
    #             else:
    #                 paragraphs.append(line)

    #         if paragraphs:
    #             html_parts.append("<p>" + "<br/>".join(html.escape(p) for p in paragraphs) + "</p>")
    #         if bullets:
    #             html_parts.append("<ul>")
    #             for b in bullets:
    #                 html_parts.append(f"<li>{html.escape(b)}</li>")
    #             html_parts.append("</ul>")

    #     return "\n".join(html_parts) if html_parts else ""

    # def _fetch_tokopedia_product_content(self, url):
    #     html_page = self._fetch_product_page(url)
    #     if not html_page:
    #         return ""

    #     soup = BeautifulSoup(html_page, "html.parser")

    #     title = ""
    #     description = ""
    #     attributes = []

    #     # =========================
    #     # 1. META TITLE (AMAN)
    #     # =========================
    #     og_title = soup.find("meta", property="og:title")
    #     if og_title:
    #         title = og_title.get("content", "").strip()

    #     # =========================
    #     # 2. JSON TOKOPEDIA (PALING AKURAT)
    #     # =========================
    #     data = self._extract_tokopedia_json(soup)
    #     try:
    #         product = (
    #             data["props"]["pageProps"]["pdpData"]["basic"]
    #         )

    #         title = title or product.get("name", "")

    #         # attributes
    #         for attr in product.get("attributes", []):
    #             name = attr.get("name")
    #             value = attr.get("value")
    #             if name and value:
    #                 attributes.append((name, value))

    #         # description
    #         description = product.get("description", "").strip()

    #     except Exception:
    #         pass
    #     # broader attributes from __NEXT_DATA__
    #     if not attributes:
    #         attributes = self._collect_tokopedia_attributes(data)

    #     # =========================
    #     # 3. FALLBACK DESCRIPTION HTML
    #     # =========================
    #     if not description:
    #         desc_block = soup.find(attrs={"data-testid": "pdp-product-description"})
    #         if desc_block:
    #             description = desc_block.get_text("\n", strip=True)

    #     if not attributes:
    #         spec_block = soup.find(
    #             attrs={"data-testid": re.compile("pdp.*(spec|detail|attribute)", re.I)}
    #         )
    #         if spec_block:
    #             lines = [l.strip() for l in spec_block.get_text("\n").split("\n") if l.strip()]
    #             for line in lines:
    #                 if ":" in line:
    #                     key, val = [x.strip() for x in line.split(":", 1)]
    #                     if key and val:
    #                         attributes.append((key, val))

    #     # =========================
    #     # 4. FORMAT DESCRIPTION
    #     # =========================
    #     paragraphs = []
    #     bullets = []

    #     for line in description.splitlines():
    #         line = line.strip()
    #         if not line:
    #             continue
    #         if line.startswith("-"):
    #             bullets.append(line[1:].strip())
    #         else:
    #             paragraphs.append(line)

    #     # =========================
    #     # 5. BUILD HTML
    #     # =========================
    #     html_parts = []

    #     if title:
    #         html_parts.append(f"<h1>{html.escape(title)}</h1>")

    #     if attributes:
    #         html_parts.append("<h3>Detail Produk</h3>")
    #         html_parts.append("<ul>")
    #         for k, v in attributes:
    #             html_parts.append(
    #                 f"<li><strong>{html.escape(k)}:</strong> {html.escape(v)}</li>"
    #             )
    #         html_parts.append("</ul>")

    #     if paragraphs:
    #         html_parts.append("<p>" + "<br/><br/>".join(html.escape(p) for p in paragraphs) + "</p>")

    #     if bullets:
    #         html_parts.append("<ul>")
    #         for b in bullets:
    #             html_parts.append(f"<li>{html.escape(b)}</li>")
    #         html_parts.append("</ul>")

    #     return "\n".join(html_parts)
