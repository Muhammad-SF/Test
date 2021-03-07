# -*- coding: utf-8 -*-
# Copyright 2019, AUTHOR(S)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models, api, _
from lxml import etree
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rate_type = fields.Selection([('c1', 'Corporate Rate'), ('u1', 'User Rate')], default='c1')
    c1_rate = fields.Float(string='Corporate Rate',  compute='_compute_c1_rate', store=True)
    u1_rate = fields.Float(string='User Rate')
    check_crrency = fields.Boolean(compute='_compute_check_currency', store=True)

    @api.depends('currency_id', 'company_id', 'company_id.currency_id')
    def _compute_check_currency(self):
        for record in self:
            if record.currency_id.id == record.company_id.currency_id.id:
                record.check_crrency = True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Hide/Show 'Rate type, Corporate and User rates' fields of PO form view according to purchase.config.settings's 'Activate User Rate For PO' field. """
        res = super(PurchaseOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        dom = etree.XML(res['arch'])
        is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        if is_user_rate_po == False:
            for node in dom.xpath("//field[@name='rate_type']"):
                node.set("modifiers", '{"invisible":true}')
            for node in dom.xpath("//field[@name='c1_rate']"):
                node.set("modifiers", '{"invisible":true}')
            for node in dom.xpath("//field[@name='u1_rate']"):
                node.set("modifiers", '{"invisible":true}')
            res['arch'] = etree.tostring(dom)
        return res

    @api.depends('rate_type', 'date_order', 'currency_id')
    def _compute_c1_rate(self):
        for record in self.filtered(lambda x: x.currency_id and x.rate_type == 'c1'):
            record.c1_rate = record.with_context({'date': record.date_order}).currency_id.conversion

    @api.multi
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        if is_user_rate_po == True:
            if self.rate_type:
                res['rate_type'] = self.rate_type
                if self.rate_type == 'c1':
                    res['c1_rate'] = self.c1_rate
                else:
                    res['u1_rate'] = self.u1_rate
            if self.currency_id:
                res['currency_id'] = self.currency_id.id
        return res

PurchaseOrder()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _get_stock_move_price_unit(self):
        is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        if is_user_rate_po == True:
            self.ensure_one()
            line = self[0]
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                price_unit = line.taxes_id.with_context(round=False).compute_all(
                    price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id,
                    partner=line.order_id.partner_id
                )['total_excluded']
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                if line.order_id.rate_type and line.order_id.rate_type == 'u1' and line.order_id.u1_rate:
                    price_unit = line.order_id.u1_rate * line.price_unit
                elif line.order_id.rate_type and line.order_id.rate_type == 'c1' and line.order_id.c1_rate:
                    price_unit = line.order_id.c1_rate * line.price_unit
                else:
                    price_unit = order.currency_id.compute(price_unit, order.company_id.currency_id, round=False)
        else:
            price_unit = super(PurchaseOrderLine, self)._get_stock_move_price_unit()
        return price_unit

PurchaseOrderLine()

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('rate_type', 'c1_rate', 'u1_rate','date_invoice')
    def _get_spot_rate(self):
        today = datetime.now().date()
        for invoice in self:
            if invoice.date_invoice:
                invoice_date = datetime.strptime(str(invoice.date_invoice), '%Y-%m-%d').date()
            else:
                invoice_date = today
            if invoice.rate_type and today == invoice_date:
                rate = 0.0
                if invoice.rate_type == 'c1' and invoice.c1_rate:
                    rate = invoice.c1_rate
                if invoice.rate_type == 'u1' and invoice.u1_rate:
                    rate = invoice.u1_rate
                invoice.spot_rate = rate

    rate_type = fields.Selection([('c1', 'Corporate Rate'), ('u1', 'User Rate')], default='c1')
    c1_rate = fields.Float(string='Corporate Rate', compute='_compute_invoice_c1_rate', store=True)
    u1_rate = fields.Float(string='User Rate')
    check_crrency = fields.Boolean(compute='_compute_check_currency', store=True)
    spot_rate = fields.Float(string='Spot Rate', compute='_get_spot_rate', store=True)

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
        for invoice in self:
            for move in self.env['account.move'].search(['|', ('is_user_rate_po_move', '=', True), ('is_user_rate_so_move', '=', True)]):
                if move:
                    move_line_invoice_ids = [line.invoice_id.id for line in move.line_ids if invoice == line.invoice_id]
                    if move_line_invoice_ids and (is_user_rate_po == True or is_user_rate_so == True):
                        move.button_cancel()
                        move.unlink()
        return res

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
        if is_user_rate_po == True or is_user_rate_so == True:
            total = 0
            total_currency = 0
            for line in invoice_move_lines:
                invoice_id = self.env['account.invoice'].browse(line['invoice_id'])
                invoice_rate = 1.00
                if invoice_id and invoice_id.rate_type and invoice_id.rate_type == 'c1' and invoice_id.c1_rate:
                    invoice_rate = invoice_id.c1_rate
                if invoice_id and invoice_id.rate_type and invoice_id.rate_type == 'u1' and invoice_id.u1_rate:
                    invoice_rate = invoice_id.u1_rate
                if self.currency_id != company_currency:
                    currency = self.currency_id.with_context(date=self._get_currency_rate_date() or fields.Date.context_today(self))
                    if not (line.get('currency_id') and line.get('amount_currency')):
                        line['currency_id'] = currency.id
                        line['amount_currency'] = currency.round(line['price'])
                        if invoice_id.rate_type and (invoice_id.c1_rate or invoice_id.u1_rate):
                            line['price'] = line['price'] * invoice_rate
                        else:
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
        else:
            super(AccountInvoice, self).compute_invoice_totals(company_currency, invoice_move_lines)

    @api.depends('currency_id', 'company_id', 'company_id.currency_id')
    def _compute_check_currency(self):
        for record in self:
            if record.currency_id.id == record.company_id.currency_id.id:
                record.check_crrency = True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Hide/Show 'Rate type, Corporate and User rates' fields of invoice form view according to purchase.config.settings's and sale.config.settings's'Activate User Rate For PO and Activate User Rate For SO' fields. """
        res = super(AccountInvoice, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                         submenu=submenu)
        dom = etree.XML(res['arch'])
        is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
        if self._context.get('type'):
            if (self._context['type'] in ('in_invoice', 'in_refund') and is_user_rate_po == False) or (self._context['type'] in ('out_invoice', 'out_refund') and is_user_rate_so == False):
                for node in dom.xpath("//field[@name='rate_type']"):
                    node.set("modifiers", '{"invisible":true}')
                for node in dom.xpath("//field[@name='c1_rate']"):
                    node.set("modifiers", '{"invisible":true}')
                for node in dom.xpath("//field[@name='u1_rate']"):
                    node.set("modifiers", '{"invisible":true}')
                res['arch'] = etree.tostring(dom)
        return res

    @api.depends('rate_type', 'date_invoice', 'currency_id')
    def _compute_invoice_c1_rate(self):
        for record in self.filtered(lambda x: x.currency_id and x.rate_type == 'c1'):
            record.c1_rate = record.with_context({'date': record.date_invoice}).currency_id.conversion

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        if self.purchase_id.currency_id:
            self.currency_id = self.purchase_id.currency_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.purchase_id = False
        return {}

    # Additional JE for PO
    def test_account_vendor_validate_account(self):
        for record in self:
            is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
            for line in record.invoice_line_ids:
                if is_user_rate_po == True and line.purchase_line_id and line.purchase_line_id.order_id and line.purchase_line_id.order_id.currency_id != line.purchase_line_id.order_id.company_id.currency_id and line.invoice_id.currency_id != line.invoice_id.company_id.currency_id:
                    account_move_line = self.env['account.move.line']
                    account_expense = line.product_id.categ_id.property_account_expense_categ_id
                    account_config_id = self.env['account.config.settings'].search([], limit=1)
                    if account_config_id and account_config_id.currency_exchange_journal_id:
                        journal = account_config_id.currency_exchange_journal_id
                    else:
                        journal = self.company_id.currency_exchange_journal_id
                    company_id = self.env['res.users'].browse(self.env.uid).company_id.id

                    # Calculating price with discount
                    if line.purchase_line_id.discount_type and line.purchase_line_id.discount and line.purchase_line_id.product_qty:
                        if line.purchase_line_id.discount_type == 'fixed':
                            initial_price_subtotal = line.purchase_line_id.price_subtotal * line.purchase_line_id.product_qty - line.purchase_line_id.discount
                            price_subtotal = initial_price_subtotal / line.purchase_line_id.product_qty
                        else:
                            price_subtotal = line.purchase_line_id.price_subtotal * (1.0 - line.purchase_line_id.discount / 100.0)
                    else:
                        price_subtotal = line.purchase_line_id.price_subtotal

                    # For rate type calculation

                    # if line.purchase_line_id and line.purchase_line_id.order_id.rate_type == 'c1':
                    #     po_rate = line.purchase_line_id.order_id.c1_rate
                    # else:
                    #     po_rate = line.purchase_line_id.order_id.u1_rate
                    #
                    # if line.invoice_id.rate_type == 'c1':
                    #     invoice_rate = line.invoice_id.c1_rate
                    # else:
                    #     invoice_rate = line.invoice_id.u1_rate

                    if line.purchase_line_id.account_analytic_id:
                        analytic_account_id = line.purchase_line_id.account_analytic_id.id
                    else:
                        analytic_account_id = False

                    analytic_distribution = []
                    module_id = self.env['ir.module.module'].search([('name', '=', 'multi_level_analytical')], limit=1)
                    if module_id and module_id.state == 'installed' and line.purchase_line_id.analytic_distribution_id:
                        for analytic in line.purchase_line_id.analytic_distribution_id:
                            analytic_distribution.append((0, 0, {'rate': analytic.rate if analytic.rate else 0.00,
                                                 'analytic_level_id': analytic.analytic_level_id.id if analytic.analytic_level_id else False,
                                                 'analytic_account_id': analytic.analytic_account_id.id if analytic.analytic_account_id else False,
                                                 }))

                    if line.purchase_line_id.order_id.currency_id == line.invoice_id.currency_id:
                        po_rate = 0.00
                        invoice_rate = 0.00
                        if line.purchase_line_id.order_id.rate_type == 'c1' and line.purchase_line_id.order_id.c1_rate:
                            po_rate = line.purchase_line_id.order_id.c1_rate
                        if line.purchase_line_id.order_id.rate_type == 'u1' and line.purchase_line_id.order_id.u1_rate:
                            po_rate = line.purchase_line_id.order_id.u1_rate
                        if line.invoice_id.rate_type == 'c1' and line.invoice_id.c1_rate:
                            invoice_rate = line.invoice_id.c1_rate
                        if line.invoice_id.rate_type == 'u1' and line.invoice_id.u1_rate:
                            invoice_rate = line.invoice_id.u1_rate
                        po_amount = price_subtotal * po_rate
                        invoice_amount = price_subtotal * invoice_rate
                        current_rate = po_amount - invoice_amount
                    else:
                        current_rate = 0.00
                        po_amount = 0.00
                        invoice_amount = 0.00
                        if line.purchase_line_id.order_id.rate_type == 'c1' and line.invoice_id.rate_type == 'u1' and line.purchase_line_id.order_id.c1_rate and line.invoice_id.u1_rate and line.invoice_id.currency_id.conversion:
                            po_amount = price_subtotal * line.purchase_line_id.order_id.c1_rate
                            invoice_amount = (po_amount * line.invoice_id.u1_rate) / line.invoice_id.currency_id.conversion
                            current_rate = po_amount - invoice_amount
                        if line.purchase_line_id.order_id.rate_type == 'u1' and line.invoice_id.rate_type == 'c1' and line.purchase_line_id.order_id.u1_rate:
                            po_amount = price_subtotal * line.purchase_line_id.order_id.u1_rate
                            invoice_amount = price_subtotal * line.purchase_line_id.order_id.currency_id.conversion
                            current_rate = po_amount - invoice_amount
                        if line.purchase_line_id.order_id.rate_type == 'u1' and line.invoice_id.rate_type == 'u1' and line.purchase_line_id.order_id.u1_rate and line.purchase_line_id.order_id.currency_id.conversion and line.invoice_id.currency_id.conversion and line.invoice_id.u1_rate:
                            po_amount = price_subtotal * line.purchase_line_id.order_id.u1_rate
                            po_conversion = price_subtotal * line.purchase_line_id.order_id.currency_id.conversion
                            invoice_amount = (po_conversion * line.invoice_id.u1_rate) / line.invoice_id.currency_id.conversion
                            current_rate = po_amount - invoice_amount
                        if line.purchase_line_id.order_id.rate_type == 'c1' and line.invoice_id.rate_type == 'c1' and line.purchase_line_id.order_id.c1_rate and line.purchase_line_id.order_id.currency_id.conversion and line.invoice_id.currency_id.conversion and line.invoice_id.c1_rate:
                            po_amount = price_subtotal * line.purchase_line_id.order_id.c1_rate
                            po_conversion = price_subtotal * line.purchase_line_id.order_id.currency_id.conversion
                            invoice_amount = (po_conversion * line.invoice_id.c1_rate) / line.invoice_id.currency_id.conversion
                            current_rate = po_amount - invoice_amount

                    # Creation of additional JE based on given rate type and its rate
                    if current_rate != 0.00:
                        if current_rate < 0.00:
                            final_rate = -(current_rate)
                        else:
                            final_rate = current_rate
                        move_vals = {}
                        move_vals['name'] = '/'
                        move_vals['ref'] = self.number
                        move_vals['journal_id'] = journal.id
                        move_vals['state'] = 'draft'
                        move_vals['is_user_rate_po_move'] = True
                        move_vals['date'] = self.date_invoice
                        # move = self.env['account.move'].create({'name': '/',
                        #     'ref': self.number,
                        #     'journal_id': journal.id,
                        #     'state':'draft',
                        #     'company_id': company_id,
                        #     'date': self.date_invoice,
                        # })
                        module_id = self.env['ir.module.module'].search([('name', '=', 'multi_level_analytical')],limit=1)
                        if po_amount > invoice_amount:
                            # create move line
                            move_line_vals1 = {
                                'name': line.product_id.name,
                                # 'move_id': move.id,
                                'account_id': account_expense.id,
                                'debit': final_rate,
                                'invoice_id': line.invoice_id.id
                            }

                            # create another move line
                            move_line_vals2 = {}
                            if line.purchase_line_id.taxes_id:
                                for tax in line.purchase_line_id.taxes_id:
                                    if tax.amount != 0.0:
                                        tax_amount = final_rate / (tax.amount if tax.amount else 1)
                                        move_line_vals2 = {
                                            'name': tax.name,
                                            # 'move_id': move.id,
                                            'account_id': tax.account_id.id,
                                            'debit': tax_amount,
                                            'invoice_id': line.invoice_id.id
                                        }
                            if not line.purchase_line_id.taxes_id:
                                move_line_vals3 = {
                                    'name': line.product_id.name,
                                    # 'move_id': move.id,
                                    'account_id': journal.default_credit_account_id.id,
                                    'credit': final_rate,
                                    'invoice_id': line.invoice_id.id
                                }
                            else:
                                # creation of move line for taxes
                                multiple_tax_amount = 0.00
                                for tax in line.purchase_line_id.taxes_id:
                                    if len(line.purchase_line_id.taxes_id) > 1 and tax.amount != 0.0:
                                        multiple_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                single_tax_amount = 0.00
                                for tax in line.purchase_line_id.taxes_id:
                                    if len(line.purchase_line_id.taxes_id) == 1 and tax.amount != 0.0:
                                        single_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                if len(line.purchase_line_id.taxes_id) > 1:
                                    final_tax_amount = multiple_tax_amount
                                else:
                                    final_tax_amount = single_tax_amount
                                move_line_vals3 = {
                                    'name': line.product_id.name,
                                    # 'move_id': move.id,
                                    'account_id': journal.default_credit_account_id.id,
                                    'credit': final_rate + final_tax_amount,
                                    'invoice_id': line.invoice_id.id
                                }
                            if move_line_vals2:
                                move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals2), (0, 0, move_line_vals3)]
                            else:
                                move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals3)]
                            move = self.env['account.move'].create(move_vals)
                            move.journal_id = journal.id
                            for line in move.line_ids:
                                if module_id and module_id.state == 'installed' and analytic_distribution:
                                    line.analytic_distribution_id = analytic_distribution
                                else:
                                    line.analytic_account_id = analytic_account_id
                            move.post()

                        if po_amount < invoice_amount:
                            move_line_vals1 = {
                                'name': line.product_id.name,
                                # 'move_id': move.id,
                                'account_id': journal.default_debit_account_id.id,
                                'debit': final_rate,
                                'credit': 0.00,
                                'invoice_id': line.invoice_id.id
                            }
                            # create another move line
                            move_line_vals2 = {}
                            if line.purchase_line_id.taxes_id:
                                for tax in line.purchase_line_id.taxes_id:
                                    if tax.amount != 0.0:
                                        tax_amount = final_rate / (tax.amount if tax.amount else 1)
                                        move_line_vals2 = {
                                            'name': tax.name,
                                            # 'move_id': move.id,
                                            'account_id': tax.account_id.id,
                                            'debit': tax_amount,
                                            'credit': 0.00,
                                            'invoice_id': line.invoice_id.id
                                        }
                            if not line.purchase_line_id.taxes_id:
                                move_line_vals3 = {
                                    'name': line.product_id.name,
                                    # 'move_id': move.id,
                                    'account_id': account_expense.id,
                                    'credit': final_rate,
                                    'debit': 0.00,
                                    'invoice_id': line.invoice_id.id
                                }
                            else:
                                # creation of move line for taxes
                                multiple_tax_amount = 0.00
                                for tax in line.purchase_line_id.taxes_id:
                                    if len(line.purchase_line_id.taxes_id) > 1 and tax.amount != 0.0:
                                        multiple_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                single_tax_amount = 0.00
                                for tax in line.purchase_line_id.taxes_id:
                                    if len(line.purchase_line_id.taxes_id) == 1 and tax.amount != 0.0:
                                        single_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                if len(line.purchase_line_id.taxes_id) > 1:
                                    final_tax_amount = multiple_tax_amount
                                else:
                                    final_tax_amount = single_tax_amount

                                move_line_vals3 = {
                                    'name': line.product_id.name,
                                    # 'move_id': move.id,
                                    'account_id': account_expense.id,
                                    'credit': final_rate + final_tax_amount,
                                    'debit': 0.00,
                                    'invoice_id': line.invoice_id.id
                                }
                            if move_line_vals2:
                                move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals2), (0, 0, move_line_vals3)]
                            else:
                                move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals3)]
                            move = self.env['account.move'].create(move_vals)
                            move.journal_id = journal.id
                            for line in move.line_ids:
                                if module_id and module_id.state == 'installed' and analytic_distribution:
                                    line.analytic_distribution_id = analytic_distribution
                                else:
                                    line.analytic_account_id = analytic_account_id
                            move.post()


                            # check that Initially account move state is "Draft"
                            # self.assertTrue((move.state == 'draft'), "Initially account move state is Draft")

                            # validate this account move by using the 'Post Journal Entries' wizard
                            # validate_account_move = self.env['validate.account.move'].with_context(active_ids=move.id).create({})

                            #click on validate Button
                            # validate_account_move.with_context({'active_ids': [move.id]}).validate_move()

                            #check that the move state is now "Posted"
                            # self.assertTrue((move.state == 'posted'), "Initially account move state is Posted")

    # Additional JE for SO
    def test_account_customer_validate_account(self):
        for record in self:
            is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
            for line in record.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    if is_user_rate_so == True and sale_line and sale_line.order_id and line.invoice_id.currency_id != line.invoice_id.company_id.currency_id and sale_line.order_id.currency_id != sale_line.order_id.company_id.currency_id:
                        account_move_line = self.env['account.move.line']
                        account_income = line.product_id.categ_id.property_account_income_categ_id
                        account_config_id = self.env['account.config.settings'].search([], limit=1)
                        if account_config_id and account_config_id.currency_exchange_journal_id:
                            journal = account_config_id.currency_exchange_journal_id
                        else:
                            journal = self.company_id.currency_exchange_journal_id
                        company_id = self.env['res.users'].browse(self.env.uid).company_id.id

                        # For rate type calculation
                        # if sale_line and sale_line.order_id.rate_type == 'c1':
                        #     so_rate = sale_line.order_id.c1_rate
                        # else:
                        #     so_rate = sale_line.order_id.u1_rate
                        #
                        # if line.invoice_id.rate_type == 'c1':
                        #     invoice_rate = line.invoice_id.c1_rate
                        # else:
                        #     invoice_rate = line.invoice_id.u1_rate
                        #
                        # current_rate = so_rate - invoice_rate

                        if line.purchase_line_id.account_analytic_id:
                            analytic_account_id = line.purchase_line_id.account_analytic_id.id
                        else:
                            analytic_account_id = False

                        analytic_distribution = []
                        module_id = self.env['ir.module.module'].search([('name', '=', 'multi_level_analytical')],limit=1)
                        if module_id and module_id.state == 'installed' and sale_line.analytic_distribution_id:
                            for analytic in sale_line.analytic_distribution_id:
                                analytic_distribution.append((0, 0, {'rate': analytic.rate if analytic.rate else 0.00,
                                                                     'analytic_level_id': analytic.analytic_level_id.id if analytic.analytic_level_id else False,
                                                                     'analytic_account_id': analytic.analytic_account_id.id if analytic.analytic_account_id else False,
                                                                     }))

                        price_subtotal = sale_line.price_subtotal
                        if sale_line.order_id.currency_id == line.invoice_id.currency_id:
                            so_rate = 0.00
                            invoice_rate = 0.00
                            if sale_line.order_id.rate_type == 'c1' and sale_line.order_id.c1_rate:
                                so_rate = sale_line.order_id.c1_rate
                            if sale_line.order_id.rate_type == 'u1' and sale_line.order_id.u1_rate:
                                so_rate = sale_line.order_id.u1_rate
                            if line.invoice_id.rate_type == 'c1' and line.invoice_id.c1_rate:
                                invoice_rate = line.invoice_id.c1_rate
                            if line.invoice_id.rate_type == 'u1' and line.invoice_id.u1_rate:
                                invoice_rate = line.invoice_id.u1_rate
                            so_amount = price_subtotal * so_rate
                            invoice_amount = price_subtotal * invoice_rate
                            current_rate = so_amount - invoice_amount
                        else:
                            current_rate = 0.00
                            so_amount = 0.00
                            invoice_amount = 0.00
                            if sale_line.order_id.rate_type == 'c1' and line.invoice_id.rate_type == 'u1' and sale_line.order_id.c1_rate and line.invoice_id.u1_rate and line.invoice_id.currency_id.conversion:
                                so_amount = price_subtotal * sale_line.order_id.c1_rate
                                invoice_amount = (so_amount * line.invoice_id.u1_rate) / line.invoice_id.currency_id.conversion
                                current_rate = so_amount - invoice_amount
                            if sale_line.order_id.rate_type == 'u1' and line.invoice_id.rate_type == 'c1' and sale_line.order_id.u1_rate:
                                so_amount = price_subtotal * sale_line.order_id.u1_rate
                                invoice_amount = price_subtotal * sale_line.order_id.currency_id.conversion
                                current_rate = so_amount - invoice_amount
                            if sale_line.order_id.rate_type == 'u1' and line.invoice_id.rate_type == 'u1' and sale_line.order_id.u1_rate and sale_line.order_id.currency_id.conversion and line.invoice_id.currency_id.conversion and line.invoice_id.u1_rate:
                                so_amount = price_subtotal * sale_line.order_id.u1_rate
                                so_conversion = price_subtotal * sale_line.order_id.currency_id.conversion
                                invoice_amount = (so_conversion * line.invoice_id.u1_rate) / line.invoice_id.currency_id.conversion
                                current_rate = so_amount - invoice_amount
                            if sale_line.order_id.rate_type == 'c1' and line.invoice_id.rate_type == 'c1' and sale_line.order_id.c1_rate and sale_line.order_id.currency_id.conversion and line.invoice_id.currency_id.conversion and line.invoice_id.c1_rate:
                                so_amount = price_subtotal * sale_line.order_id.c1_rate
                                so_conversion = price_subtotal * sale_line.order_id.currency_id.conversion
                                invoice_amount = (so_conversion * line.invoice_id.c1_rate) / line.invoice_id.currency_id.conversion
                                current_rate = so_amount - invoice_amount

                        # Creation of additional JE based on given rate type and its rate
                        if current_rate != 0.00:
                            if current_rate < 0.00:
                                final_rate = -(current_rate)
                            else:
                                final_rate = current_rate

                            move_vals = {}
                            move_vals['name'] = '/'
                            move_vals['ref'] = self.number
                            move_vals['journal_id'] = journal.id
                            move_vals['state'] = 'draft'
                            move_vals['is_user_rate_so_move'] = True
                            move_vals['date'] = self.date_invoice

                            # move = self.env['account.move'].create({'name': '/',
                            #                                         'ref': self.number,
                            #                                         'journal_id': journal.id,
                            #                                         'state': 'draft',
                            #                                         'company_id': company_id,
                            #                                         'date': self.date_invoice,
                            #                                         })
                            module_id = self.env['ir.module.module'].search([('name', '=', 'multi_level_analytical')],limit=1)
                            if so_amount > invoice_amount:
                                # create move line
                                move_line_vals1 = {
                                    'name': line.product_id.name,
                                    # 'move_id': move.id,
                                    'account_id': account_income.id,
                                    'debit': final_rate,
                                    'invoice_id': line.invoice_id.id
                                }
                                # create another move line
                                move_line_vals2 = {}
                                if sale_line.tax_id:
                                    for tax in sale_line.tax_id:
                                        if tax.amount != 0.0:
                                            tax_amount = final_rate / (tax.amount if tax.amount else 1)
                                            move_line_vals2 = {
                                                'name': tax.name,
                                                # 'move_id': move.id,
                                                'account_id': tax.account_id.id,
                                                'debit': tax_amount,
                                                'invoice_id': line.invoice_id.id
                                            }
                                if not sale_line.tax_id:
                                    move_line_vals3 = {
                                        'name': line.product_id.name,
                                        # 'move_id': move.id,
                                        'account_id': journal.default_credit_account_id.id,
                                        'credit': final_rate,
                                        'invoice_id': line.invoice_id.id
                                    }
                                else:
                                    # creation of move line for taxes
                                    multiple_tax_amount = 0.00
                                    for tax in sale_line.tax_id:
                                        if len(sale_line.tax_id) > 1 and tax.amount != 0.0:
                                            multiple_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                    single_tax_amount = 0.00
                                    for tax in sale_line.tax_id:
                                        if len(sale_line.tax_id) == 1 and tax.amount != 0.0:
                                            single_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                    if len(sale_line.tax_id) > 1:
                                        final_tax_amount = multiple_tax_amount
                                    else:
                                        final_tax_amount = single_tax_amount
                                    move_line_vals3 = {
                                        'name': line.product_id.name,
                                        # 'move_id': move.id,
                                        'account_id': journal.default_credit_account_id.id,
                                        'credit': final_rate + final_tax_amount,
                                        'invoice_id': line.invoice_id.id
                                    }
                                if move_line_vals2:
                                    move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals2),
                                                             (0, 0, move_line_vals3)]
                                else:
                                    move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals3)]
                                move = self.env['account.move'].create(move_vals)
                                move.journal_id = journal.id
                                for line in move.line_ids:
                                    if module_id and module_id.state == 'installed' and analytic_distribution:
                                        line.analytic_distribution_id = analytic_distribution
                                    else:
                                        line.analytic_account_id = analytic_account_id
                                move.post()

                            if so_amount < invoice_amount:
                                move_line_vals1 = {
                                    'name': line.product_id.name,
                                    # 'move_id': move.id,
                                    'account_id': journal.default_credit_account_id.id,
                                    'debit': final_rate,
                                    'invoice_id': line.invoice_id.id
                                }
                                # create another move line
                                move_line_vals2 = {}
                                if sale_line.tax_id:
                                    for tax in sale_line.tax_id:
                                        if tax.amount != 0.0:
                                            tax_amount = final_rate / (tax.amount if tax.amount else 1)
                                            move_line_vals2 = {
                                                'name': tax.name,
                                                # 'move_id': move.id,
                                                'account_id': tax.account_id.id,
                                                'debit': tax_amount,
                                                'invoice_id': line.invoice_id.id
                                            }
                                if not sale_line.tax_id:
                                    move_line_vals3 = {
                                        'name': line.product_id.name,
                                        # 'move_id': move.id,
                                        'account_id': account_income.id,
                                        'credit': final_rate,
                                        'invoice_id': line.invoice_id.id
                                    }
                                else:
                                    # creation of move line for taxes
                                    multiple_tax_amount = 0.00
                                    for tax in sale_line.tax_id:
                                        if len(sale_line.tax_id) > 1 and tax.amount != 0.0:
                                            multiple_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                    single_tax_amount = 0.00
                                    for tax in sale_line.tax_id:
                                        if len(sale_line.tax_id) == 1 and tax.amount != 0.0:
                                            single_tax_amount += final_rate / (tax.amount if tax.amount else 1)
                                    if len(sale_line.tax_id) > 1:
                                        final_tax_amount = multiple_tax_amount
                                    else:
                                        final_tax_amount = single_tax_amount
                                    move_line_vals3 = {
                                        'name': line.product_id.name,
                                        # 'move_id': move.id,
                                        'account_id': account_income.id,
                                        'credit': final_rate + final_tax_amount,
                                        'invoice_id': line.invoice_id.id
                                    }
                                if move_line_vals2:
                                    move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals2), (0, 0, move_line_vals3)]
                                else:
                                    move_vals['line_ids'] = [(0, 0, move_line_vals1), (0, 0, move_line_vals3)]
                                move = self.env['account.move'].create(move_vals)
                                move.journal_id = journal.id
                                for line in move.line_ids:
                                    if module_id and module_id.state == 'installed' and analytic_distribution:
                                        line.analytic_distribution_id = analytic_distribution
                                    else:
                                        line.analytic_account_id = analytic_account_id
                                move.post()

                            # validate this account move by using the 'Post Journal Entries' wizard
                            # validate_account_move = self.env['validate.account.move'].with_context(
                            #     active_ids=move.id).create({})

                            # click on validate Button
                            # validate_account_move.with_context({'active_ids': [move.id]}).validate_move()

    # @api.multi
    # def action_move_create(self):
    #     """ Creates invoice related analytics and financial move lines """
    #     account_move = self.env['account.move']
    #     for inv in self:
    #         is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
    #         is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
    #         invoice_rate = 1.00
    #         # if (is_user_rate_po == True or is_user_rate_so == True) and inv.rate_type and inv.currency_id != inv.company_id.currency_id and inv.rate_type == 'c1':
    #         #     invoice_rate = inv.c1_rate
    #         if (is_user_rate_po == True or is_user_rate_so == True) and inv.rate_type and inv.currency_id != inv.company_id.currency_id and inv.rate_type == 'u1':
    #             invoice_rate = inv.u1_rate
    #         if not inv.journal_id.sequence_id:
    #             raise UserError(_('Please define sequence on the journal related to this invoice.'))
    #         if not inv.invoice_line_ids:
    #             raise UserError(_('Please create some invoice lines.'))
    #         if inv.move_id:
    #             continue
    #
    #         ctx = dict(self._context, lang=inv.partner_id.lang)
    #
    #         if not inv.date_invoice:
    #             inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
    #         date_invoice = inv.date_invoice
    #         company_currency = inv.company_id.currency_id
    #
    #         # create move lines (one per invoice line + eventual taxes and analytic lines)
    #         iml = inv.invoice_line_move_line_get()
    #         iml += inv.tax_line_move_line_get()
    #
    #         diff_currency = inv.currency_id != company_currency
    #         # create one move line for the total and possibly adjust the other lines amount
    #         total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)
    #
    #         name = inv.name or '/'
    #         if inv.payment_term_id:
    #             totlines = \
    #                 inv.with_context(ctx).payment_term_id.with_context(currency_id=inv.currency_id.id).compute(
    #                     total,
    #                     date_invoice)[
    #                     0]
    #             res_amount_currency = total_currency
    #             ctx['date'] = date_invoice
    #             for i, t in enumerate(totlines):
    #                 if inv.currency_id != company_currency:
    #                     amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
    #                 else:
    #                     amount_currency = False
    #                 # last line: add the diff
    #                 res_amount_currency -= amount_currency or 0
    #                 if i + 1 == len(totlines):
    #                     amount_currency += res_amount_currency
    #                 iml.append({
    #                     'type': 'dest',
    #                     'name': name,
    #                     'price': t[1],
    #                     'account_id': inv.account_id.id,
    #                     'date_maturity': t[0],
    #                     'amount_currency': diff_currency and amount_currency,
    #                     'currency_id': diff_currency and inv.currency_id.id,
    #                     'invoice_id': inv.id
    #                 })
    #         else:
    #             iml.append({
    #                 'type': 'dest',
    #                 'name': name,
    #                 'price': total,
    #                 'account_id': inv.account_id.id,
    #                 'date_maturity': inv.date_due,
    #                 'amount_currency': diff_currency and total_currency,
    #                 'currency_id': diff_currency and inv.currency_id.id,
    #                 'invoice_id': inv.id
    #             })
    #         part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
    #         line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
    #         line = inv.group_lines(iml, line)
    #
    #         journal = inv.journal_id.with_context(ctx)
    #         line = inv.finalize_invoice_move_lines(line)
    #         date = inv.date or date_invoice
    #         move_vals = {
    #             'ref': inv.reference,
    #             'line_ids': line,
    #             'journal_id': journal.id,
    #             'date': date,
    #             'branch_id': inv.branch_id.id,
    #             'narration': inv.comment,
    #         }
    #         ctx['company_id'] = inv.company_id.id
    #         ctx['invoice'] = inv
    #         ctx_nolang = ctx.copy()
    #         ctx_nolang.pop('lang', None)
    #         move = account_move.with_context(ctx_nolang).create(move_vals)
    #         # for line in move.line_ids:
    #         #     if (is_user_rate_po == True or is_user_rate_so == True) and inv.currency_id != inv.company_id.currency_id and inv.rate_type:
    #         #         debit = line.debit * invoice_rate
    #         #         credit = line.credit * invoice_rate
    #         #         line.debit = debit
    #         #         line.credit = credit
    #         #     else:
    #         #         line.debit = line.debit
    #         #         line.credit = line.credit
    #
    #         # Pass invoice in context in method post: used if you want to get the same
    #         # account move reference when creating the same invoice after a cancelled one:
    #         move.post()
    #         # make the invoice point to that move
    #         vals = {
    #             'move_id': move.id,
    #             'date': date,
    #             'move_name': move.name,
    #         }
    #         inv.with_context(ctx).write(vals)
    #     return True

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        self.test_account_vendor_validate_account()
        self.test_account_customer_validate_account()
        return res

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        if self.currency_id:
            for line in self.invoice_line_ids:
                is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings','is_user_rate_po')
                is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
                if line and (is_user_rate_po or is_user_rate_so) and self.currency_id == self.company_id.currency_id and self.rate_type:
                    if self.rate_type == 'u1' and self.u1_rate:
                        line.price_subtotal = line.price_unit * self.u1_rate
                    if self.rate_type == 'c1' and self.c1_rate:
                        line.price_subtotal = line.price_unit * self.c1_rate

AccountInvoice()

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.depends('price_unit', 'discount', 'discount_type', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice')
    def _compute_price(self):
        for record in self:
            currency = record.invoice_id and record.invoice_id.currency_id or None
            is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
            is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
            if (is_user_rate_po or is_user_rate_so) and record.invoice_id.currency_id == record.invoice_id.company_id.currency_id and record.invoice_id.rate_type and (record.invoice_id.u1_rate or record.invoice_id.c1_rate):
                if record.invoice_id.rate_type == 'u1' and record.invoice_id.u1_rate and not record.invoice_id.rate_type == 'c1' and not record.invoice_id.c1_rate:
                    price = (record.price_unit * (1 - (record.discount or 0.0) / 100.0)) * record.invoice_id.u1_rate
                elif not record.invoice_id.rate_type == 'u1' and not record.invoice_id.u1_rate and record.invoice_id.rate_type == 'c1' and record.invoice_id.c1_rate:
                    price = record.price_unit * (1 - (record.discount or 0.0) / 100.0) * record.invoice_id.c1_rate
                else:
                    price = record.price_unit * (1 - (record.discount or 0.0) / 100.0)

                taxes = False
                if record.invoice_line_tax_ids:
                    taxes = record.invoice_line_tax_ids.compute_all(price, currency, record.quantity, product=record.product_id, partner=record.invoice_id.partner_id)
                record.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else record.quantity * price
                if record.invoice_id.currency_id and record.invoice_id.company_id and record.invoice_id.currency_id != record.invoice_id.company_id.currency_id:
                    price_subtotal_signed = record.invoice_id.currency_id.with_context(date=record.invoice_id.date_invoice).compute(price_subtotal_signed, record.invoice_id.company_id.currency_id)
                sign = record.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
                record.price_subtotal_signed = price_subtotal_signed * sign
            else:
                super(AccountInvoiceLine, self)._compute_price()

AccountInvoiceLine()

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_user_rate_po_move = fields.Boolean('User Rate PO Move')
    is_user_rate_so_move = fields.Boolean('User Rate SO Move')
    
    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        picking_id = self.env['stock.picking'].search([('name', '=', res.ref)])
        if picking_id and (picking_id.purchase_id or picking_id.sale_id):
            is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
            is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
            for line in res.line_ids:
                so_line = picking_id.sale_id.order_line.filtered(lambda x: x.product_id.id == line.product_id.id)
                po_line = picking_id.purchase_id.order_line.filtered(lambda x: x.product_id.id == line.product_id.id)
                if picking_id.min_date:
                    date = picking_id.min_date
                else:
                    date = datetime.now()
                company_id = picking_id.company_id.id or self.env['res.users']._get_company().id
                # the subquery selects the last rate before 'Scheduled Date' of picking for the given foreign currency/company at PO/SO
                query = """SELECT c.id, (SELECT r.conversion FROM res_currency_rate r
                                                                  WHERE r.currency_id = c.id AND r.name <= %s
                                                                    AND (r.company_id IS NULL OR r.company_id = %s)
                                                               ORDER BY r.company_id, r.name DESC
                                                                  LIMIT 1) AS conversion
                                                   FROM res_currency c
                                                   WHERE c.id IN %s"""
                if picking_id.purchase_id:
                    order_id = picking_id.purchase_id
                else:
                    order_id = picking_id.sale_id
                self._cr.execute(query, (date, company_id, tuple(order_id.currency_id.ids)))
                currency_conversions = dict(self._cr.fetchall())
                foreign_rate = currency_conversions.get(order_id.currency_id.id) or 0.00
                if so_line and is_user_rate_so == True:
                    if line.product_id and line.product_id.categ_id.property_cost_method == 'real':
                        price = so_line[0].price_unit * line.quantity
                    elif line.product_id and line.product_id.categ_id.property_cost_method == 'average':
                        price = line.product_id.standard_price * line.quantity
                    elif line.product_id and line.product_id.categ_id.property_cost_method == 'standard':
                        price = line.product_id.standard_price * line.quantity
                    else:
                        price = so_line[0].price_unit

                    if line.product_id.categ_id.property_cost_method == 'average' or line.product_id.categ_id.property_cost_method == 'standard':
                        amount = price
                    else:
                        if line.product_id and picking_id.sale_id.rate_type == 'c1' and picking_id.sale_id.c1_rate:
                            amount = foreign_rate * price
                        elif line.product_id and picking_id.sale_id.rate_type == 'u1' and picking_id.sale_id.u1_rate:
                            amount = picking_id.sale_id.u1_rate * price
                        else:
                            amount = price

                    if line.credit:
                        line.write({
                            'credit_cash_basis': amount,
                            'credit': amount,
                            'balance_cash_basis': -amount,
                            'balance': -amount,
                        })
                    if line.debit:
                        line.write({
                            'debit_cash_basis': amount,
                            'debit': amount,
                            'balance_cash_basis': amount,
                            'balance': amount,
                        })
                if po_line and is_user_rate_po == True:
                    if line.product_id and line.product_id.categ_id.property_cost_method == 'real':
                        price = po_line[0].price_unit * line.quantity
                    elif line.product_id and line.product_id.categ_id.property_cost_method == 'average':
                        price = po_line[0].price_unit * line.quantity
                    elif line.product_id and line.product_id.categ_id.property_cost_method == 'standard':
                        price = line.product_id.standard_price * line.quantity
                    else:
                        price = po_line[0].price_unit

                    if line.product_id.categ_id.property_cost_method == 'standard':
                        amount = price
                    else:
                        if line.product_id and picking_id.purchase_id.rate_type == 'c1' and picking_id.purchase_id.c1_rate:
                            amount = foreign_rate * price
                        elif line.product_id and picking_id.purchase_id.rate_type == 'u1' and picking_id.purchase_id.u1_rate:
                            amount = picking_id.purchase_id.u1_rate * price
                        else:
                            amount = price

                    if line.credit:
                        line.write({
                            'credit_cash_basis': amount,
                            'credit': amount,
                            'balance_cash_basis': -amount,
                            'balance': -amount,
                        })
                    if line.debit:
                        line.write({
                            'debit_cash_basis': amount,
                            'debit': amount,
                            'balance_cash_basis': amount,
                            'balance': amount,
                        })
        return res

AccountMove()