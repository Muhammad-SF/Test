# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_assign(self):
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if moves and self.filtered(lambda picking: picking.state in ('confirmed','waiting')):
            moves.write({'reserved_by_id': self.env.user.id, 'is_reserved': True})
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        moves.action_assign()
        return True

stock_picking()