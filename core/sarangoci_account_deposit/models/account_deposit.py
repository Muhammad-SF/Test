# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from lxml import etree
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError
import json


class AccountPaymentDeposite(models.Model):
    _inherit = "account.payment"
    _rec_name = 'name'

    is_deposit = fields.Boolean('Is Deposit', default=False)
    is_deposit_return = fields.Boolean('Return Payment')
    deposit_payment_id = fields.Many2one('account.payment', string='Deposit = fie Payment Reference')
    return_payment_reference = fields.Many2many('account.payment', 'account_payment_rel', 'payment_id', 'return_payment_id', String="Return Payments", copy=False)
    amount = fields.Integer('Amount')
    remaining_amount = fields.Integer('Remaining amount')
    account_id = fields.Many2one('account.account','Account')
    
    @api.onchange('amount')
    def onchnage_remaining_amount(self):
        self.remaining_amount = self.amount

    @api.model
    def create(self, vals):
        if vals.get('amount'):
            vals.update({'remaining_amount': vals.get('amount')})
        return super(AccountPaymentDeposite, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('amount'):
            vals.update({'remaining_amount': vals.get('amount')})
        return super(AccountPaymentDeposite, self).write(vals)

    @api.multi
    def button_invoices(self):
        for rec in self:
            inv = self.invoice_ids[0]
            xml_id = (inv.type in ['out_refund', 'out_invoice']) and 'action_invoice_tree1' or \
                (inv.type in ['in_refund', 'in_invoice']) and 'action_invoice_tree2'
            if xml_id:
                result = self.env.ref('account.%s' % (xml_id)).read()[0]
                invoice_domain = safe_eval(result['domain'])
                invoice_domain.append(('id', 'in', [x.id for x in self.invoice_ids]))
                result['domain'] = invoice_domain
                return result

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountPaymentDeposite, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self._context.get('default_is_deposit'):
            doc = etree.XML(res['arch'])
            fields = res.get('fields')
            # arch_data = res.get('arch')
            if fields and res['fields'].get('state') and res['fields']['state'].get('selection') and self._context.get('default_partner_type') == 'customer':
                res['fields']['state']['selection'] = [('draft', 'Draft'), ('posted', 'Received'), ('returned', 'Returned'), ('revenue', 'Converted to Revenue'),  ('reconciled', 'Reconciled')]
            if fields and res['fields'].get('state') and res['fields']['state'].get('selection') and self._context.get('default_partner_type') == 'supplier':
                res['fields']['state']['selection'] = [('draft', 'Draft'), ('posted', 'Paid'), ('returned', 'Received'), ('revenue', 'Converted to Expenses'),  ('reconciled', 'Reconciled')]
        
        return res

    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('returned', 'Returned'), ('revenue', 'Converted to Revenue'), ('reconciled', 'Reconciled')], readonly=True, default='draft', copy=False, string="Status")

    @api.multi
    def convert_revenue(self):
        view = self.env.ref('account_deposit.view_convert_to_revenue')
        context = self.env.context.copy()
        if self.partner_type == 'customer':
            label = 'Convert Revenue'
            context.update({'account_string': 'Revenue Account', 'customer': True})
        else:
            label = 'Convert Expenses'
            context.update({'account_string': 'Expense Account', 'supplier': True})
        return{
            'name': _(label),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'convert.revenue',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }


