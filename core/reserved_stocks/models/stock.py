# -*- coding: utf-8 -*-
from odoo import models, fields

class stock_move(models.Model):
    _inherit = 'stock.move'

    reserved_by_id = fields.Many2one('res.users', string='Reserved By')
    is_reserved = fields.Boolean('Reserved')

stock_move()