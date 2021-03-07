# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def get_price_unit(self):
        return super(StockMove, self).get_price_unit()

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        result = []
        if not self.env.context.get('from_assemble', False) and not self.env.context.get('from_disassemble', False):
            result = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        return result