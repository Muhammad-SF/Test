# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    @api.depends('tax_correction', 'line_ids.price_subtotal')
    def _compute_total(self):
        for voucher in self:
            total = 0
            tax_amount = 0
            for line in voucher.line_ids:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                tax_info = line.tax_ids.compute_all(price, voucher.currency_id, line.quantity, line.product_id, voucher.partner_id)
                total += tax_info.get('total_included', 0.0)
                tax_amount += sum([t.get('amount',0.0) for t in tax_info.get('taxes', False)])
            voucher.amount = total + voucher.tax_correction
            voucher.tax_amount = tax_amount

    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
        readonly=True, states={'draft': [('readonly', False)]})
    permit_number = fields.Char('Permit Number')
    cheque_no = fields.Char(string="Cheque No")
    attention = fields.Char(string="Attention")

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        for line in self.line_ids:
            #create one move line per voucher line where amount is not 0.0
            if not line.price_subtotal:
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount((line.price_unit * (1 - (line.discount or 0.0) / 100.0)) *line.quantity)
            move_line = {
                'journal_id': self.journal_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': self.partner_id.id,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': abs(amount) if self.voucher_type == 'sale' else 0.0,
                'debit': abs(amount) if self.voucher_type == 'purchase' else 0.0,
                'date': self.account_date,
                'tax_ids': [(4,t.id) for t in line.tax_ids],
                'amount_currency': line.price_subtotal if current_currency != company_currency else 0.0,
                'currency_id': company_currency != current_currency and current_currency or False,
            }

            self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)
        return line_total

AccountVoucher()

class AccountVoucherLine(models.Model):
    _inherit = 'account.voucher.line'

    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    @api.one
    @api.depends('price_unit', 'tax_ids', 'discount', 'quantity', 'product_id', 'voucher_id.currency_id')
    def _compute_subtotal(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        self.price_subtotal = self.quantity * price
        if self.tax_ids:
            taxes = self.tax_ids.compute_all(price, self.voucher_id.currency_id, self.quantity, product=self.product_id, partner=self.voucher_id.partner_id)
            self.price_subtotal = taxes['total_excluded']

AccountVoucherLine()