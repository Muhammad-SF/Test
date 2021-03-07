# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import amount_to_text_en, float_round
from odoo.exceptions import ValidationError, Warning as UserError
import json


class ReceiptPayment(models.Model):
    _inherit = 'receipt.payment'

    partner_id = fields.Many2one('res.partner', required=False, string='Partner')
    state = fields.Selection(
        [('draft', 'Draft'), ('request_approval', 'Request for Approval'), ('approved', 'Approved'),
         ('cancel', 'Cancelled'), ('in_progress', 'In Progress'), ('posted', 'Paid'), ('rejected', 'Rejected')],
        default='draft', copy=False, track_visibility='onchange', string='Status')
    approver = fields.Many2one('hr.employee', string='Approver')
    is_approver = fields.Boolean(compute='get_is_approver')
    line_cr_strs = fields.Text(string="paymnent credit")
    is_update = fields.Boolean(store=0, default=False)

    def get_is_approver(self):
        self.is_approver = False
        # if self._uid == 1:
        #     self.is_approver = True
        if self.env.user and self.approver and self.env.user.id == self.approver.user_id.id:
            self.is_approver = True

    def request_for_approval(self):
        self.state = 'request_approval'

    def approve_receipt(self):
        self.state = 'approved'

    def reject_receipt(self):
        self.state = 'rejected'

    def prepare_payment_credit_lines(self, credits):
        res = []
        for line_cr in credits:
            res.append([0, 0, {
                'invoice_id': line_cr.invoice_id.id,
                'account_id': line_cr.account_id.id,
                'date': line_cr.date,
                'base_currency_id': line_cr.base_currency_id.id,
                'original_amount': line_cr.original_amount,
                'original_amount_currency': self.currency_id.compute(line_cr.original_amount,
                                                                     line_cr.move_currency_id or line_cr.invoice_id.currency_id,
                                                                     False),
                'amount_unreconciled': line_cr.amount_unreconciled,
                'amount_unreconciled_currency': self.currency_id.compute(line_cr.amount_unreconciled,
                                                                         line_cr.move_currency_id or line_cr.invoice_id.currency_id,
                                                                         False),
                'reconcile': line_cr.reconcile,
                'amount': line_cr.amount,
            }])
        return res

    def validate_data(self, vals):
        amount = sum(map(lambda x: x[2]['amount'] if x[0] == 0 else 0, vals.get('line_cr_ids', [])))
        if (vals.get('amount', 0) or self.amount) < amount:
            raise ValidationError('The amount is invalid!')

    @api.model
    def create(self, vals):
        # if vals.get('line_cr_ids', []):
        #     credits = self.env['receipt.payment.credit'].browse(map(lambda x: x[1], vals.get('line_cr_ids', [])))
        #     vals['line_cr_ids'] = self.prepare_payment_credit_lines(credits)
        # else:
        if vals.get('line_cr_strs', False):
            vals['line_cr_ids'] = json.loads(vals['line_cr_strs'])
        #self.validate_data(vals)
        res = super(ReceiptPayment, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('line_cr_strs', False) and vals.get('line_cr_ids', False):
            vals['line_cr_ids'] = json.loads(vals['line_cr_strs'])
            #self.validate_data(vals)
            del vals['line_cr_strs']
            vals['is_update'] = True
        res = super(ReceiptPayment, self).write(vals)
        return res

    @api.constrains('line_cr_ids', 'currency_id', 'amount')
    @api.onchange('line_cr_ids', 'currency_id', 'amount')
    def onchange_line_cr_ids(self):
        if not self.partner_id and self.type == 'supplier':
            dic = [[5]]
            amount = self.amount
            for line_cr in self.line_cr_ids:

                line_cr.original_amount_currency = self.currency_id.compute(line_cr.original_amount,
                                                                            line_cr.move_currency_id or line_cr.invoice_id.currency_id,
                                                                            False)
                line_cr.amount_unreconciled_currency = self.currency_id.compute(line_cr.amount_unreconciled,
                                                                                line_cr.move_currency_id or line_cr.invoice_id.currency_id,
                                                                                False)
                line_cr.reconcile = min(amount, line_cr.amount_unreconciled_currency) == line_cr.amount_unreconciled_currency
                line_cr.amount = min(amount, line_cr.amount_unreconciled_currency)
                amount -= line_cr.amount
                dic.append([0, 0, {
                    'invoice_id': line_cr.invoice_id.id,
                    'account_id': line_cr.account_id.id,
                    'date': line_cr.date,
                    'base_currency_id': line_cr.base_currency_id.id,
                    'original_amount': line_cr.original_amount,
                    'original_amount_currency': line_cr.original_amount_currency,
                    'amount_unreconciled': line_cr.amount_unreconciled,
                    'amount_unreconciled_currency': line_cr.amount_unreconciled_currency,
                    'reconcile': line_cr.reconcile,
                    'assign_amount': line_cr.amount,
                }])

            if self.line_cr_ids:
                self.line_cr_strs = json.dumps(dic)
            else:
                self.line_cr_ids = json.loads(self.line_cr_strs or '[]')


class ReceiptPaymentCredit(models.Model):
    _inherit = 'receipt.payment.credit'

    assign_amount=fields.Float()
    amount = fields.Monetary(currency_field='currency_id', string='Allocation',compute='_assign_amount')

    @api.multi
    @api.depends('assign_amount')
    def _assign_amount(self):
        for rec in self:
            if rec.assign_amount:
                rec.amount =rec.assign_amount
            else:
                rec.amount=0.0

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if not order:
            order =  'invoice_id DESC'
        res = super(ReceiptPaymentCredit, self).search_read(domain=domain, fields=fields, offset=offset,
                                                            limit=limit, order=order)
        exist_bill_ids = []
        new_res = []
        for result in res:
            if result['invoice_id'][0] not in exist_bill_ids:
                invoice = self.env['account.invoice'].browse(result['invoice_id'][0])
                if invoice.state == 'open':
                    new_res.append(result)
                    exist_bill_ids.append(result['invoice_id'][0])

        res_invoice_ids = map(lambda x: x['invoice_id'][0], res)
        bill_domain = filter(lambda x: x[0] == 'invoice_id', domain)
        id_domain = filter(lambda x: x[0] == 'id', domain)
        exist_bills = self.env['receipt.payment.credit'].browse(id_domain and id_domain[0][2]).mapped('invoice_id')
        res_invoice_ids += exist_bills.ids

        bill_domains = [('id', 'not in', res_invoice_ids), ('type', '=', 'in_invoice'), ('state', '=', 'open')]
        if bill_domain:
            bill_domain[0][0] = 'name'
            bill_domains.append(bill_domain[0])

        new_bill_ids = self.env['account.invoice'].search(bill_domains)
        for bill_id in new_bill_ids:
            vals = {
                'invoice_id': bill_id.id,
                'account_id': bill_id.account_id.id,
                'date': bill_id.date,
                'base_currency_id': self.env.user.company_id.currency_id.id,
                'move_currency_id': bill_id.currency_id.id,
                'original_amount': bill_id.amount_total,
                'original_amount_currency': bill_id.amount_total,
                'amount_unreconciled': bill_id.amount_total,
                'amount_unreconciled_currency': bill_id.amount_total,
                'amount': 0,
            }
            credit = self.env['receipt.payment.credit'].create(vals)
            vals.update({
                'id': credit.id,
                'invoice_id': (bill_id.id, bill_id.display_name),
                'account_id': (bill_id.account_id.id, bill_id.account_id.name),
            })
            new_res.append(vals)

        return new_res

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if self.currency_id:
            open_amount = self.move_currency_id.compute(abs(self.amount_unreconciled_currency), self.currency_id, False)
            if open_amount > 0 and float_round(self.amount, 2) > float_round(open_amount, 2):
                raise ValidationError('Allocation amount must be less than or equal to Residual Amount.')
