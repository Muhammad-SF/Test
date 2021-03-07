# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import amount_to_text_en, float_round
from odoo.exceptions import ValidationError, Warning as UserError
import json


class ReceiptPayment(models.Model):
    _inherit = 'receipt.payment'

    partner_id      = fields.Many2one('res.partner', required=False, string='Partner')
    state           = fields.Selection([
        ('draft', 'Draft'),
        ('request_approval', 'Request for Approval'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
        ('in_progress', 'In Progress'),
        ('posted', 'Paid'),
        ('rejected', 'Rejected')
    ], default='draft', copy=False, track_visibility='onchange', string='Status')
    approver        = fields.Many2one('hr.employee', string='Approver')
    is_approver     = fields.Boolean(compute='get_is_approver')
    line_cr_strs    = fields.Text(string="paymnent credit")
    is_update       = fields.Boolean(store=0, default=False)
    vendor_bill_ids = fields.Many2many('account.invoice', string='Vendor Bill', domain=[('type', '=', 'in_invoice'), ('state', 'in', ['open'])])

    @api.onchange('vendor_bill_ids')
    def onchange_account_id(self):
        self.line_cr_ids = False
        self.line_dr_ids = False
        if self.vendor_bill_ids:
            self.line_cr_ids, self.line_dr_ids = self.load_data()

    @api.multi
    def load_data(self):
        line_cr_lst = []
        line_dr_lst = []
        if not self.partner_id and len(self.vendor_bill_ids.ids) > 0:
            # Query to load the data from account.move.line for Cr and Dr
            base_currency_id = self.company_id.currency_id
            currency_id      = self.currency_id
            query = '''SELECT 
                id as invoice_id,
                state,
                date_invoice as date,
                date_due as date_maturity,
                account_id,
                amount_total as balance,
                type,
                credit_note,
                residual as amount_unreconciled_currency,
                debit_note,
                amount_untaxed as original_amount,
                currency_id as move_currency_id,
                residual_signed as amount_unreconciled,
                amount_total_company_signed as original_amount_currency
            FROM 
                account_invoice 
            WHERE 
                state = 'open'  AND id IN (%s) ''' % (','.join(str(x) for x in self.vendor_bill_ids.ids))
            self.env.cr.execute(query)
            credit_amount = 0.0
            debit_amount  = 0.0
            for result in self.env.cr.dictfetchall():
                invoice_id = self.env['account.invoice'].browse(result['invoice_id'])
                if result['balance'] != 0:
                    if not result['move_currency_id']:
                        result['move_currency_id'] = base_currency_id.id
                    result['residual_balance'] = abs(result['amount_unreconciled_currency'])
                    result['amount_unreconciled'] = invoice_id.currency_id.with_context(
                        date=invoice_id.date_invoice).compute(abs(result['amount_unreconciled_currency']),
                                                              base_currency_id, False)
                    result['amount_unreconciled_currency'] = abs(result['amount_unreconciled_currency'])
                    result['original_amount_currency'] = abs(result['balance'])

                    if invoice_id.type in ['out_invoice', 'in_refund']:
                        original_amount = invoice_id.currency_id.with_context(date=invoice_id.date_invoice).compute(
                            abs(result['balance']), base_currency_id, False)
                        debit_amount += result['amount_unreconciled_currency']
                        result['original_amount'] = original_amount
                        line_dr_lst.append((0, 0, result))

                    elif invoice_id.type in ['out_refund', 'in_invoice']:
                        original_amount = invoice_id.currency_id.with_context(date=invoice_id.date_invoice).compute(
                            abs(result['balance']), base_currency_id, False)
                        credit_amount += result['amount_unreconciled_currency']
                        result['original_amount'] = original_amount
                        line_cr_lst.append((0, 0, result))

            # Code to auto-fill Reconcile and Allocation amount
            dr_index = -1
            cr_index = -1
            if self.type == 'customer':
                credit_amount += self.amount
                # debit_amount = 0.0
                for dr_lst in line_dr_lst:
                    dr_index += 1
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = currency_id.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(
                            abs(credit_amount), invoice_currency_obj, False)
                    if credit_amount > 0:
                        amt = line_dr_lst[dr_index][2]['residual_balance']
                        if amt > credit_amount:
                            amt = credit_amount
                            credit_amount -= amt
                            reconcile = False
                        else:
                            credit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(
                                line_dr_lst[dr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(
                                date=line_dr_lst[dr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        line_dr_lst[dr_index][2].update({'amount': allocation_amount, 'reconcile': reconcile})
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = invoice_currency_obj.with_context(
                            date=line_dr_lst[dr_index][2].get('date')).compute(abs(credit_amount), currency_id, False)

                debit_amount = debit_amount - self.amount if debit_amount > self.amount else 0.00
                for cr_lst in line_cr_lst:
                    cr_index += 1
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = currency_id.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(
                            abs(debit_amount), invoice_currency_obj, False)

                    if debit_amount > 0:
                        amt = line_cr_lst[cr_index][2]['residual_balance']
                        if amt > debit_amount:
                            amt = debit_amount
                            debit_amount -= amt
                            reconcile = False
                        else:
                            debit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(
                                line_cr_lst[cr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(
                                date=line_cr_lst[cr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        line_cr_lst[cr_index][2].update({'amount': allocation_amount, 'reconcile': reconcile})
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = invoice_currency_obj.with_context(
                            date=line_cr_lst[cr_index][2].get('date')).compute(abs(debit_amount), currency_id, False)
            else:
                debit_amount += self.amount
                for cr_lst in line_cr_lst:
                    cr_index += 1
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = currency_id.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(
                            abs(debit_amount), invoice_currency_obj, False)
                    if debit_amount > 0:
                        amt = line_cr_lst[cr_index][2]['residual_balance']
                        if amt > debit_amount:
                            amt = debit_amount
                            debit_amount -= amt
                            reconcile = False
                        else:
                            debit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(
                                line_cr_lst[cr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(
                                date=line_cr_lst[cr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        line_cr_lst[cr_index][2].update({'amount': allocation_amount, 'reconcile': reconcile})
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = invoice_currency_obj.with_context(
                            date=line_cr_lst[cr_index][2].get('date')).compute(abs(debit_amount), currency_id, False)

                credit_amount = credit_amount - self.amount if credit_amount > self.amount else 0.00
                for dr_lst in line_dr_lst:
                    dr_index += 1
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = currency_id.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(
                            abs(credit_amount), invoice_currency_obj, False)
                    if credit_amount > 0:
                        amt = line_dr_lst[dr_index][2]['residual_balance']
                        if amt > credit_amount:
                            amt = credit_amount
                            credit_amount -= amt
                            reconcile = False
                        else:
                            credit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(
                                line_dr_lst[dr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(
                                date=line_dr_lst[dr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        line_dr_lst[dr_index][2].update({'amount': allocation_amount, 'reconcile': reconcile})
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(
                            line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = invoice_currency_obj.with_context(
                            date=line_dr_lst[dr_index][2].get('date')).compute(abs(credit_amount), currency_id, False)
        else:
            line_cr_lst, line_dr_lst = super(ReceiptPayment, self).load_data()
        return line_cr_lst, line_dr_lst

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
                'invoice_id'                   : line_cr.invoice_id.id,
                'account_id'                   : line_cr.account_id.id,
                'date'                         : line_cr.date,
                'base_currency_id'             : line_cr.base_currency_id.id,
                'original_amount'              : line_cr.original_amount,
                'original_amount_currency'     : self.currency_id.compute(line_cr.original_amount, line_cr.move_currency_id or line_cr.invoice_id.currency_id, False),
                'amount_unreconciled'          : line_cr.amount_unreconciled,
                'amount_unreconciled_currency' : self.currency_id.compute(line_cr.amount_unreconciled, line_cr.move_currency_id or line_cr.invoice_id.currency_id, False),
                'reconcile'                    : line_cr.reconcile,
                'amount'                       : line_cr.amount,
            }])
        return res

    def validate_data(self, vals):
        amount = sum(map(lambda x: x[2]['amount'] if x[0] == 0 else 0, vals.get('line_cr_ids', [])))
        if (vals.get('amount', 0) or self.amount) < amount:
            raise ValidationError('The amount is invalid!')

    @api.constrains('line_cr_ids', 'currency_id', 'amount')
    @api.depends('line_cr_ids', 'currency_id', 'amount')
    def onchange_line_cr_ids(self):
        for record in self:
            if not record.partner_id and record.type == 'supplier':
                for line in record.line_cr_ids:
                    line.amount_unreconciled_currency = abs(line.invoice_id.residual)
                    line.amount_unreconciled = line.invoice_id.currency_id.with_context(date=line.invoice_id.date_invoice).compute(abs(line.invoice_id.residual), self.env.user.company_id.currency_id, False)


    @api.model
    def create(self, vals):
        # if vals.get('line_cr_ids', []):
        #     credits = self.env['receipt.payment.credit'].browse(map(lambda x: x[1], vals.get('line_cr_ids', [])))
        #     vals['line_cr_ids'] = self.prepare_payment_credit_lines(credits)
        # else:
        if vals.get('line_cr_strs', False):
            vals['line_cr_ids'] = json.loads(vals['line_cr_strs'])
        self.validate_data(vals)
        res = super(ReceiptPayment, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('line_cr_strs', False) and vals.get('line_cr_ids', False):
            vals['line_cr_ids'] = json.loads(vals['line_cr_strs'])
            self.validate_data(vals)
            del vals['line_cr_strs']
            vals['is_update'] = True
        res = super(ReceiptPayment, self).write(vals)
        return res