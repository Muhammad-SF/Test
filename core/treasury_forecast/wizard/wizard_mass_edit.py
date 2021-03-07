# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class BankStatementLineMassEdit(models.TransientModel):
    _name = 'bank.statement.line.mass.edit'

    statement_id = fields.Many2one(
        comodel_name='account.bank.statement',
        domain="[('state', '!=', 'confirm')]",
        )
    amount = fields.Float('Amount')

    @api.multi
    def button_edit_data(self):
        """ Upon confirmation data will be edited in all
            bank statement lines selected."""
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for line in self.env['account.bank.statement.line'].browse(active_ids):
            if line.statement_id.state != ('confirm'):
                line.statement_id = self.statement_id.id

        return {"type": "ir.actions.act_window_close"}
