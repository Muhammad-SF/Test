# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    is_return = fields.Boolean('Returned')
    return_date = fields.Datetime('Returned Date')
    return_reason = fields.Char('Return Reason')
    remarks = fields.Char('Remarks')

stock_picking()

class stock_return_picking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        # TDE FIXME: store it in the wizard, stupid
        picking = self.env['stock.picking'].browse(self.env.context['active_id'])

        return_moves = self.product_return_moves.mapped('move_id')
        unreserve_moves = self.env['stock.move']
        for move in return_moves:
            to_check_moves = self.env['stock.move'] | move.move_dest_id
            while to_check_moves:
                current_move = to_check_moves[-1]
                to_check_moves = to_check_moves[:-1]
                if current_move.state not in ('done', 'cancel') and current_move.reserved_quant_ids:
                    unreserve_moves |= current_move
                split_move_ids = self.env['stock.move'].search([('split_from', '=', current_move.id)])
                to_check_moves |= split_move_ids

        if unreserve_moves:
            unreserve_moves.do_unreserve()
            # break the link between moves in order to be able to fix them later if needed
            unreserve_moves.write({'move_orig_ids': False})

        # create new picking for returned products
        picking_type_id = picking.picking_type_id.return_picking_type_id.id or picking.picking_type_id.id


        returned_lines = 0
        for return_line in self.product_return_moves:
            new_picking = picking.copy({
                'move_lines': [],
                'picking_type_id': picking_type_id,
                'state': 'draft',
                'origin': picking.name,
                'is_return': True,
                'return_date': datetime.now(),
                'return_reason': return_line.return_reason.name if return_line.return_reason and return_line.return_reason.name else '',
                'remarks': self.remarks if self.remarks else '',
                'location_id': picking.location_dest_id.id,
                'location_dest_id': self.location_id.id})
            new_picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': new_picking, 'origin': picking},
                                               subtype_id=self.env.ref('mail.mt_note').id)
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed"))
            new_qty = return_line.quantity
            if new_qty:
                # The return of a return should be linked with the original's destination move if it was not cancelled
                if return_line.move_id.origin_returned_move_id.move_dest_id.id and return_line.move_id.origin_returned_move_id.move_dest_id.state != 'cancel':
                    move_dest_id = return_line.move_id.origin_returned_move_id.move_dest_id.id
                else:
                    move_dest_id = False

                returned_lines += 1
                return_line.move_id.copy({
                    'product_id': return_line.product_id.id,
                    'product_uom_qty': new_qty,
                    'picking_id': new_picking.id,
                    'state': 'draft',
                    'location_id': return_line.move_id.location_dest_id.id,
                    'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
                    'picking_type_id': picking_type_id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                    'origin_returned_move_id': return_line.move_id.id,
                    'procure_method': 'make_to_stock',
                    'move_dest_id': move_dest_id,
                })

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

stock_return_picking()

class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.depends('product_uom_qty')
    def compute_return_qty(self):
        for record in self:
            total_qty = 0.0
            for line in record.picking_id.move_lines:
                total_qty += line.product_uom_qty
            record.return_qty_percentage = total_qty and ((record.product_uom_qty / total_qty) * 100) or 0.00

    return_reason = fields.Char(related='picking_id.return_reason', store=True)
    return_qty_percentage = fields.Float('Return Qty %', compute='compute_return_qty', store=True)
    is_return = fields.Boolean(related='picking_id.is_return', string='Is Return', store=True)
    remarks = fields.Char(related='picking_id.remarks', string='Remarks', store=True)
    partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', string='Partner', store=True)

stock_move()