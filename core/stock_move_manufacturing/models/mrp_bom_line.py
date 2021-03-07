from odoo import models, fields, api

class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'

    location_id   = fields.Many2one('stock.location','Stock Location')
