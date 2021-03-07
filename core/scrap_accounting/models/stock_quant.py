# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

class stock_quant(models.Model):
    _inherit = 'stock.quant'

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        # group quants by cost
        quant_cost_qty = defaultdict(lambda: 0.0)

        for quant in self:
            quant_cost_qty[quant.cost] += quant.qty

        AccountMove = self.env['account.move']
        if move.scrapped == True:
            stock_scrap_account_id = move.product_id.stock_scrap_account_id or move.product_id.categ_id.stock_scrap_account_id
            debit_account_id = stock_scrap_account_id.id
        for cost, qty in quant_cost_qty.iteritems():
            move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
            if move_lines:
                date = self._context.get('force_period_date', fields.Date.context_today(self))
                new_account_move = AccountMove.create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': move.picking_id.name})
                new_account_move.post()
