# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # @api.one
    # @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'type')
    # def _compute_amount(self):
    #     round_curr = self.currency_id.round
    #     self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
    #     self.amount_tax = sum(round_curr(line.amount) for line in self.tax_line_ids)
    #     amountss = 0.0
    #     amountadd = 0.0   
    #     if self.tax_line_ids:
    #         for line in self.tax_line_ids:
    #             if line.tax_id.price_include_total:
    #                 amountss += round_curr(line.amount)
    #             elif line.tax_id.price_include:
    #                 amountadd += round_curr(line.amount)
    #                 self.amount_untaxed = self.amount_untaxed - amountadd
    #             else:
    #                 amountadd += round_curr(line.amount)
    #             self.amount_total = self.amount_untaxed + amountadd - amountss
    #     else:
    #         self.amount_total = self.amount_untaxed + self.amount_tax
    #     amount_total_company_signed = self.amount_total
    #     amount_untaxed_signed = self.amount_untaxed
    #     if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
    #         currency_id = self.currency_id.with_context(date=self.date_invoice)
    #         amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
    #         amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
    #     sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
    #     self.amount_total_company_signed = amount_total_company_signed * sign
    #     self.amount_total_signed = self.amount_total * sign
    #     self.amount_untaxed_signed = amount_untaxed_signed * sign


    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if line.quantity==0:
                continue
            tax_ids = []
            in_amount = 0.0 
            un_amount = 0.0 

            round_curr = self.currency_id.round
            for tax in line.invoice_line_tax_ids:
                # if tax.price_include_total:
                #     in_amount += line.price_subtotal * tax.amount / 100
                #     line.price_subtotal -= in_amount
                # else:
                #     un_amount += line.price_subtotal
                #     line.price_subtotal = un_amount

                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))

            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
            
            move_line_dict = {
            'invl_id': line.id,
            'type': 'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'price': line.price_subtotal,
            'account_id': line.account_id.id,
            'product_id': line.product_id.id,
            'uom_id': line.uom_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            'tax_ids': tax_ids,
            'invoice_id': self.id,
            'analytic_tag_ids': analytic_tag_ids
            }
            
            res.append(move_line_dict)
        return res

    @api.model
    def tax_line_move_line_get(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount:
                tax = tax_line.tax_id
                if tax.amount_type == "group":
                    for child_tax in tax.children_tax_ids:
                        done_taxes.append(child_tax.id)
                        
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount,
                    'quantity': 1,
                    'price': tax_line.amount,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'invoice_id': self.id,
                    'tax_ids': [(6, 0, list(done_taxes))] if tax_line.tax_id.include_base_amount else []
                })
                done_taxes.append(tax.id)
        return res

    def inv_line_characteristic_hashcode(self, invoice_line):
        """Overridable hashcode generation for invoice lines. Lines having the same hashcode
        will be grouped together if the journal has the 'group line' option. Of course a module
        can add fields to invoice lines that would need to be tested too before merging lines
        or not."""
        return "%s-%s-%s-%s-%s-%s-%s" % (
            invoice_line['account_id'],
            invoice_line.get('tax_ids', 'False'),
            invoice_line.get('tax_line_id', 'False'),
            invoice_line.get('product_id', 'False'),
            invoice_line.get('analytic_account_id', 'False'),
            invoice_line.get('date_maturity', 'False'),
            invoice_line.get('analytic_tag_ids', 'False'),
        )

    def group_lines(self, iml, line):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if self.journal_id.group_invoice_lines:
            line2 = {}
            for x, y, l in line:
                tmp = self.inv_line_characteristic_hashcode(l)
                if tmp in line2:
                    am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                    line2[tmp]['debit'] = (am > 0) and am or 0.0
                    line2[tmp]['credit'] = (am < 0) and -am or 0.0
                    line2[tmp]['amount_currency'] += l['amount_currency']
                    line2[tmp]['analytic_line_ids'] += l['analytic_line_ids']
                    qty = l.get('quantity')
                    if qty:
                        line2[tmp]['quantity'] = line2[tmp].get('quantity', 0.0) + qty
                else:
                    line2[tmp] = l
            line = []
            for key, val in line2.items():
                line.append((0, 0, val))
        return line



    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)
            
            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency
                ctx['date'] = inv._get_currency_rate_date()
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)
            
            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        for line in invoice_move_lines:
            amountss = 0.0
            amountadd = 0.0   
            round_curr = self.currency_id.round
            if line.get('invoice_tax_line_id'):
                dttax_id = self.env['account.tax'].search([('id','=',line.get('tax_line_id'))],limit=1)
                if dttax_id.price_include_total:
                    line['price'] = ((line['price'])*-1)
                else:
                    line['price'] = ((line['price'])*+1)
            if line.get('tax_line_id'):
                dtax_id = self.env['account.tax'].search([('id','=',line.get('tax_line_id'))],limit=1)
                if dtax_id.price_include_total:
                    if self.currency_id != company_currency:
                        currency = self.currency_id.with_context(date=self._get_currency_rate_date() or fields.Date.context_today(self))
                        if not (line.get('currency_id') and line.get('amount_currency')):
                            line['currency_id'] = currency.id
                            line['amount_currency'] = currency.round(line['price'])
                            line['price'] = currency.compute(line['price'], company_currency)
                    else:
                        line['currency_id'] = False
                        line['amount_currency'] = False
                        line['price'] = self.currency_id.round(line['price'])
                    if self.type in ('out_invoice', 'in_refund'):
                        total += line['price']
                        total_currency += line['amount_currency'] or line['price']
                        line['price'] = - line['price']
                    else:
                        total -= line['price']
                        total_currency -= line['amount_currency'] or line['price']
                else:
                    if self.currency_id != company_currency:
                        currency = self.currency_id.with_context(date=self._get_currency_rate_date() or fields.Date.context_today(self))
                        if not (line.get('currency_id') and line.get('amount_currency')):
                            line['currency_id'] = currency.id
                            line['amount_currency'] = currency.round(line['price'])
                            line['price'] = currency.compute(line['price'], company_currency)
                    else:
                        line['currency_id'] = False
                        line['amount_currency'] = False
                        line['price'] = self.currency_id.round(line['price'])
                    if self.type in ('out_invoice', 'in_refund'):
                        total += line['price']
                        total_currency += line['amount_currency'] or line['price']
                        line['price'] = - line['price']
                    else:
                        total -= line['price']
                        total_currency -= line['amount_currency'] or line['price']
            else:
                if self.currency_id != company_currency:
                    currency = self.currency_id.with_context(date=self._get_currency_rate_date() or fields.Date.context_today(self))
                    if not (line.get('currency_id') and line.get('amount_currency')):
                        line['currency_id'] = currency.id
                        line['amount_currency'] = currency.round(line['price'])
                        line['price'] = currency.compute(line['price'], company_currency)
                else:
                    line['currency_id'] = False
                    line['amount_currency'] = False
                    line['price'] = self.currency_id.round(line['price'])
                if self.type in ('out_invoice', 'in_refund'):
                    total += line['price']
                    total_currency += line['amount_currency'] or line['price']
                    line['price'] = - line['price']
                else:
                    total -= line['price']
                    total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, invoice_move_lines
