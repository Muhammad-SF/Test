# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, SUPERUSER_ID, _
from datetime import datetime

class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(sale_order, self).onchange_partner_id()
        values = {}
        if self.partner_id and self.partner_id.id:
            values['is_consignment'] = False
            if self.partner_id.is_consignment:
                values['warehouse_id'] = self.partner_id.consignment_wh.id
                values['is_consignment'] = True
        self.update(values)
        return res

class force_done(models.Model):
    _name = 'force.done'

    @api.model
    def invoice_pay_customer(self, invoice_id):
        return {
            'name': _('Register Payment'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_account_payment_invoice_form').id,
            'view_type': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_invoice_ids': [(4, invoice_id, None)],
            }
        }

    @api.model
    def invoice_paid(self, invoice_id):
        voucher_obj = self.env.get('account.voucher')
        voucher_line_obj = self.env.get('account.voucher.line')
        invoice_obj = self.env.get('account.invoice').sudo().browse(invoice_id)

        date = datetime.now().strftime('%Y-%m-%d')
        journals = self.env.get('account.journal').search([('type', '=','bank')], limit=1)
        journal_id = journals.ids[0]
        amount = invoice_obj.amount_total
        partner_id = invoice_obj.partner_id.id


        res1 = self.invoice_pay_customer(invoice_id)
        ctx = res1['context']
        fields = ['type','date','journal_id', 'account_id', 'period_id', 'narration','company_id', 'amount','reference','partner_id','payment_option','payment_rate_currency_id','payment_rate']
        statement_vals = self.env.get('account.voucher').sudo().default_get(fields)

        # data = voucher_obj.onchange_partner_id(cr, uid, [], partner_id, journal_id, amount, False, 'payment', date, context)['value']
        invoice_name = invoice_obj.number
        # for line_cr in data.get('line_cr_ids'):
        #     if line_cr['name']==invoice_name:
        #         amount=line_cr['amount_original']
        # account_id = data['account_id']
        statement_vals.update({
            'reference': invoice_name,
            'journal_id': journal_id,
            'amount': amount,
            'date' : date,
            'partner_id': partner_id,
            # 'payment_option':'with_writeoff'
        })
        # raise osv.except_osv(_('Error!'),_('statement_id=%s...%s')%(statement_vals, invoice_id))
        # if data.get('payment_rate_currency_id'):
        #     statement_vals['payment_rate_currency_id'] = data['payment_rate_currency_id']
        #     company_currency_id=self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        #     if company_currency_id<>data['payment_rate_currency_id']:
        #         statement_vals['is_multi_currency']=True
        # if data.get('paid_amount_in_company_currency'):
        #     statement_vals['paid_amount_in_company_currency'] = data['paid_amount_in_company_currency']
        # if data.get('writeoff_amount'):
        #     statement_vals['writeoff_amount'] =data['writeoff_amount']
        # if data.get('pre_line'):
        #     statement_vals['pre_line'] = data['pre_line']
        # if data.get('payment_rate'):
        #     statement_vals['payment_rate'] = data['payment_rate']

        statement = voucher_obj.create(statement_vals)
        statement.onchange_partner_id()
        # for line_cr in data.get('line_cr_ids'):
        #     line_cr.update({'voucher_id':statement_id})
        #     line_cr_id=self.pool.get('account.voucher.line').create(cr,uid,line_cr)
        # for line_dr in data.get('line_dr_ids'):
        #     line_dr.update({'voucher_id':statement_id})
        #     if line_dr['name']==invoice_name:
        #         line_dr['amount']=line_dr['amount_original']
        #         line_dr['reconcile']=True
        #     line_dr_id=self.pool.get('account.voucher.line').create(cr,uid,line_dr)
        statement.proforma_voucher()
        # raise osv.except_osv(_('Error!'),_('statement_id=%s...%s')%(statement_id, invoice_id))
        # self.pool.get('account.voucher').button_proforma_voucher(cr, uid, [statement_id], context=context)
        return True

    @api.model
    def order_paid111(self, invoice_id):
        invoice = self.env.get('account.invoice').sudo().browse(invoice_id)
        voucher_obj = self.env.get('account.voucher')
        res = self.invoice_pay_customer(invoice_id)
        ctx = res['context']
        # context_copy.update(ctx)
        fields = ['type','date','journal_id', 'account_id', 'period_id', 'narration','company_id', 'amount','reference','partner_id','payment_option','payment_rate_currency_id','payment_rate'
            # 'line_ids',
            # 'line_cr_ids',
            # 'line_dr_ids',           
            # 'state',
            # 'tax_amount',            
            # 'number',
            # 'move_id',
            # 'pay_now',
            # 'tax_id',
            # 'pre_line',
            # 'date_due',            
            # 'writeoff_acc_id',
            # 'comment',
            # 'analytic_id',
        ]
        default_vals = self.env.get('account.voucher').sudo().default_get(fields)
        journals = self.env.get('account.journal').search([('type', '=','bank')], limit=1)
        default_vals.update({
            'journal_id': journals.ids[0],
        })
        voucher = self.env.get('account.voucher').create(default_vals)
        voucher.onchange_partner_id()
        voucher.proforma_voucher()

    @api.model
    def order_shipped(self, order_id):
        order = self.env.get('sale.order').browse(order_id)
        if order.picking_ids:
            order.picking_ids.do_transfer()
        return True