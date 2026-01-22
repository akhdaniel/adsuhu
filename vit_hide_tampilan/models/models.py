# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class vit_kerma_tampilan(models.Model):
#     _name = 'vit_kerma_tampilan.vit_kerma_tampilan'
#     _description = 'vit_kerma_tampilan.vit_kerma_tampilan'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
