# -*- coding: utf-8 -*-
#
#
#    Author: Guewen Baconnier, Yannick Vaucher
#    Copyright 2013-2015 Camptocamp SA
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
#
from odoo import models, api, fields, osv
from odoo.osv import orm
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_procurement_group_by_line(self, line):
        """ Hook to be able to use line data on procurement group """
        return self._prepare_procurement_group()

    ###
    # OVERRIDE to use sale.order.line's procurement_group_id from lines
    ###
    @api.one
    @api.depends('order_line.procurement_group_id.procurement_ids.state')
    def _get_shipped(self):
        """ As procurement is per sale line basis, we check each line

            If at least a line has no procurement group defined, it means it
            isn't shipped yet.

            Only when all procurement are done or cancelled, we consider
            the sale order as being shipped.

            And if there is no line, we have nothing to ship, thus it isn't
            shipped.

        """
        if not self.order_line:
            self.shipped = False
            return

        # keep empty groups
        groups = set([line.procurement_group_id
                      for line in self.order_line
                      if line.product_id.type != 'service'])
        is_shipped = True
        for group in groups:
            if not group or not group.procurement_ids:
                is_shipped = False
                break
            is_shipped &= all([proc.state in ['cancel', 'done']
                               for proc in group.procurement_ids])
        self.shipped = is_shipped

    ###
    # OVERRIDE to find sale.order.line's picking
    ###
    @api.multi
    def _get_pickings(self):
        res = {}
        for sale in self:
            group_ids = set([line.procurement_group_id.id
                             for line in sale.order_line
                             if line.procurement_group_id])
            if not any(group_ids):
                sale.picking_ids = []
                continue
            sale.picking_ids = self.env.get('stock.picking').search([('group_id', 'in', list(group_ids))])

    picking_ids = fields.One2many('stock.picking', string='Picking associated to this sale', compute='_get_pickings')
    shipped     = fields.Boolean(
        compute='_get_shipped',
        string='Delivered',
        store=True)


class SaleOrderLine(orm.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _action_procurement_create(self):
        """
        Create procurements based on quantity ordered. If the quantity is increased, new
        procurements are created. If the quantity is decreased, no automated action is taken.
        """
        res = super(SaleOrderLine, self)._action_procurement_create()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order']  # Empty recordset
        groups = {}
        for line in self:
            if line.state != 'sale' or not line.product_id._need_procurement():
                continue
            qty = 0.0
            for proc in line.procurement_ids:
                qty += proc.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = groups.get(line._get_procurement_group_key())
            if not group_id:
                vals = line.order_id._prepare_procurement_group_by_line(line)
                group_id = self.env['procurement.group'].create(vals)
                groups[line._get_procurement_group_key()] = group_id
            line.procurement_group_id = group_id

            # if not line.order_id.procurement_group_id:

            vals = line._prepare_order_line_procurement(group_id=group_id.id)
            vals['product_qty'] = line.product_uom_qty - qty
            new_proc = self.env['procurement.order'].create(vals)
            new_proc.message_post_with_view('mail.message_origin_link',
                                            values={'self': new_proc, 'origin': line.order_id},
                                            subtype_id=self.env.ref('mail.mt_note').id)
            new_procs += new_proc
            new_procs = self.product_pack_do_line(line,new_procs)

        new_procs.run()
        return res

    def product_pack_do_line(self,line,new_procs):
        if line.product_id.is_pack:
            if not line.order_id.procurement_group_id and line.product_id.pack_stock_management == 'decrmnt_products':
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)
            vals = line._prepare_order_line_procurement(group_id=line.order_id.procurement_group_id.id)
            temp = vals
            if line.product_id.pack_stock_management != 'decrmnt_pack':
                for pack_obj in line.product_id.wk_product_pack:            
                    temp['product_id'] = pack_obj.product_name.id
                    temp['product_qty'] = line.product_uom_qty * pack_obj.product_quantity
                    temp['product_uom'] = pack_obj.product_name.uom_id.id
                    temp['message_follower_ids'] = False
                    temp['sale_line_id'] = False
                    new_proc = self.env["procurement.order"].create(temp)
                    new_procs += new_proc
            return new_procs



    # @api.multi
    # def _get_procurement_group_key(self):
    #     """ Return a key with priority to be used to regroup lines in multiple
    #     procurement groups

    #     """
    #     return (8, self.order_id.id)

    procurement_group_id = fields.Many2one(
        'procurement.group',
        'Procurement group',
        copy=False)
