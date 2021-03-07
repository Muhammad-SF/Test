# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    ba_ca_journal_id = fields.Many2one('account.journal', 'Bank/Cash Journal',
        required=True, readonly=True, states={'draft': [('readonly', False)]}, domain=[('type','in',['cash', 'bank'])])

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(AccountVoucher, self).onchange_partner_id()
        if self.voucher_type == 'sale':
            if self.journal_id.default_debit_account_id:
                self.account_id = self.journal_id.default_debit_account_id.id
            else:
                raise UserError(_('Please Define Default Debit Account In Journal'))
        elif self.voucher_type == 'purchase':
            if self.journal_id.default_credit_account_id:
                self.account_id = self.journal_id.default_credit_account_id.id
            else:
                raise UserError(_('Please Define Default Debit Account In Journal'))
        return res

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.voucher_type == 'sale':
            if self.journal_id.default_debit_account_id:
                self.account_id = self.journal_id.default_debit_account_id.id
            else:
                raise UserError(_('Please Define Default Debit Account In Journal'))
        elif self.voucher_type == 'purchase':
            if self.journal_id.default_credit_account_id:
                self.account_id = self.journal_id.default_credit_account_id.id
            else:
                raise UserError(_('Please Define Default Debit Account In Journal'))

    @api.multi
    def extra_entry_first_line(self, move_id, company_currency, current_currency):
        debit = credit = 0.0
        # config_setting = self.env['account.config.settings'].search([], order='id desc', limit=1)
        account_id = self.company_id.transfer_account_id.id
        if self.voucher_type == 'purchase':
            debit = self._convert_amount(self.amount)
        elif self.voucher_type == 'sale':
            credit = self._convert_amount(self.amount)
        elif self.voucher_type == 'sale':
            if self.ba_ca_journal_id.default_debit_account_id:
                account_id = self.ba_ca_journal_id.default_debit_account_id.id
            else:
                raise UserError(_('Please Define Default Debit Account In Journal'))
            debit = self._convert_amount(self.amount)
        if debit < 0.0: debit = 0.0
        if credit < 0.0: credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
            'name': self.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': account_id,
            'move_id': move_id,
            'journal_id': self.ba_ca_journal_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': company_currency != current_currency and current_currency or False,
            'amount_currency': (sign * abs(self.amount) if company_currency != current_currency else 0.0),
            'date': self.account_date,
            'date_maturity': self.date_due
        }
        return move_line

    def extra_entry_move_line_create(self, move_id, company_currency, current_currency):
        debit = credit = 0.0
        account_id = False
        if self.voucher_type == 'purchase':
            if self.journal_id.default_debit_account_id:
                account_id = self.ba_ca_journal_id.default_debit_account_id.id
            else:
                raise UserError(_('Please Define Default Debit Account In Journal'))
            credit = self._convert_amount(self.amount)
        elif self.voucher_type == 'sale':
            if self.journal_id.default_credit_account_id:
                account_id = self.ba_ca_journal_id.default_credit_account_id.id
            else:
                raise UserError(_('Please Define Default Debit Account In Journal'))
            debit = self._convert_amount(self.amount)
        if debit < 0.0:
            debit = 0.0
        if credit < 0.0:
            credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
            'name': self.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': account_id,
            'move_id': move_id,
            'journal_id': self.ba_ca_journal_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': company_currency != current_currency and current_currency or False,
            'amount_currency': (sign * abs(self.amount) if company_currency != current_currency else 0.0),
            'date': self.account_date,
            'date_maturity': self.date_due
        }
        return move_line

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        debit = credit = 0.0
        if self.voucher_type == 'purchase':
            credit = self._convert_amount(self.amount)
        elif self.voucher_type == 'sale':
            debit = self._convert_amount(self.amount)
        if debit < 0.0:
            debit = 0.0
        if credit < 0.0:
            credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        # config_setting = self.env['account.config.settings'].search([], order='id desc', limit=1)
        # set the first line of the voucher
        move_line = {
            'name': self.name or '/',
            'debit': debit,
            'credit': credit,
            # 'account_id': config_setting.transfer_account_id.id,
            'account_id': self.company_id.transfer_account_id.id,
            'move_id': move_id,
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'currency_id': company_currency != current_currency and current_currency or False,
            'amount_currency': (sign * abs(self.amount) if company_currency != current_currency else 0.0),
            'date': self.account_date,
            'date_maturity': self.date_due,
            'payment_id': self._context.get('payment_id'),
        }
        return move_line

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        for line in self.line_ids:
            # create one move line per voucher line where amount is not 0.0
            if not line.price_subtotal:
                continue
            line_subtotal = line.price_subtotal
            if self.voucher_type == 'sale':
                line_subtotal = -1 * line.price_subtotal
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(line_subtotal)
            move_line = {
                'journal_id': self.journal_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': self.partner_id.commercial_partner_id.id,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': abs(amount) if self.voucher_type == 'sale' else 0.0,
                'debit': abs(amount) if self.voucher_type == 'purchase' else 0.0,
                'date': self.account_date,
                'tax_ids': [(4, t.id) for t in line.tax_ids],
                'amount_currency': line_subtotal if current_currency != company_currency else 0.0,
                'currency_id': company_currency != current_currency and current_currency or False,
                'payment_id': self._context.get('payment_id'),
            }
            self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)
        return line_total

    @api.multi
    def proforma_voucher(self):
        res = super(AccountVoucher, self).proforma_voucher()
        local_context = dict(self._context, force_company=self.journal_id.company_id.id)
        ctx = local_context.copy()
        ctx['date'] = self.account_date
        ctx['check_move_validity'] = False
        company_currency = self.journal_id.company_id.currency_id.id
        current_currency = self.currency_id.id or company_currency
        move = self.env['account.move'].create({
            'name': self.ba_ca_journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id(),
            'journal_id': self.ba_ca_journal_id.id,
            'date': self.account_date,
        })
        self.env['account.move.line'].with_context(ctx).create(self.with_context(ctx).extra_entry_first_line(move.id, company_currency, current_currency))
        self.env['account.move.line'].with_context(ctx).create(self.with_context(ctx).extra_entry_move_line_create(move.id, company_currency, current_currency))
        move.post()
        return res

AccountVoucher()