from odoo import http
from odoo.http import request
from markupsafe import Markup
import markdown
import re

class ProductValueAnalysisController(http.Controller):

    @http.route(['/product_analysis', '/product_analysis/page/<int:page>'], type='http', auth='user', website=True)
    def list(self, page=1, **kwargs):
        product_analysis_obj = request.env['vit.product_value_analysis']
        domain = []
        
        # Pagination
        per_page = 12
        total = product_analysis_obj.search_count(domain)
        pager = request.website.pager(
            url='/product_analysis',
            total=total,
            page=page,
            step=per_page,
            scope=7,
            url_args=kwargs
        )
        
        analyses = product_analysis_obj.search(domain, offset=pager['offset'], limit=per_page, order="create_date desc")
        
        return request.render('vit_adsuhu_frontend.product_analysis_list_template', {
            'analyses': analyses,
            'pager': pager,
        })

    @http.route('/product_analysis/create', type='http', auth='user', website=True)
    def create(self, **kwargs):
        langs = request.env['res.lang'].search([('active', '=', True)])
        return request.render('vit_adsuhu_frontend.product_analysis_create_template', {
            'langs': langs,
        })

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/edit', type='http', auth='user', website=True)
    def edit(self, analysis, **kwargs):
        langs = request.env['res.lang'].search([('active', '=', True)])
        return request.render('vit_adsuhu_frontend.product_analysis_edit_template', {
            'analysis': analysis,
            'langs': langs,
        })

    @http.route('/product_analysis/submit', type='http', auth='user', website=True, methods=['POST'])
    def submit(self, **post):
        product_name = post.get('product_name')
        product_url = post.get('product_url')
        target_market = post.get('target_market')
        description = post.get('description')
        features = post.get('features')
        deafult_lang = request.env['res.lang'].search([('active', '=', True)], limit=1)
        lang_id = int(post.get('lang_id')) if post.get('lang_id') else deafult_lang.id

        # if not product_url:
        #     return request.redirect('/product_analysis/create')

        new_analysis = request.env['vit.product_value_analysis'].sudo().create({
            'name': product_name,
            'product_url': product_url,
            'target_market': target_market,
            'description': description,
            'features': features,
            'lang_id': lang_id,
        })

        return request.redirect(f'/product_analysis/{new_analysis.id}')

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/update', type='http', auth='user', website=True, methods=['POST'])
    def update(self, analysis, **post):
        product_name = post.get('product_name')
        product_url = post.get('product_url')
        target_market = post.get('target_market')
        description = post.get('description')
        features = post.get('features')
        deafult_lang = request.env['res.lang'].search([('active', '=', True)], limit=1)
        lang_id = int(post.get('lang_id')) if post.get('lang_id') else deafult_lang.id

        if not product_url:
            return request.redirect(f'/product_analysis/{analysis.id}/edit')

        analysis.sudo().write({
            'name': product_name if product_name else analysis.name,
            'product_url': product_url,
            'target_market': target_market if target_market else analysis.target_market,
            'description': description,
            'features': features,
            'lang_id': lang_id,
        })

        return request.redirect(f'/product_analysis/{analysis.id}')

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/write_with_ai', type='json', auth='user', website=True, methods=['POST'])
    def write_with_ai(self, analysis, **kwargs):
        analysis.sudo().action_write_with_ai()
        result = analysis.sudo().read(['description', 'features', 'lang_id'])[0]
        return {
            'description': result.get('description', ''),
            'features': result.get('features', ''),
            'lang_id': result.get('lang_id', False),
        }

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_product_analysis(self, analysis, **kwargs):
        analysis.sudo().action_generate()
        return [{
            'output_html': analysis.sudo().output_html or '',
        }]

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/market_mapper/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_market_mapper(self, analysis, **kwargs):
        analysis.sudo().action_generate_market_mapping()
        return [{
            'name': mm.name,
            'output_html': mm.output_html or '',
        } for mm in analysis.market_mapper_ids]

    @http.route('/market_mapper/<model("vit.market_mapper"):market_mapper>/audience_profiler/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_audience_profiler(self, market_mapper, **kwargs):
        market_mapper.action_create_audience_profiles()
        return [{
            'name': ap.name,
            'output_html': ap.output_html or '',
        } for ap in market_mapper.audience_profiler_ids]

    @http.route('/audience_profiler/<model("vit.audience_profiler"):audience_profiler>/angle_hook/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_angle_hook(self, audience_profiler, **kwargs):
        audience_profiler.action_generate_angles()
        return [{
            'name': an.name,
            'output_html': an.output_html or '',
        } for an in audience_profiler.angle_hook_ids]

    # @http.route('/product_analysis/hook/<model("vit.hook"):hook>/regenerate', type='json', auth='user', website=True, methods=['POST'])
    # def regenerate_hook(self, hook, **kwargs):
    #     hook.action_create_ads_copy()
    #     return [{
    #         'output_html': ads.output_html or '',
    #     } for ads in hook.ads_copy_ids]

    @http.route('/hook/<model("vit.hook"):hook>/ads_copy/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_ads_copy(self, hook, **kwargs):
        hook.action_create_ads_copy()

        return [{
            'name': ads.name,
            'output_html': ads.output_html or '',
        } for ads in hook.ads_copy_ids]

    @http.route('/image_generator/<model("vit.image_generator"):image_generator>/image_variant/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_image_variant(self, image_generator, **kwargs):
        image_generator.action_generate()

        return [{
            'name': iv.name,
            'output_html': f"""<a href="{iv.image_url}" target="_new">
    <img src='{iv.image_url_512}' class='img-fluid'/>
</a>
""",
        } for iv in image_generator.image_variant_ids[-1]]
    
    def _add_img_responsive_classes(self, html):
        if not html:
            return html

        def _inject(match):
            tag = match.group(0)
            class_match = re.search(r'class="([^"]*)"', tag)
            if class_match:
                classes = class_match.group(1).split()
                if "img" not in classes:
                    classes.append("img")
                if "img-fluid" not in classes:
                    classes.append("img-fluid")
                new_class_attr = f'class="{" ".join(classes)}"'
                return tag[: class_match.start()] + new_class_attr + tag[class_match.end() :]
            return tag.replace("<img", '<img class="img img-fluid"', 1)

        return re.sub(r"<img\b[^>]*>", _inject, html)

    def _process_markdown(self, text):
        if not text:
            return '', ''
        
        lines = text.split('\n')
        new_lines = []
        toc_lines = []
        counters = [0] * 6  # For h1 to h6
        
        import re
        header_pattern = re.compile(r'^(#{1,6})\s+(.*)')
        
        for line in lines:
            match = header_pattern.match(line)
            if match:
                hashes, title = match.groups()
                level = len(hashes)
                
                # Increment current level, reset deeper levels
                counters[level-1] += 1
                for i in range(level, 6):
                    counters[i] = 0
                
                # Build version string 1.2.1
                version_parts = [str(c) for c in counters[:level]]
                version = ".".join(version_parts)
                
                new_title = f"{version} {title}"
                new_lines.append(f"{hashes} {new_title}")
                
                # Add to TOC
                indent = "  " * (level - 1)
                slug = re.sub(r'[^a-zA-Z0-9\-_]', '', new_title.replace(' ', '-').lower())
                
                # Check if the title already has a link, if so avoid double linking in TOC or handle gracefully
                # Generally markdown headers get IDs. We need to ensure we can link to them.
                # The 'toc' extension usually handles IDs.
                # If we manually change content, 'toc' extension will see the numbers.
                # simpler approach: Just collect them here, we will rely on markdown toc extension for anchoring if we pass 'toc' extension?
                # Actually, simply prepending text is enough. 
                # To define anchors, we might rely on python-markdown's default behavior or 'toc' extension.
                # Let's use [TOC] marker if we want to use the extension, BUT the user wants numbering in the text too.
                # So we modified the text.
                
                toc_lines.append(f"{indent}- [{new_title}](#slug-{version.replace('.', '-')})")
                
                # Add explicit anchor to the line to ensure linking works
                # Python-markdown attr_list extension allows {: #id } but maybe not available?
                # We can use raw html or just hope standard slugify works with the new numbering?
                # Safer: inject encoded header id if we can. 
                # Let's try to append standard HTML anchor if possible or use attr_list if available.
                # Since we don't know extensions available, let's output raw HTML header? No, mixing markdown is risky.
                # Let's use the fact that later we render with markdown.
                
                # Optimized approach:
                # We modified the line to: "## 1.1 Title"
                # We want a TOC that links to this.
                # Standard markdown generates id "11-title" or similar.
                # Let's manually constructing a cleaned slug is hard to match exactly what python-markdown does.
                # ALTERNATIVE: Don't generate TOC manually, just Number the headers, then use the 'toc' extension to generate the TOC?
                # User asked to "create table of content section".
                # If we use `markdown(extensions=['toc'])` object, we can extract the TOC object.
                pass 
            else:
                new_lines.append(line)
        
        numbered_text = "\n".join(new_lines)
        
        # Now pass to markdown with 'toc' extension
        md = markdown.Markdown(extensions=['tables', 'toc'])
        html_content = md.convert(numbered_text)
        html_content = self._add_img_responsive_classes(html_content)
        
        # The 'toc' extension automatically supports [TOC] marker, but we can also access md.toc
        # However, to display TOC separately, we can return md.toc
        
        return Markup(html_content), Markup(md.toc)

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>', type='http', auth='user', website=True)
    def detail(self, analysis, **kwargs):
        final_report_html, final_report_toc = self._process_markdown(analysis.final_report)
        
        values = {
            'analysis': analysis,
            'description_html': Markup(markdown.markdown(analysis.description, extensions=['tables'])) if analysis.description else '',
            'features_html': Markup(markdown.markdown(analysis.features, extensions=['tables'])) if analysis.features else '',
            'final_report_html': final_report_html,
            'final_report_toc': final_report_toc,
        }
        return request.render('vit_adsuhu_frontend.product_analysis_detail_template', values)
