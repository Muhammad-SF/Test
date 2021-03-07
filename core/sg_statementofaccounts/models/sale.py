from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=False, required=True)

SaleOrder()