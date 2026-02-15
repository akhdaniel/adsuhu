from odoo import http, api, fields
from odoo.http import request
from markupsafe import Markup
import markdown
import re
import threading
import odoo
import logging
import time
import json
import base64
import psycopg2
simulation = True
_logger = logging.getLogger(__name__)

class ProductValueAnalysisController(http.Controller):
    def _clear_record_output(self, record, fieldname=None):
        vals = {}

        _logger.info(record._name) 
        
        if record._name == 'vit.audience_profiler':
            record.unlink()        
        elif record._name == 'vit.angle_hook':
            record.unlink()
        elif record._name == 'vit.product_value_analysis':
            if fieldname == "features":
                vals["features"] = False
            elif fieldname == "description":
                vals["description"] = False

        if "output" in record._fields:
            vals["output"] = False
        if "output_html" in record._fields:
            vals["output_html"] = False
                           
        if vals:
            record.sudo().write(vals)

    def _run_background(self, model_name, record_id, action):
        dbname = request.env.cr.dbname
        uid = request.env.uid
        context = dict(request.env.context)

        _logger.info("Background thread spawn: %s(%s) action=%s", model_name, record_id, action)

        def _target():
            _logger.info("Background thread started: %s(%s)", model_name, record_id)
            try:
                _logger.info("Background thread entering Odoo env: %s(%s)", model_name, record_id)
                registry = odoo.registry(dbname)
                _logger.info("Background thread got registry: %s(%s)", model_name, record_id)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    try:
                        with registry.cursor() as cr:
                            _logger.info("Background thread got cursor: %s(%s)", model_name, record_id)
                            env = api.Environment(cr, uid, context)
                            rec = env[model_name].sudo().browse(record_id)
                            try:
                                _logger.info("Background job start: %s(%s) action=%s", model_name, record_id, action)
                                action(rec)
                                _logger.info("Background job done: %s(%s)", model_name, record_id)
                                rec.write({"status": "done", "error_message": False})
                                cr.commit()
                            except Exception as e:
                                _logger.exception("Background job failed for %s(%s)", model_name, record_id)
                                rec.write({"status": "failed", "error_message": str(e)})
                                cr.commit()
                        break
                    except psycopg2.errors.SerializationFailure:
                        _logger.warning(
                            "Serialization failure for %s(%s) attempt %s/%s",
                            model_name,
                            record_id,
                            attempt,
                            max_attempts,
                        )
                        if attempt >= max_attempts:
                            raise
                        time.sleep(0.2 * attempt)
            except Exception:
                _logger.exception("Background thread crashed before job execution for %s(%s)", model_name, record_id)

        threading.Thread(target=_target, daemon=True).start()

    # Write features & desriptopn
    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/write_with_ai', type='json', auth='user', website=True, methods=['POST'])
    def write_with_ai(self, analysis, **kwargs):
        
        analysis.write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.product_value_analysis", analysis.id, lambda rec: rec.action_write_with_ai())
        return {"status": "processing"}

        '''
        analysis.write({"status": "processing", "error_message": False})
        try:
            analysis.action_write_with_ai()
            analysis.write({"status": "done", "error_message": False})
        except Exception as e:
            analysis.write({"status": "failed", "error_message": str(e)})
            raise

        result = analysis.read(['initial_description', 'description', 'features', 'lang_id'])[0]

        return [{
            'id': result.get('id'),
            'name':'Description',
            'output_html': result.get('description', ''),
            'with_next_button': False,
            'target_section':'description'

        },{
            'id': result.get('id'),
            'name':'Features',
            'output_html': result.get('features', ''),
            'target_section':'features',
            'next_step':'product_value_analysis'
        }]
        '''

    def _build_result(self, regenerate_type, record):
        _logger.info(f"regenerate_type={regenerate_type} record={record}")
        if regenerate_type == "write_with_ai":
            return [{
                "id": record.id,
                "name": "Product Value Analysis",
                "description": record.description or "",
                "features":record.features or "",
                "clear_url": f"/product_analysis/{record.id}/clear",
                "next_step":"product_value_analysis",
                "back_title": None,
                "show_view_button": True
            }]
        if regenerate_type == "product_value_analysis":
            return [{
                "id": record.id,
                "name": "Product Value Analysis",
                "output_html": record.output_html or "",
                "current_step":"product_value_analysis",
                "clear_url": f"/product_analysis/{record.id}/clear",
                "next_step":"market_map_analysis",
                "back_title": None,
                "show_view_button": True
            }]
        if regenerate_type == "market_map_analysis":
            return [{
                "id": mm.id,
                "name": mm.name,
                "output_html": mm.output_html or "",
                "prev_step":"product_value_analysis",
                "current_step":"market_map_analysis",
                "next_step":"audience_profile_analysis",
                "clear_url": f"/market_mapper/{mm.id}/clear",
                "back_title": f"Product {record.name}",      
                "show_view_button": True          
            } for mm in record.market_mapper_ids]
        if regenerate_type == "audience_profile_analysis":
            return [{
                "id": ap.id,
                "name": ap.name,
                "output_html": ap.output_html or "",
                "clear_url": f"/audience_profiler/{ap.id}/clear",
                "record_id": record.id,
                "prev_step": "market_map_analysis",
                "current_step":"audience_profile_analysis",
                "next_step":"angle_hook",
                "back_title": f"Market Map {record.name}",       
                "show_view_button": True         
            } for ap in record.audience_profiler_ids]
            # } for ap in record.audience_profiler_ids.sorted(key=lambda rec: rec.audience_profile_no or "")]
        if regenerate_type == "angle_hook":
            return [{
                "id": an.id,
                "name": f"AP {record.audience_profile_no} - Angle {an.angle_no}",
                "output_html": an.output_html or "",
                "clear_url": f"/angle_hook/{an.id}/clear",
                "record_id": record.id,
                "prev_step": "audience_profile_analysis",
                "current_step":"angle_hook",
                "back_title": f"AP {record.audience_profile_no}",
                "next_step": "hook",
                "hooks":[{
                    "id": hook.id,
                    "name": f"AP {record.audience_profile_no} - Angle {an.angle_no} - Hook {hook.hook_no}",
                    "output_html": hook.output_html,
                    "clear_url": f"/hook/{hook.id}/clear",
                    "prev_step": "angle_hook",
                    "current_step":"hook",
                    "next_step":"ads_copy",
                    "back_title": f"Angle {an.angle_no}",
                    "record_id": an.id,

                } for hook in an.hook_ids]
            } for an in record.angle_hook_ids.sorted(key=lambda rec: rec.angle_no or "")]
        if regenerate_type == "hook":
            
            return [{
                "id": ads.id,
                "name": f"Ads Copy: {ads.name}",
                "prev_step": "angle_hook",
                "current_step":"ads_copy",
                "record_id": record.id,                
                "images":[
                    {
                        "id": im.id,
                        "name": im.name,
                        "output_html": im.output_html,
                        "clear_url": f"/image_generator/{im.id}/clear",
                        "next_step":"generate_variants",
                        "back_title": f"Ads Copy {ads.name}",
                        "record_id": ads.id
                    } for im in ads.image_generator_ids
                ],
                "lps":[
                    {
                        "id": lp.id,
                        "name": lp.name,
                        "output_html": lp.output_html,
                        "clear_url": f"/landing_page/{lp.id}/clear",
                        "next_step":"generate_landing_pages",
                        "back_title": f"Ads Copy {ads.name}",
                        "record_id": ads.id
                    } for lp in ads.landing_page_builder_ids
                ],
                "videos":[
                    {
                        "id": vid.id,
                        "name": vid.name,
                        "output_html": vid.output_html,
                        "clear_url": f"/video_director/{vid.id}/clear",
                        "next_step":"generate_videos",
                        "back_title": f"Ads Copy {ads.name}",                        
                        "record_id": ads.id
                    } for vid in ads.video_director_ids
                ],
                "output_html": f"""{ads.output_html_trimmed}
<div class="d-flex align-items-center justify-content-center">
    <a class="btn btn-primary" href="#section-hook-{record.id}"> <i class="fa fa-arrow-left me-1"></i> Back to Hook {record.hook_no}</a>
    <a class="btn btn-primary" href="#ads-copy-images-{ads.id}">View Images</a>
    <a class="btn btn-primary" href="#ads-copy-lp-{ads.id}">View Landing Page</a>
    <a class="btn btn-primary" href="#ads-copy-video-{ads.id}">View Video Script</a>
</div>
""",
                "clear_url": f"/ads_copy/{ads.id}/clear",
            } for ads in record.ads_copy_ids.sorted(key=lambda rec: rec.name or "")]
            
        if regenerate_type == "image_variants":
            return [{
                "id": iv.id,
                "name": iv.name,
                "output_html": f"""<a href="{iv.image_url}" target="_new">
    <img src='{iv.image_url_512}' class='img-fluid'/>
</a>
""",
                "clear_url": f"/image_generator/{record.id}/clear",
                "record_id": record.id
            } for iv in record.image_variant_ids[-1]]
        return []

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/clear/<fieldname>', type='json', auth='user', website=True, methods=['POST'])
    def clear_product_analysis(self, analysis, fieldname, **kwargs):
        self._clear_record_output(analysis, fieldname)
        return {"status": "ok"}

    @http.route('/market_mapper/<model("vit.market_mapper"):market_mapper>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_market_mapper(self, market_mapper, **kwargs):
        self._clear_record_output(market_mapper)
        return {"status": "ok"}

    @http.route('/audience_profiler/<model("vit.audience_profiler"):audience_profiler>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_audience_profiler(self, audience_profiler, **kwargs):
        self._clear_record_output(audience_profiler)
        return {"status": "ok"}

    @http.route('/angle_hook/<model("vit.angle_hook"):angle_hook>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_angle_hook(self, angle_hook, **kwargs):
        self._clear_record_output(angle_hook)
        return {"status": "ok"}

    @http.route('/hook/<model("vit.hook"):hook>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_hook(self, hook, **kwargs):
        self._clear_record_output(hook)
        return {"status": "ok"}

    @http.route('/ads_copy/<model("vit.ads_copy"):ads_copy>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_ads_copy(self, ads_copy, **kwargs):
        self._clear_record_output(ads_copy)
        return {"status": "ok"}

    @http.route('/image_generator/<model("vit.image_generator"):image_generator>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_image_generator(self, image_generator, **kwargs):
        self._clear_record_output(image_generator)
        return {"status": "ok"}

    @http.route('/video_director/<model("vit.video_director"):video_director>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_video_director(self, video_director, **kwargs):
        self._clear_record_output(video_director)
        return {"status": "ok"}

    @http.route('/landing_page/<model("vit.landing_page_builder"):landing_page>/clear', type='json', auth='user', website=True, methods=['POST'])
    def clear_landing_page(self, landing_page, **kwargs):
        self._clear_record_output(landing_page)
        return {"status": "ok"}

    # CRUD 
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

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/download_docx', type='http', auth='user', website=True)
    def download_docx(self, analysis, **kwargs):
        action = analysis.sudo().action_download_docx()
        url = action.get("url") if isinstance(action, dict) else None
        if url:
            return request.redirect(url)
        return request.redirect(f'/product_analysis/{analysis.id}')

    @http.route(['/customer_credits', '/customer_credits/page/<int:page>'], type='http', auth='user', website=True)
    def customer_credits(self, page=1, **kwargs):
        credit_obj = request.env['vit.customer_credit'].sudo()
        partner = request.env.user.partner_id
        domain = [('customer_id', '=', partner.id)]

        per_page = 20
        total = credit_obj.search_count(domain)
        pager = request.website.pager(
            url='/customer_credits',
            total=total,
            page=page,
            step=per_page,
            scope=7,
            url_args=kwargs
        )

        credits = credit_obj.search(
            domain,
            offset=pager['offset'],
            limit=per_page,
            order="date_time desc"
        )

        return request.render('vit_adsuhu_frontend.customer_credits_list_template', {
            'credits': credits,
            'pager': pager,
        })

    @http.route('/payment/manual_info', type='json', auth='user', website=True, methods=['POST'])
    def manual_payment_info(self, **kwargs):
        provider = request.env['payment.provider'].sudo().search(
            [('code', '=', 'custom'), ('is_published', '=', True), ('state', '=', 'enabled')], limit=1
        )
        if not provider or not provider.pending_msg:
            return {"error": "Manual payment instruction not configured."}
        return {"message": provider.pending_msg}

    @http.route('/payment/manual_submit', type='http', auth='user', website=True, methods=['POST'])
    def manual_payment_submit(self, **post):
        package = (post.get('package') or '').strip()
        amount_raw = (post.get('amount') or post.get('custom_amount') or '').strip()
        partner = request.env.user.partner_id
        proof_file = request.httprequest.files.get('transfer_proof')

        if not partner:
            return request.make_response(
                json.dumps({"error": "Partner not found."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        if not proof_file:
            return request.make_response(
                json.dumps({"error": "Transfer proof file is required."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        predefined_packages = {
            "100000": {"amount": 100000.0},
            "200000": {"amount": 200000.0},
            "500000": {"amount": 500000.0},
        }

        try:
            if package in predefined_packages:
                amount = predefined_packages[package]["amount"]
            else:
                amount = float(amount_raw or 0)
            if amount <= 0:
                raise ValueError("amount must be positive")
        except Exception:
            return request.make_response(
                json.dumps({"error": "Invalid top up amount."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        proof_content = proof_file.read()
        if not proof_content:
            return request.make_response(
                json.dumps({"error": "Transfer proof file is empty."}),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        credit = request.env['vit.customer_credit'].sudo().create({
            'customer_id': partner.id,
            'ref': 'Manual transfer - pending verification',
            'credit': amount,
            'is_usage': False,
            'date_time': fields.Datetime.now(),
            'state': 'draft',
            'transfer_proof': base64.b64encode(proof_content).decode(),
            'transfer_proof_filename': proof_file.filename or 'transfer_proof',
        })

        return request.make_response(
            json.dumps({"success": True, "id": credit.id}),
            headers=[('Content-Type', 'application/json')],
            status=200,
        )

    @http.route('/product_analysis/submit', type='http', auth='user', website=True, methods=['POST'])
    def submit(self, **post):
        product_name = post.get('product_name')
        product_url = post.get('product_url')
        target_market = post.get('target_market')
        description = post.get('description')
        initial_description = post.get('initial_description')
        features = post.get('features')
        tags = post.get('tags')
        deafult_lang = request.env['res.lang'].search([('active', '=', True)], limit=1)
        lang_id = int(post.get('lang_id')) if post.get('lang_id') else deafult_lang.id

        # if not product_url:
        #     return request.redirect('/product_analysis/create')

        new_analysis = request.env['vit.product_value_analysis'].create({
            'name': product_name,
            'product_url': product_url,
            'target_market': target_market,
            'description': description,
            'initial_description': initial_description,
            'features': features,
            'tags': tags,
            'lang_id': lang_id,
            'partner_id': request.env.user.partner_id.id
        })

        return request.redirect(f'/product_analysis/{new_analysis.id}')

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/update', type='http', auth='user', website=True, methods=['POST'])
    def update(self, analysis, **post):
        product_name = post.get('product_name')
        product_url = post.get('product_url')
        target_market = post.get('target_market')
        description = post.get('description')
        initial_description = post.get('initial_description')
        features = post.get('features')
        deafult_lang = request.env['res.lang'].search([('active', '=', True)], limit=1)
        lang_id = int(post.get('lang_id')) if post.get('lang_id') else deafult_lang.id

        if not product_url:
            return request.redirect(f'/product_analysis/{analysis.id}/edit')

        analysis.write({
            'name': product_name if product_name else analysis.name,
            'product_url': product_url,
            'target_market': target_market if target_market else analysis.target_market,
            'description': description,
            'initial_description': initial_description,
            'features': features,
            'lang_id': lang_id,
        })

        return request.redirect(f'/product_analysis/{analysis.id}')

    # Regenerate secion
    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_product_analysis(self, analysis, **kwargs):
        analysis.write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.product_value_analysis", analysis.id, lambda rec: rec.action_generate())
        return {"status": "processing"}

    @http.route('/product_analysis/<model("vit.product_value_analysis"):analysis>/market_mapper/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_market_mapper(self, analysis, **kwargs):
        analysis.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.product_value_analysis", analysis.id, lambda rec: rec.action_generate_market_mapping())
        return {"status": "processing"}

    @http.route('/market_mapper/<model("vit.market_mapper"):market_mapper>/audience_profiler/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_audience_profiler(self, market_mapper, **kwargs):
        market_mapper.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.market_mapper", market_mapper.id, lambda rec: rec.action_generate_audience_profiler())
        return {"status": "processing"}

    @http.route('/audience_profiler/<model("vit.audience_profiler"):audience_profiler>/angle_hook/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_angle_hook(self, audience_profiler, **kwargs):
        audience_profiler.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.audience_profiler", audience_profiler.id, lambda rec: rec.action_generate_angles())
        return {"status": "processing"}

    @http.route('/hook/<model("vit.hook"):hook>/ads_copy/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_ads_copy(self, hook, **kwargs):
        hook.write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.hook", hook.id, lambda rec: rec.action_create_ads_copy())
        return {"status": "processing"}

    @http.route('/image_generator/<model("vit.image_generator"):image_generator>/image_variant/regenerate', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_image_variant(self, image_generator, **kwargs):
        image_generator.sudo().write({"status": "processing", "error_message": False})
        request.env.cr.commit()
        self._run_background("vit.image_generator", image_generator.id, lambda rec: rec.action_generate())
        return {"status": "processing"}
    
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



    # fetch status
    @http.route('/regenerate_status/<string:regenerate_type>/<int:record_id>', type='json', auth='user', website=True, methods=['POST'])
    def regenerate_status(self, regenerate_type, record_id, **kwargs):
        model_map = {
            "write_with_ai": "vit.product_value_analysis",
            "product_value_analysis": "vit.product_value_analysis",
            "market_map_analysis": "vit.product_value_analysis",
            "audience_profile_analysis": "vit.market_mapper",
            "angle_hook": "vit.audience_profiler",
            "hook": "vit.hook",
            "ads_copy": "vit.hook",
            "image_variants": "vit.image_generator",
        }
        model_name = model_map.get(regenerate_type)
        if not model_name:
            return {"status": "failed", "error": "Unknown regenerate type."}

        record = request.env[model_name].browse(record_id)
        status = record.status or "idle"
        result = []
        if status == "done":
            result = self._build_result(regenerate_type, record)
        error_message = record.error_message if status == "failed" else False
        return {"status": status, "result": result, "error": error_message}

    # view details
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
