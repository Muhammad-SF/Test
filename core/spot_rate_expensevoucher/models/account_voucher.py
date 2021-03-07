# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.depends('journal_id')
    def compute_spot_rate_check(self):
        for record in self:
            if record.journal_id and record.journal_id.currency_id:
                if record.company_id.currency_id != record.journal_id.currency_id:
                    record.spot_rate_check = True

    spot_rate_check = fields.Boolean(compute='compute_spot_rate_check', string='Spot Rate Check')
    spot_rate = fields.Float('Spot Rate')

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        if self.spot_rate != 0.0:
            debit = credit = 0.0
            rate = self.amount * self.spot_rate
            if self.voucher_type == 'purchase':
                credit = rate
            elif self.voucher_type == 'sale':
                debit = rate
            if debit < 0.0: debit = 0.0
            if credit < 0.0: credit = 0.0
            sign = debit - credit < 0 and -1 or 1

            # set the first line of the voucher
            move_line = {
                'name': self.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': self.account_id.id,
                'move_id': move_id,
                'journal_id': self.journal_id.id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'currency_id': company_currency != current_currency and current_currency or False,
                'amount_currency': (sign * abs(self.amount)  # amount < 0 for refunds
                                    if company_currency != current_currency else 0.0),
                'date': self.account_date,
                'date_maturity': self.date_due,
                'payment_id': self._context.get('payment_id'),
            }
        else:
            move_line = super(AccountVoucher, self).first_move_line_get(move_id, company_currency, current_currency)
        return move_line

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        for line in self.line_ids:
            if line.voucher_id.spot_rate != 0.0:
                # create one move line per voucher line where amount is not 0.0
                if not line.price_subtotal:
                    continue
                line_subtotal = line.price_subtotal
                if self.voucher_type == 'sale':
                    line_subtotal = -1 * line.price_subtotal
                # convert the amount set on the voucher line into the currency of the voucher's company
                # this calls res_curreny.compute() with the right context,
                # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
                amount = line.price_unit * line.quantity
                rate = amount * line.voucher_id.spot_rate
                move_line = {
                    'journal_id': self.journal_id.id,
                    'name': line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': self.partner_id.commercial_partner_id.id,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': abs(rate) if self.voucher_type == 'sale' else 0.0,
                    'debit': abs(rate) if self.voucher_type == 'purchase' else 0.0,
                    'date': self.account_date,
                    'tax_ids': [(4, t.id) for t in line.tax_ids],
                    'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
                    'currency_id': company_currency != current_currency and current_currency or False,
                    'payment_id': self._context.get('payment_id'),
                }
                self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)
            else:
                super(AccountVoucher, self).voucher_move_line_create(line_total, move_id, company_currency, current_currency)
        return line_total

AccountVoucher()