# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.float_utils import float_compare, float_round
import time


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    pick_id = fields.Many2one('stock.picking')

    @api.model
    def default_get(self, fields):
        res = super(StockBackorderConfirmation, self).default_get(fields)
        if 'pick_id' in fields and self._context.get('active_id') and not res.get('pick_id'):
            res = {'pick_id': self._context['active_id']}
        return res

    @api.one
    def _process(self, cancel_backorder=False):
        for order in self:
            operations_to_delete = order.pick_id.pack_operation_ids.filtered(lambda o: o.qty_done <= 0)
            for pack in order.pick_id.pack_operation_ids - operations_to_delete:
                pack.product_qty = pack.qty_done
            operations_to_delete.unlink()
            order.pick_id.do_transfer()
            if cancel_backorder:
                backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', order.pick_id.id)])
                backorder_pick.action_cancel()
                order.pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))

    @api.multi
    def process(self):
        for order in self:
            order._process()

    @api.multi
    def process_cancel_backorder(self):
        for order in self:
            order._process(cancel_backorder=True)



















class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_cancel(self, backorder_moves=[]):
        res = super(Picking, self).action_cancel()
        account_move = self.env['account.move'].search([('ref','=',self.name)])
        account_move.button_cancel()
        return res


    @api.multi
    def _create_backorder(self, backorder_moves=[]):
        res = super(Picking, self)._create_backorder(backorder_moves)
        for picking in self.filtered(lambda pick: pick.picking_type_id.code == 'outgoing'):
            backorder = picking.search([('backorder_id', '=', picking.id)])
            if backorder.group_id: # origin from a sale
                order = self.env['sale.order'].search([('procurement_group_id', '=', backorder.group_id.id)])
                backorder.message_post_with_view(
                    'mail.message_origin_link',
                    values={'self': backorder, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return res




    @api.multi
    def _create_backorder(self, backorder_moves=[]):
        """ Move all non-done lines into a new backorder picking. If the key 'do_only_split' is given in the context, then move all lines not in context.get('split', []) instead of all non-done lines.
        """
        # TDE note: o2o conversion, todo multi
        backorders = self.env['stock.picking']
        for picking in self:
            backorder_moves = backorder_moves or picking.move_lines
            if self._context.get('do_only_split'):
                not_done_bo_moves = backorder_moves.filtered(lambda move: move.id not in self._context.get('split', []))
            else:
                not_done_bo_moves = backorder_moves.filtered(lambda move: move.state not in ('done', 'cancel'))
            if not not_done_bo_moves:
                continue
            backorder_picking = picking.copy({
                'name': '/',
                'move_lines': [],
                'pack_operation_ids': [],
                'backorder_id': picking.id
            })
            picking.message_post(body=_("Back order <em>%s</em> <b>created</b>.") % (backorder_picking.name))
            not_done_bo_moves.write({'picking_id': backorder_picking.id})
            if not picking.date_done:
                picking.write({'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
            backorder_picking.action_confirm()
            backorder_picking.action_assign()
            backorders |= backorder_picking
        return backorders



















    @api.multi
    def action_cancel_draft(self):
        if not len(self.ids):
            return False
        move_obj = self.env['stock.move']
        for (ids, name) in self.name_get():
            message = _("Picking '%s' has been set in draft state.") % name
            self.message_post(message)
        for pick in self:
            ids2 = [move.id for move in pick.move_lines]
            moves = move_obj.browse(ids2)
            moves.sudo().action_draft()
        return True







    @api.multi
    def do_transfer(self):
        """ If no pack operation, we do simple action_done of the picking.
        Otherwise, do the pack operations. """
        # TDE CLEAN ME: reclean me, please
        self._create_lots_for_picking()

        no_pack_op_pickings = self.filtered(lambda picking: not picking.pack_operation_ids)
        no_pack_op_pickings.action_done()
        other_pickings = self - no_pack_op_pickings
        for picking in other_pickings:
            need_rereserve, all_op_processed = picking.picking_recompute_remaining_quantities()
            todo_moves = self.env['stock.move']
            toassign_moves = self.env['stock.move']

            # create extra moves in the picking (unexpected product moves coming from pack operations)
            if not all_op_processed:
                todo_moves |= picking._create_extra_moves()

            if need_rereserve or not all_op_processed:
                moves_reassign = any(x.origin_returned_move_id or x.move_orig_ids for x in picking.move_lines if x.state not in ['done', 'cancel'])
                if moves_reassign and picking.location_id.usage not in ("supplier", "production", "inventory"):
                    # unnecessary to assign other quants than those involved with pack operations as they will be unreserved anyways.
                    picking.with_context(reserve_only_ops=True, no_state_change=True).rereserve_quants(move_ids=picking.move_lines.ids)
                picking.do_recompute_remaining_quantities()

            # split move lines if needed
            for move in picking.move_lines:
                rounding = move.product_id.uom_id.rounding
                remaining_qty = move.remaining_qty
                if move.state in ('done', 'cancel'):
                    # ignore stock moves cancelled or already done
                    continue
                elif move.state == 'draft':
                    toassign_moves |= move
                if float_compare(remaining_qty, 0,  precision_rounding=rounding) == 0:
                    if move.state in ('draft', 'assigned', 'confirmed'):
                        todo_moves |= move
                elif float_compare(remaining_qty, 0, precision_rounding=rounding) > 0 and float_compare(remaining_qty, move.product_qty, precision_rounding=rounding) < 0:
                    # TDE FIXME: shoudl probably return a move - check for no track key, by the way
                    new_move_id = move.split(remaining_qty)
                    new_move = self.env['stock.move'].with_context(mail_notrack=True).browse(new_move_id)
                    todo_moves |= move
                    # Assign move as it was assigned before
                    toassign_moves |= new_move

            # TDE FIXME: do_only_split does not seem used anymore
            if todo_moves and not self.env.context.get('do_only_split'):
                todo_moves.action_done()
            elif self.env.context.get('do_only_split'):
                picking = picking.with_context(split=todo_moves.ids)
            picking._create_backorder()
        return True





















class StockMove(models.Model):
    _inherit = 'stock.move'
    
    @api.multi
    def action_cancel_quant_create(self):
        quant_obj = self.env['stock.quant']
        for move in self:
            price_unit = move.get_price_unit()
            location = move.location_id
            rounding = move.product_id.uom_id.rounding
            vals = {
                'product_id': move.product_id.id,
                'location_id': location.id,
                'qty': float_round(move.product_uom_qty, precision_rounding=rounding),
                'cost': price_unit,
                'in_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'company_id': move.company_id.id,
            }
            quant_obj.sudo().create(vals)
            return
        
    @api.multi
    def action_draft(self):
        res = self.write({'state': 'draft'})
        return res
    




    @api.multi
    def action_cancel(self):
	
        # TDE DUMB: why is cancel_procuremetn in ctx we do quite nothing ?? like not updating the move ??
        procurements = self.env['procurement.order']
        for move in self:
                    
            if move.picking_id.state == 'done':
            	quant_ids = move.quant_ids.ids
                pack_op = self.env['stock.pack.operation'].sudo().search([('picking_id','=',move.picking_id.id),('product_id','=',move.product_id.id)])
                for pack_op_id in pack_op: 
                    if move.picking_id.picking_type_id.code in ['outgoing','internal']:
                        for move_id in quant_ids:
                            quant_id = self.env['stock.quant'].browse(move_id)
                            if pack_op_id.location_dest_id.usage == 'customer':
                                quant_id.write({'location_id':move.location_id.id})
                            else:
                                quant_id = self.env['stock.quant'].browse(move_id)
                                if quant_id.lot_id:
                                    quant_id.write({'location_id':move.location_id.id})
                                else:
                                    quant_id.write({'location_id':move.location_id.id})
                    #incoming
                    if move.picking_id.picking_type_id.code == 'incoming':
                        for move_id in quant_ids:
                            quant_id = self.env['stock.quant'].browse(move_id)
                            for i in quant_id:
                                if i.lot_id:
                                    i.qty = 0.0
                                else:
                                    i.qty = 0.0
        self.sudo().write({'state': 'cancel', 'move_dest_id': False})
        return True



            
