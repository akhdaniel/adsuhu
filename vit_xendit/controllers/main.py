from odoo import http, fields
from odoo.http import request

import logging
import time
import requests

_logger = logging.getLogger(__name__)
_webhook_url = '/payment/xendit/webhook'


class XenditController(http.Controller):
    def _get_xendit_config(self):
        params = request.env['ir.config_parameter'].sudo()
        return {
            "public_key": params.get_param('xendit_public_key'),
            "secret_key": params.get_param('xendit_secret_key'),
            "webhook_token": params.get_param('xendit_webhook_token'),
            "topup_amount": float(params.get_param('xendit_topup_amount', '10000')),
            "topup_credit": float(params.get_param('xendit_topup_credit', '1')),
            "topup_currency": params.get_param('xendit_topup_currency', 'IDR'),
        }

    def _xendit_make_request(self, endpoint, payload, secret_key):
        url = f'https://api.xendit.co/{endpoint}'
        auth = (secret_key, '')
        response = requests.post(url, json=payload, auth=auth, timeout=10)
        response.raise_for_status()
        return response.json()

    @http.route('/xendit/create_payment', type='json', auth='user', website=True, methods=['POST'])
    def create_payment(self, **kwargs):
        payload_data = request.get_json_data()

        _logger.info(f'payload = {payload_data}')
        partner = request.env.user.partner_id
        cfg = self._get_xendit_config()
        if not cfg["secret_key"]:
            return {"error": "Xendit secret key not configured."}

        packages = {
            "100000": {"amount": 100000.0, "credit": 1_000.0},
            "200000": {"amount": 200000.0, "credit": 2_000.0},
            "500000": {"amount": 500000.0, "credit": 7_500.0},
        }
        # payload_data = kwargs or {}
        # _logger.info(payload_data)
        package_key = payload_data.get("package") or "100000"
        custom_amount = payload_data.get("custom_amount")
        raw_amount = payload_data.get("amount")
        if package_key == "custom":
            try:
                amount = float(custom_amount or raw_amount)
            except (TypeError, ValueError):
                return {"error": "Invalid custom amount."}
            if amount < 10000:
                return {"error": "Minimum top up is Rp 10,000."}
            credit = (amount / 100000.0) * 1_000.0
            package = {"amount": amount, "credit": credit}
        else:
            if raw_amount:
                try:
                    amount = float(raw_amount)
                except (TypeError, ValueError):
                    return {"error": "Invalid top up amount."}
                if amount < 100000:
                    return {"error": "Minimum top up is Rp 100,000."}
                credit = (amount / 100000.0) * 1_000.0
                package = {"amount": amount, "credit": credit}
            else:
                if package_key not in packages:
                    return {"error": "Invalid top up package."}
                package = packages[package_key]

        external_id = f"adsuhu_topup:{partner.id}:{package['credit']}:{int(time.time())}"

        payload = {
            "external_id": external_id,
            "amount": package["amount"],
            "payer_email": partner.email or "",
            "description": f"Top up credit for {partner.name or 'customer'}",
            "success_redirect_url": f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/customer_credits",
            "failure_redirect_url": f"{request.env['ir.config_parameter'].sudo().get_param('web.base.url')}/customer_credits",
            "currency": cfg["topup_currency"],
        }
        
        
        _logger.info(payload)

        credit_model = request.env['vit.customer_credit'].sudo()
        credit_model.create({
            'customer_id': partner.id,
            'name': external_id,
            'credit': package["credit"],
            'is_usage': False,
            'state': 'draft',
            'date_time': fields.Datetime.now(),
        })

        result = self._xendit_make_request("v2/invoices", payload=payload, secret_key=cfg["secret_key"])
        url = result.get("invoice_url")
        if not url:
            _logger.error("Xendit invoice_url missing: %s", result)
            return {"error": "Failed to create payment URL."}
        return {"url": url}

    @http.route('/xendit/webhook', type='json', auth='public', csrf=False, methods=['POST'])
    def webhook(self, **kwargs):
        # payload = request.get_json_data()
        payload = (kwargs or {}) or request.httprequest.get_json(silent=True) or {}
        _logger.info(f"payload={payload}")
        token = request.httprequest.headers.get('x-callback-token')
        cfg = self._get_xendit_config()
        expected_token = cfg["webhook_token"]
        if expected_token and token != expected_token:
            _logger.warning("Xendit webhook token mismatch.")
            return {"status": "forbidden"}

        forward_url = payload.get("success_redirect_url") or ""
        _logger.info(f'forward_url={forward_url}')
        if forward_url.startswith("https://bootcamp.vitraining.com"):
            try:
                _logger.info('forward to bootcamp...')
                resp = requests.post(
                    f"https://bootcamp.vitraining.com/{_webhook_url}",
                    json=payload,
                    timeout=10,
                )
                
                _logger.info(f"bootcamp response {resp.text}")
                return {
                    "status": "ok",
                    "forward": {
                        "status_code": resp.status_code,
                        "text": resp.text,
                    },
                }
            except Exception as e:
                _logger.warning("Forward webhook failed: %s", e)
                return {"status": "forward_failed", "error": str(e)}

        status = payload.get("status") or payload.get("invoice_status")
        if status not in ["PAID", "SETTLED"]:
            return {"status": "ignored"}

        external_id = payload.get("external_id") or ""
        if not external_id.startswith("adsuhu_topup:"):
            return {"status": "ignored"}

        try:
            _, partner_id, credit_str, _ = external_id.split(":", 3)
            partner_id = int(partner_id)
            credit = float(credit_str)
        except Exception:
            _logger.exception("Invalid external_id: %s", external_id)
            return {"status": "invalid_external_id"}

        credit_model = request.env['vit.customer_credit'].sudo()
        existing = credit_model.search(
            [('name', '=', external_id), ('customer_id', '=', partner_id)], limit=1
        )
        if existing:
            existing.write({'state': 'done'})
            return {"status": "ok"}

        credit_model.create({
            'customer_id': partner_id,
            'name': external_id,
            'credit': credit,
            'is_usage': False,
            'state': 'done',
            'date_time': request.env['ir.fields']._now(),
        })
        return {"status": "ok"}
