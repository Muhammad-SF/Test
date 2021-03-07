# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_round
from odoo.exceptions import ValidationError

class ReceiptPaymentCredit(models.Model):
    _inherit = 'receipt.payment.credit'

    @api.multi
    def write(self, values):
        result = super(ReceiptPaymentCredit, self).write(values)
        return result

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        result = []

        for record in self:
            item = super(ReceiptPaymentCredit, record).read(fields, load)[0]
            if record.invoice_id and record.invoice_id.state == 'open':
                if fields and 'amount_unreconciled' in fields:
                    item['amount_unreconciled_currency'] = abs(record.invoice_id.residual)
                    item['amount_unreconciled'] = record.invoice_id.currency_id.with_context(date=record.invoice_id.date_invoice).compute(abs(record.invoice_id.residual), self.env.user.company_id.currency_id, False)
            result.append(item)

        return result

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if not order:
            order =  'invoice_id DESC'
        res = super(ReceiptPaymentCredit, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        exist_bill_ids = []
        new_res = []
        for result in res:
            if result['invoice_id'] and result['invoice_id'][0] not in exist_bill_ids:
                invoice = self.env['account.invoice'].browse(result['invoice_id'][0])
                if invoice.state == 'open':
                    new_res.append(result)
                    exist_bill_ids.append(result['invoice_id'][0])

        res_invoice_ids  = map(lambda x: x['invoice_id'][0], filter(lambda x: x['invoice_id'], res))
        bill_domain      = filter(lambda x: x[0] == 'invoice_id', domain)
        id_domain        = filter(lambda x: x[0] == 'id', domain)
        exist_bills      = self.env['receipt.payment.credit'].browse(id_domain and id_domain[0][2]).mapped('invoice_id')
        res_invoice_ids += exist_bills.ids

        bill_domains = [
            ('id', 'not in', res_invoice_ids),
            ('type', '=', 'in_invoice'),
            ('state', '=', 'open')
        ]
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
                'amount_unreconciled': bill_id.currency_id.with_context(date=bill_id.date_invoice).compute(abs(bill_id.residual), self.env.user.company_id.currency_id, False),
                'amount_unreconciled_currency': abs(bill_id.residual),
                'amount': 0,
            }

            credit = self.env['receipt.payment.credit'].create(vals)
            vals.update({
                'id': credit.id,
                'invoice_id': (bill_id.id, bill_id.display_name),
                'account_id': (bill_id.account_id.id, bill_id.account_id.name),
            })
            length = len(new_res)
            # insert = False
            if length > 0:
                for i in range(length):
                    if vals['invoice_id'][0] < new_res[i]['invoice_id'][0]:
                        new_res[i+1:i+1] = vals
                        break
                if i == length:
                    new_res[i + 1:i + 1] = vals
            pass

        return new_res

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if self.currency_id:
            open_amount = self.move_currency_id.compute(abs(self.amount_unreconciled_currency), self.currency_id, False)
            if open_amount > 0 and float_round(self.amount, 2) > float_round(open_amount, 2):
                raise ValidationError('Allocation amount must be less than or equal to Residual Amount.')