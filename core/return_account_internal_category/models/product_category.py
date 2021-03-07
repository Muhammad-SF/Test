# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = "product.category"

    sales_return_account_id = fields.Many2one('account.account',string="Sales Return Account",
        company_dependent=True,
        help="This account will be used for sales return.")
    purchase_return_account_id = fields.Many2one('account.account',string="Purchase Return Account",
        company_dependent=True,
        help="This account will be used for purchase return.")


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.invoice_id:
            return

        part = self.invoice_id.partner_id
        fpos = self.invoice_id.fiscal_position_id
        company = self.invoice_id.company_id
        currency = self.invoice_id.currency_id
        type = self.invoice_id.type

        if not part:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner!'),
                }
            return {'warning': warning}

        if not self.product_id:
            if type not in ('in_invoice', 'in_refund'):
                self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            if part.lang:
                product = self.product_id.with_context(lang=part.lang)
            else:
                product = self.product_id

            self.name = product.partner_ref
            account = self.get_invoice_line_account(type, product, fpos, company)
            if account:
                self.account_id = account.id
            if type == 'out_refund':
                if self.product_id.categ_id.sales_return_account_id:
                    self.account_id = self.product_id.categ_id.sales_return_account_id.id
            if type == 'in_refund':
                if self.product_id.categ_id.purchase_return_account_id:
                    self.account_id = self.product_id.categ_id.purchase_return_account_id.id

            self._set_taxes()

            if type in ('in_invoice', 'in_refund'):
                if product.description_purchase:
                    self.name += '\n' + product.description_purchase
            else:
                if product.description_sale:
                    self.name += '\n' + product.description_sale

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        return {'domain': domain}


class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    @api.model
    def create(self, vals):
        onchanges = {
            '_onchange_partner_id': ['account_id', 'payment_term_id', 'fiscal_position_id', 'partner_bank_id'],
            '_onchange_journal_id': ['currency_id'],
        }
        for onchange_method, changed_fields in onchanges.items():
            if any(f not in vals for f in changed_fields):
                invoice = self.new(vals)
                getattr(invoice, onchange_method)()
                for field in changed_fields:
                    if field not in vals and invoice[field]:
                        vals[field] = invoice._fields[field].convert_to_write(invoice[field], invoice)
        if not vals.get('account_id',False):
            raise UserError(_('Configuration error!\nCould not find any account to create the invoice, are you sure you have a chart of account installed?'))

        invoice = super(AccountInvoice, self.with_context(mail_create_nolog=True)).create(vals)

        if any(line.invoice_line_tax_ids for line in invoice.invoice_line_ids) and not invoice.tax_line_ids:
            invoice.compute_taxes()
        if self._context.get('search_disable_custom_filters') == True and self._context.get('type') == 'out_invoice':
            for line in invoice.invoice_line_ids:
                if line.product_id.categ_id.sales_return_account_id:
                    line.account_id = line.product_id.categ_id.sales_return_account_id.id

        return invoice