# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    user_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson')
    sale_order_name = fields.Char(related='order_id.name', store=True, string='Sale Order Number')