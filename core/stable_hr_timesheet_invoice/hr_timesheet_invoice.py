# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time

from odoo import fields, models, exceptions, api
from odoo.tools.translate import _

class hr_timesheet_invoice_factor(models.Model):
    _name = 'hr_timesheet_invoice.factor'
    _description = 'Invoice Rate'
    _order = 'factor'

    name          = fields.Char('Internal Name', required=True, translate=True)
    customer_name = fields.Char('Name', help="Label for the customer")
    factor        = fields.Float('Discount (%)', required=True, help="Discount in percentage", default=0.0)

class account_analytic_account(models.Model):

    @api.multi
    def _invoiced_calc(self):
        obj_invoice = self.env['account.invoice']
        self.env.cr.execute('SELECT l.account_id as account_id, l.invoice_id '
                            'FROM account_analytic_line l '
                            'WHERE l.account_id IN (%s)', (self._ids,))
        account_to_invoice_map = {}
        for rec in self.env.cr.dictfetchall():
            account_to_invoice_map.setdefault(rec['account_id'], []).append(rec['invoice_id'])

        for account in self:
            invoice_ids = filter(None, list(set(account_to_invoice_map.get(account.id, []))))
            amount_invoiced = 0.0
            for invoice in obj_invoice.browse(invoice_ids):
                amount_invoiced += invoice.amount_untaxed
            amount_invoiced         = round(amount_invoiced, 2)
            account.amount_invoiced = amount_invoiced

    _inherit = 'account.analytic.account'

    pricelist_id    = fields.Many2one('product.pricelist', 'Pricelist',
                                      help="The product to invoice is defined on the employee form, the price will be deducted by this pricelist on the product.")
    amount_max      = fields.Float('Max. Invoice Price',
                                   help="Keep empty if this contract is not limited to a total fixed price.")
    amount_invoiced = fields.Float(compute=_invoiced_calc, string='Invoiced Amount',
                                   help="Total invoiced")
    to_invoice      = fields.Many2one('hr_timesheet_invoice.factor', 'Timesheet Invoicing Ratio',
                                      help="You usually invoice 100% of the timesheets. But if you mix fixed price and timesheet invoicing, you may use another ratio. For instance, if you do a 20% advance invoice (fixed price, based on a sales order), you should invoice the rest on timesheet with a 80% ratio.")

    @api.onchange('partner_id')
    def on_change_partner_id(self):
        # res = super(account_analytic_account, self).on_change_partner_id()
        for record in self:
            if record.partner_id and record.partner_id.id:
                part = record.partner_id
                pricelist = part.property_product_pricelist and part.property_product_pricelist.id or False
                if pricelist:
                    record.pricelist_id = pricelist
        # return res

    @api.multi
    def set_close(self):
        return self.write({'state': 'close'})

    @api.multi
    def set_cancel(self):
        return self.write({'state': 'cancelled'})

    @api.multi
    def set_open(self):
        return self.write({'state': 'open'})

    @api.multi
    def set_pending(self):
        return self.write({'state': 'pending'})

