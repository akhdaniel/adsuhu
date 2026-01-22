# -*- coding: utf-8 -*-
# from odoo import http


# class VitKermaTampilan(http.Controller):
#     @http.route('/vit_kerma_tampilan/vit_kerma_tampilan', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vit_kerma_tampilan/vit_kerma_tampilan/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('vit_kerma_tampilan.listing', {
#             'root': '/vit_kerma_tampilan/vit_kerma_tampilan',
#             'objects': http.request.env['vit_kerma_tampilan.vit_kerma_tampilan'].search([]),
#         })

#     @http.route('/vit_kerma_tampilan/vit_kerma_tampilan/objects/<model("vit_kerma_tampilan.vit_kerma_tampilan"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vit_kerma_tampilan.object', {
#             'object': obj
#         })
