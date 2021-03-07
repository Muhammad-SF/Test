# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ComponentMaterials(models.Model):
    _name = 'component.materials'

    component_id      = fields.Many2one('product.template', 'Materials')
    product_id        = fields.Many2one('product.product', 'Product')
    material_quantity = fields.Integer('Quantity', default=1)
    allocation_cost   = fields.Float('Allocation Cost (%)', default=0)