class account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'

    invoice_id = fields.Many2one('account.invoice', 'Invoice', ondelete="set null", copy=False)
    to_invoice = fields.Many2one('hr_timesheet_invoice.factor', 'Invoiceable',
                                 help="It allows to set the discount while making invoice, keep empty if the activities should not be invoiced.")
    general_account_id = fields.Many2one('account.account', compute='compute_general_account_id', string='Financial Account', ondelete='restrict', readonly=True, domain=[('deprecated', '=', False)])

    @api.multi
    def compute_general_account_id(self):
        for record in self:
            if record.move_id and record.move_id.account_id:
                record.general_account_id = record.move_id.account_id
            else:
                employee_obj = self.env['hr.employee']
                employees    = employee_obj.search([('user_id', '=', self.env.uid)], limit=1)
                if employees:
                    employee = employees[0]
                    if employee.product_id and employee.product_id.property_account_income_id:
                        record.general_account_id = employee.product_id.property_account_income_id
                    else:
                        record.general_account_id = employee.product_id.categ_id.property_account_income_categ_id.id

    @api.multi
    def write(self, vals):
        self._check_inv(vals)
        return super(account_analytic_line, self).write(vals)

    @api.multi
    def _check_inv(self, vals):
        if ( not vals.has_key('invoice_id')) or vals['invoice_id' ] == False:
            for line in self:
                if line.invoice_id:
                    raise exceptions.Warning(_('Error!'),
                        _('You cannot modify an invoiced analytic line!'))
        return True

    @api.model
    def _get_invoice_price(self, account, product_id, user_id, qty):
        price = 0.0
        if account.pricelist_id:
            # TODO: Fixed the list
            result = account.pricelist_id.price_get(product_id, qty or 1.0, account.partner_id.id)
            if result:
                price = result.get(account.pricelist_id and account.pricelist_id.id, 0.0)
        return price

    @api.model
    def _prepare_cost_invoice(self, partner, company_id, currency_id, analytic_lines):
        """ returns values used to create main invoice from analytic lines"""
        account_payment_term_obj = self.env['account.payment.term']
        invoice_name = analytic_lines[0].account_id.name

        date_due = False
        if partner.property_payment_term_id:
            pterm_list = account_payment_term_obj.compute(partner.property_payment_term_id.id, value=1, date_ref=time.strftime('%Y-%m-%d'))
            if pterm_list:
                pterm_list = [line[0] for line in pterm_list]
                pterm_list.sort()
                date_due = pterm_list[-1]

        return {
            'name': "%s - %s" % (time.strftime('%d/%m/%Y'), invoice_name),
            'partner_id': partner.id,
            'company_id': company_id,
            'payment_term': partner.property_payment_term_id.id or False,
            'account_id': partner.property_account_receivable_id.id,
            'currency_id': currency_id,
            'date_due': date_due,
            'fiscal_position': partner.property_account_position_id.id
        }

    @api.model
    def _prepare_cost_invoice_line(self, invoice_id, product_id, uom, user_id,
                factor_id, account, analytic_lines, journal_type, data, context=None):
        product_obj = self.env['product.product']

        uom_context = dict(context or {}, uom=uom)

        total_price = sum(l.amount for l in analytic_lines)
        total_qty   = sum(l.unit_amount for l in analytic_lines)

        if data.get('product'):
            # force product, use its public price
            if isinstance(data['product'], (tuple, list)):
                product_id = data['product'][0]
            else:
                product_id = data['product']
            unit_price = self._get_invoice_price(account, product_id, user_id, total_qty, uom_context)
        elif journal_type == 'general' and product_id:
            # timesheets, use sale price
            unit_price = self._get_invoice_price(account, product_id, user_id, total_qty, uom_context)
        else:
            # expenses, using price from amount field
            unit_price = total_price*-1.0 / total_qty

        factor = self.env['hr_timesheet_invoice.factor'].browse(factor_id)
        factor_name = factor.customer_name or ''
        curr_invoice_line = {
            'price_unit' : unit_price,
            'quantity'   : total_qty,
            'product_id' : product_id,
            'discount'   : factor.factor,
            'invoice_id' : invoice_id,
            'name'       : factor_name,
            'uos_id'     : uom,
            'account_analytic_id': account.id,
        }

        if product_id:
            product = product_obj.browse(product_id)
            factor_name = product_obj.name_get([product_id])[0][1]
            if factor.customer_name:
                factor_name += ' - ' + factor.customer_name

            general_account = product.property_account_income or product.categ_id.property_account_income_categ
            if not general_account:
                raise exceptions.Warning(_('Error!'), _("Configuration Error!") + '\n' + _("Please define income account for product '%s'.") % product.name)
            taxes = product.taxes_id or general_account.tax_ids
            tax = self.env['account.fiscal.position'].map_tax(account.partner_id.property_account_position, taxes, context=context)
            curr_invoice_line.update({
                'invoice_line_tax_id': [(6, 0, tax)],
                'name'       : factor_name,
                'account_id' : general_account.id,
            })

            note = []
            for line in analytic_lines:
                # set invoice_line_note
                details = []
                if data.get('date', False):
                    details.append(line['date'])
                if data.get('time', False):
                    if line['product_uom_id']:
                        details.append("%s %s" % (line.unit_amount, line.product_uom_id.name))
                    else:
                        details.append("%s" % (line['unit_amount'], ))
                if data.get('name', False):
                    details.append(line['name'])
                if details:
                    note.append(u' - '.join(map(lambda x: unicode(x) or '', details)))
            if note:
                curr_invoice_line['name'] += "\n" + ("\n".join(map(lambda x: unicode(x) or '', note)))
        return curr_invoice_line

    @api.multi
    def invoice_cost_create(self, data=None):
        invoice_obj = self.env['account.invoice']
        invoice_line_obj = self.env['account.invoice.line']
        analytic_line_obj = self.env['account.analytic.line']
        invoices = []

        if data is None:
            data = {}

        # use key (partner/account, company, currency)
        # creates one invoice per key
        invoice_grouping = {}

        currency_id = False
        # prepare for iteration on journal and accounts
        for line in self:

            key = (line.account_id.id,
                   line.account_id.company_id.id,
                   line.account_id.pricelist_id.currency_id.id)
            invoice_grouping.setdefault(key, []).append(line)

        for (key_id, company_id, currency_id), analytic_lines in invoice_grouping.items():
            # key_id is an account.analytic.account
            account = analytic_lines[0].account_id
            partner = account.partner_id  # will be the same for every line
            if (not partner) or not (currency_id):
                raise exceptions.Warning(_('Error!'), _('Contract incomplete. Please fill in the Customer and Pricelist fields for %s.') % (account.name))

            curr_invoice = self._prepare_cost_invoice(partner, company_id, currency_id, analytic_lines)
            last_invoice = invoice_obj.with_context({
                'lang'          : partner.lang,
                'force_company' : company_id,  # set force_company in context so the correct product properties are selected (eg. income account)
                'company_id'    : company_id,
            }).create(curr_invoice)
            invoices.append(last_invoice)

            # use key (product, uom, user, invoiceable, analytic account, journal type)
            # creates one invoice line per key
            invoice_lines_grouping = {}
            for analytic_line in analytic_lines:
                account = analytic_line.account_id

                if not analytic_line.to_invoice:
                    raise exceptions.Warning(_('Trying to invoice non invoiceable line for %s.') % (analytic_line.product_id.name))

                key = (analytic_line.product_id.id,
                       analytic_line.product_uom_id.id,
                       analytic_line.user_id.id,
                       analytic_line.to_invoice.id,
                       analytic_line.account_id)
                # We want to retrieve the data in the partner language for the invoice creation
                analytic_line = analytic_line_obj.browse([line.id for line in analytic_line])
                invoice_lines_grouping.setdefault(key, []).append(analytic_line)

            # finally creates the invoice line
            for (product_id, uom, user_id, factor_id, account), lines_to_invoice in invoice_lines_grouping.items():
                curr_invoice_line = self._prepare_cost_invoice_line(last_invoice,
                    product_id, uom, user_id, factor_id, account, lines_to_invoice, data)

                invoice_line_obj.create(curr_invoice_line)
            analytic_lines.write({'invoice_id': last_invoice})
            last_invoice.button_reset_taxes()
        return invoices

