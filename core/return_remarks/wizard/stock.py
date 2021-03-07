# -*- coding: utf-8 -*-
from odoo import models, fields

class stock_return_picking(models.TransientModel):
    _inherit = 'stock.return.picking'

    remarks = fields.Char('Remarks')

stock_return_picking()

class stock_return_picking_line(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    return_reason = fields.Many2one('return.reasons', string='Return Reason')

stock_return_picking_line()