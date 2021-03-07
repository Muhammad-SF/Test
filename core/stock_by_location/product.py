# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 BrowseInfo(<http://www.browseinfo.in>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, _
from odoo.tools.float_utils import float_round

class stock_location(models.Model):
    _name = 'stock.location.product'

    stock_location_id = fields.Many2one('stock.location', string="Location")
    on_hand_qty = fields.Float('On hand Quantity')
    custom_product_id = fields.Many2one('product.product')
    forcasted_qty = fields.Float('Forcasted Quantity')
    incoming_qty = fields.Float('Incoming Quantity')
    out_qty = fields.Float('Out Quantity')
    available_qty = fields.Float(string='Available Qty')
    reserved_qty = fields.Float(string='Reserved Qty')

class product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _compute_quantities_custom(self):
        res = {}
        for rec in self:
            res[rec.id] = []
            loc = rec.env['stock.location'].search([('usage', '=', 'internal')])
            for a in loc:
                domain_quant = [('product_id', '=', rec.id), ('location_id', '=', a.id)]
                domain_move_in = [('product_id', '=', rec.id), ('location_dest_id', '=', a.id)]
                domain_move_out = [('product_id', '=', rec.id), ('location_id', '=', a.id)]
                Move = rec.env['stock.move']
                Quant =  rec.env['stock.quant']
                domain_move_in_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_in
                domain_move_out_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_out
                incoming = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id']))
                outgoing = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id']))
                on_hand = dict((item['product_id'][0], item['qty']) for item in Quant.read_group(domain_quant, ['product_id', 'qty'], ['product_id']))
                available_qty = dict((item['product_id'][0], item['available_qty']) for item in Quant.read_group(domain_quant, ['product_id', 'available_qty'], ['product_id']))
                reserved_qty = dict((item['product_id'][0], item['reserved_available_qty']) for item in Quant.read_group(domain_quant, ['product_id', 'reserved_available_qty'], ['product_id']))
                vals = {
                            'stock_location_id':a.id,
                            'on_hand_qty':on_hand.get(rec.id, 0.0),
                            'incoming_qty':incoming.get(rec.id, 0.0),
                            'out_qty' :outgoing.get(rec.id, 0.0),
                            'custom_product_id':rec.id,
                            'forcasted_qty':(on_hand.get(rec.id, 0.0)) + (incoming.get(rec.id, 0.0) - outgoing.get(rec.id, 0.0)),
                            'available_qty': available_qty.get(rec.id, 0.0),
                            'reserved_qty': reserved_qty.get(rec.id, 0.0)
                            }
                if vals.get('on_hand_qty') == 0 and vals.get('incoming_qty') == 0 and vals.get('out_qty') == 0 and vals.get('forcasted_qty') ==0:
                    pass
                else:
                    rec.stock_location |= rec.env['stock.location.product'].create(vals)

    stock_location = fields.One2many('stock.location.product', 'custom_product_id', string="Stock Location", compute="_compute_quantities_custom")