# class hr_analytic_timesheet(models.Model):
#     _inherit = "hr.analytic.timesheet"
#     def on_change_account_id(self, cr, uid, ids, account_id, user_id=False):
#         res = super(hr_analytic_timesheet, self).on_change_account_id(
#             cr, uid, ids, account_id, context=user_id)
#         if not account_id:
#             return res
#         res.setdefault('value',{})
#         acc = self.pool.get('account.analytic.account').browse(cr, uid, account_id)
#         st = acc.to_invoice.id
#         res['value']['to_invoice'] = st or False
#         if acc.state=='pending':
#             res['warning'] = {
#                 'title': _('Warning'),
#                 'message': _('The analytic account is in pending state.\nYou should not work on this account !')
#             }
#         return res

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_analytic_lines(self):
        iml = super(account_invoice, self)._get_analytic_lines()

        inv = self[0]
        if inv.type == 'in_invoice':
            obj_analytic_account = self.env['account.analytic.account']
            for il in iml:
                if il['account_analytic_id']:
                    # *-* browse (or refactor to avoid read inside the loop)
                    account_analytic = obj_analytic_account.browse(il['account_analytic_id'])
                    il['analytic_lines'][0][2]['to_invoice'] = account_analytic.to_invoice
        return iml

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def create_analytic_lines(self):
        res = super(account_move_line, self).create_analytic_lines()
        for move_line in self:
            #For customer invoice, link analytic line to the invoice so it is not proposed for invoicing in Bill Tasks Work
            invoice_id = move_line.invoice_id and move_line.invoice_id.type in ('out_invoice','out_refund') and move_line.invoice_id.id or False
            for line in move_line.analytic_line_ids:
                line.write({
                    'invoice_id': invoice_id,
                    'to_invoice': line.account_id.to_invoice and line.account_id.to_invoice.id or False
                })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
