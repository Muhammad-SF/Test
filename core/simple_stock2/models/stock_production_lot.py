from odoo import models, fields, api, _
from odoo.exceptions import UserError

class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'

    stock_in_id = fields.Many2one('simple.stock.in', 'Stock In ID')
    quant_ids = fields.One2many('stock.quant', 'lot_id', 'Quants')