class AccountMove(models.Model):
    _inherit = "account.move"


    @api.multi
    def assert_balanced(self):
        if self._context.get('deposit_active_id'):
            if not self.ids:
                return True
            prec = self.env['decimal.precision'].precision_get('Account')

            self._cr.execute("""\
                SELECT      move_id
                FROM        account_move_line
                WHERE       move_id in %s
                GROUP BY    move_id
                HAVING      abs(sum(debit) - sum(credit)) > %s
                """, (tuple(self.ids), 10 ** (-max(5, prec))))
            return True
        else:
            return super(AccountMove, self).assert_balanced()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    def create(self, vals):
        if self._context.get('deposit_active_id'):
            deposit_id = self.env['account.payment'].search([('id', '=',  self._context.get('deposit_active_id'))])

            # received amount for customer and suppliers\
            if self._context.get('default_is_deposit') and self._context.get('receive_deposit'): 
                if self._context.get('default_payment_type') == 'inbound' and vals.get('credit'):
                    vals.update({'account_id': deposit_id.writeoff_account_id.id})
                elif self._context.get('default_payment_type') == 'outbound' and vals.get('debit'):
                    vals.update({'account_id': deposit_id.writeoff_account_id.id})
           
            # return deposit for customer and supplier 
            if self._context.get('default_is_deposit') and self._context.get('return_deposit'):
                return_payment_id = self.env['account.payment'].search([('id', '=',  self._context.get('return_payment_id'))])                
                if self._context.get('return_payment_create') and deposit_id.payment_type  == 'inbound' and vals.get('debit'):
                    vals.update({'account_id': deposit_id.writeoff_account_id.id})
                elif  self._context.get('return_payment_create') and deposit_id.payment_type == 'outbound' and vals.get('credit'):                    
                    vals.update({'account_id': deposit_id.writeoff_account_id.id})

                if deposit_id.remaining_amount != self._context.get('return_amount') and self._context.get('return_payment_create'):
                    return_dep_id = self.env['account.payment'].search([('id', '=',  vals.get('payment_id'))])
                    
                    if return_dep_id.payment_type  == 'inbound' and vals.get('debit'):
                        vals.update({'debit': self._context.get('return_amount')})
                    elif return_dep_id.payment_type == 'outbound' and vals.get('credit'):                    
                        vals.update({'credit': self._context.get('return_amount')})

                if return_payment_id and return_payment_id.payment_type == 'inbound' and vals.get('debit'):
                    vals.update({'debit': deposit_id.remaining_amount - self._context.get('return_amount')})
                elif return_payment_id and return_payment_id.payment_type == 'outbound' and vals.get('credit'):                    
                    vals.update({'credit': deposit_id.remaining_amount - self._context.get('return_amount')})
                
        res = super(AccountMoveLine, self).create(vals)
        return res

    @api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        # Empty self can happen if the user tries to reconcile entries which are already reconciled.
        # The calling method might have filtered out reconciled lines.
        if self._context.get('deposit_active_id'):

            if not self:
                return True

            #Perform all checks on lines
            company_ids = set()
            all_accounts = []
            partners = set()
            for line in self:
                company_ids.add(line.company_id.id)
                all_accounts.append(line.account_id)
                if (line.account_id.internal_type in ('receivable', 'payable')):
                    partners.add(line.partner_id.id)
                if line.reconciled:
                    raise UserError(_('You are trying to reconcile some entries that are already reconciled!'))
            if len(company_ids) > 1:
                raise UserError(_('To reconcile the entries company should be the same for all entries!'))
            # if len(set(all_accounts)) > 1:
                # raise UserError(_('Entries are not of the same account!'))
            if not all_accounts[0].reconcile:
                raise UserError(_('The account %s (%s) is not marked as reconciliable !') % (all_accounts[0].name, all_accounts[0].code))
            if len(partners) > 1:
                raise UserError(_('The partner has to be the same on all lines for receivable and payable accounts!'))

            #reconcile everything that can be
            remaining_moves = self.auto_reconcile_lines()

            #if writeoff_acc_id specified, then create write-off move with value the remaining amount from move in self
            if writeoff_acc_id and writeoff_journal_id and remaining_moves:
                all_aml_share_same_currency = all([x.currency_id == self[0].currency_id for x in self])
                writeoff_vals = {
                    'account_id': writeoff_acc_id.id,
                    'journal_id': writeoff_journal_id.id
                }
                if not all_aml_share_same_currency:
                    writeoff_vals['amount_currency'] = False
                writeoff_to_reconcile = remaining_moves._create_writeoff(writeoff_vals)
                #add writeoff line to reconcile algo and finish the reconciliation
                remaining_moves = (remaining_moves + writeoff_to_reconcile).auto_reconcile_lines()
                return writeoff_to_reconcile
            return True
        else:
            super(AccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def name_get(self):
        if self._context.get('deposit_reconcile'):
            res = []
            for invoice in self:
                res.append((invoice.id, '%s - %s %s' % (invoice.number, invoice.currency_id.symbol, "%.2f" % invoice.residual)))
            return res
        else:
            return super(AccountInvoice, self).name_get()

AccountInvoice()