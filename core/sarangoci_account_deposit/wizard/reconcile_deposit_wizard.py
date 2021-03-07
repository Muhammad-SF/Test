
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import Warning


class ReconcileDepositWizard(models.TransientModel):
    _name = 'account.deposit.reconcile'

    @api.model
    def set_invoice_ids(self):
        inv_ids = []
        if self._context and self._context.get('active_id'):
            pay_id = self.env['account.payment'].search([('id', '=', self._context.get('active_id') )])
            if pay_id.partner_type == 'customer':
                inv_ids = self.env['account.invoice'].search([('partner_id', '=', pay_id.partner_id.id), ('state', '=', 'open'), ('type', '=', 'out_invoice')]).ids 
            elif pay_id.partner_type == 'supplier':
                inv_ids = self.env['account.invoice'].search([('partner_id', '=', pay_id.partner_id.id), ('state', '=', 'open'), ('type', '=', 'in_invoice')]).ids 
        return [('id', 'in', inv_ids)]

    date = fields.Date(string='Date', default=fields.Date.context_today)
    invoice_id = fields.Many2one('account.invoice', string="Invoice", domain=set_invoice_ids)

    @api.multi
    def reconcile_deposit(self):
        if self._context and self._context.get('active_id') and self.invoice_id:

            pay_id = self.env['account.payment'].search([('id', '=', self._context.get('active_id') )])
            current_amount = pay_id.remaining_amount and pay_id.remaining_amount or pay_id.amount
            domain = [('id', 'in', pay_id.move_line_ids.ids), ('account_id', '=', pay_id.writeoff_account_id.id), ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.invoice_id.partner_id).id), ('reconciled', '=', False), ('amount_residual', '!=', 0.0)]
            if self.invoice_id.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
            revenue_account = False
            invoice_residual = self.invoice_id.residual
            remaining_amount = pay_id.remaining_amount
            total_remaining = 0.00
            if invoice_residual < remaining_amount:
                revenue_account = True
                total_remaining = remaining_amount - invoice_residual
            else:
                total_remaining = invoice_residual - remaining_amount

            if invoice_residual == self.invoice_id.amount_total:
                residual_tax = self.invoice_id.amount_tax
            elif invoice_residual > self.invoice_id.amount_untaxed:
                residual_tax = invoice_residual - self.invoice_id.amount_untaxed
            else:
                residual_tax = 0

            lines = self.env['account.move.line'].search(domain)
            line_id = pay_id.move_line_ids.search(domain)
            # self.invoice_id.assign_outstanding_credit(line_id.id)

            # jounral 
            # move_id = pay_id.move_line_ids and pay_id.move_line_ids[0].move_id and pay_id.move_line_ids[0].move_id.id or False
            account_move_vals = {
                'journal_id': pay_id.journal_id.id, 
                'date': fields.date.today(),
                'amount': pay_id.remaining_amount,
            }
            move_id = self.env['account.move'].create(account_move_vals)
            if pay_id.partner_type == 'customer':
                account_type_id = self.env['account.account.type'].search([('name', '=', 'Receivable')])
            else:
                account_type_id = self.env['account.account.type'].search([('name', '=', 'Payable')])
            receivable_account_id = self.env['account.account'].search([('user_type_id', '=', account_type_id.id)], limit=1)

            receivable_account_value = {'payment_id': pay_id.id, 
                'name': u'Invoice Reconcile', 
                'invoice_id': False,
                'journal_id': pay_id.journal_id.id, 
                'currency_id': False,
                'amount_currency': False, 
                'partner_id': pay_id.partner_id.commercial_partner_id.id, 
                'move_id': move_id.id}
            if revenue_account:
                if pay_id.payment_type == 'inbound':
                    receivable_account_value.update({
                        'credit': residual_tax,
                        'debit': 0.0,
                        'account_id': receivable_account_id.id })
                elif pay_id.payment_type == 'outbound':
                    receivable_account_value.update({
                        'credit': 0.0,
                        'debit': residual_tax,
                        'account_id': receivable_account_id.id })
#                 account_type_id = self.env['account.account.type'].search([('name', '=', 'Other Income')])
                revenue_account_id = self.env['account.account'].search([('user_type_id', '=', account_type_id.id)], limit=1)

                revenue_account_value = {'payment_id': pay_id.id, 
                    'name': u'Invoice Reconcile', 
                    'invoice_id': False,
                    'journal_id': pay_id.journal_id.id, 
                    'currency_id': False,
                    'amount_currency': False, 
                    'partner_id': pay_id.partner_id.commercial_partner_id.id, 
                    'move_id': move_id.id}
                if pay_id.payment_type == 'inbound':
                    revenue_account_value.update({
                        'credit': invoice_residual - residual_tax or 0.0,
                        'debit': 0.0,
                        'account_id': revenue_account_id.id })
                elif pay_id.payment_type == 'outbound':
                    revenue_account_value.update({
                        'credit': 0.0,
                        'debit':invoice_residual - residual_tax or 0.0,
                        'account_id': revenue_account_id.id })
                move_line_id = self.with_context(check_move_validity=False).env['account.move.line'].create(revenue_account_value)
            else:
                if pay_id.payment_type == 'inbound':
                    receivable_account_value.update({
                        'credit': invoice_residual,
                        'debit': 0.0,
                        'account_id': receivable_account_id.id })
                elif pay_id.payment_type == 'outbound':
                    receivable_account_value.update({
                        'credit': 0.0,
                        'debit':invoice_residual,
                        'account_id': receivable_account_id.id })

            if receivable_account_value.get('credit') != 0 or receivable_account_value.get('debit') != 0:
                move_line_id = self.with_context(check_move_validity=False).env['account.move.line'].create(receivable_account_value)
            self.invoice_id.assign_outstanding_credit(move_line_id.id)

            deposit_account_value = {'payment_id': pay_id.id, 
                'name': u'Invoice Reconcile', 
                'invoice_id': False,
                'journal_id': pay_id.journal_id.id, 
                'currency_id': False,
                'amount_currency': False, 
                'partner_id': pay_id.partner_id.commercial_partner_id.id, 
                'move_id': move_id.id}
            if pay_id.payment_type == 'inbound':
                deposit_account_value.update({
                    'credit': 0.0,   
                    'debit': invoice_residual,
                    'account_id': pay_id.writeoff_account_id.id })
            elif pay_id.payment_type == 'outbound':
                deposit_account_value.update({
                    'credit': invoice_residual,
                    'debit': 0.0,
                    'account_id': pay_id.writeoff_account_id.id})
            move_line_id = self.with_context(check_move_validity=False).env['account.move.line'].create(deposit_account_value)
            move_id.post()
            pay_id.remaining_amount = total_remaining
            if total_remaining == 0.00:
                pay_id.state = 'reconciled'