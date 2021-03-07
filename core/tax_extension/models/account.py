from odoo import models, fields, api, _
from odoo.exceptions import UserError


class invoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        
        price_include_total_tax = self.mapped('invoice_line_tax_ids').filtered(lambda tax: tax.price_include_total)
        if price_include_total_tax:
            if len(self.invoice_line_tax_ids) < 2:
                if self.invoice_line_tax_ids:
                    taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
                self.price_subtotal = price_subtotal_signed = self.quantity * price
                if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
                    price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
                sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
                self.price_subtotal_signed = price_subtotal_signed * sign
            else:
                if self.invoice_line_tax_ids:
                    taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
                self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
                if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
                    price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
                sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
                self.price_subtotal_signed = price_subtotal_signed * sign
        else:
            if self.invoice_line_tax_ids:
                taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
            self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
            if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
                price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
            sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
            self.price_subtotal_signed = price_subtotal_signed * sign
        
class Tax(models.Model):
    _inherit = 'account.tax'
    
    price_include_total =fields.Boolean(string="Included in Price Based on Total Amount")
    pay_seprately = fields.Boolean(string="To Pay Separately")
    tax_paid_account = fields.Many2one('account.account', string="Tax Paid Account")

class Invoice(models.Model):
    _inherit = 'account.invoice'
    
    payment_fields_boolean = fields.Boolean(string="Make Payment fields Visible", default=False)
    payment_proof = fields.Binary("Payment Proof")
    tax_payment_date = fields.Date("Tax Payment Date")
    ppn = fields.Html(string='PPN',readonly=True, compute='_compute_amount')
    pph = fields.Html(string='PPH',readonly=True, compute='_compute_amount')
    tax_paid_status = fields.Selection([
            ('unpaid', 'Unpaid'),
            ('paid', 'Paid'),
        ], string='Tax Paid Status', default='unpaid',
       )
    file_name = fields.Char(string="File Name")
    payment_date = fields.Date(string='Payment Date')
    separate_tax_amount = fields.Float(string='Tax Amount', compute='_compute_amount')

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        round_curr = self.currency_id.round
        taxes=[]

        for line in self.invoice_line_ids:
            tax_lines = []
            tax_included = line.invoice_line_tax_ids.filtered(lambda tax: tax.price_include)
            tax_not_included = line.invoice_line_tax_ids.filtered(lambda tax: not tax.price_include)
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            tax_lines.append(tax_included)
            tax_lines.append(tax_not_included)
            if tax_included:
                tax_price_included = tax_included.compute_all(price_unit, self.currency_id, line.quantity, line.product_id,
                                                          self.partner_id)['taxes']
                price = 0.0
                for tax_line in tax_price_included:
                    price += tax_line['base']
                taxes += tax_price_included
                price_unit = price
            prec = self.currency_id.decimal_places
            price_unit = round(price_unit * line.quantity, prec)
            tax_price_not_included = tax_not_included.with_context(base_values=(price_unit, price_unit, price_unit)).compute_all(price_unit, self.currency_id, line.quantity, line.product_id,
                                                          self.partner_id)['taxes']
            taxes += tax_price_not_included

            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.tax_line_ids.filtered('manual')
        for line in self.invoice_line_ids:
            for tax1 in line.invoice_line_tax_ids:
                amount=0.0
                base=0.0
                if tax1.price_include_total:
                   amount=line.price_subtotal * tax1.amount/100
                   base=line.price_subtotal
                else:
                   if tax1.price_include:
                      amount=line.price_subtotal * tax1.amount/100
                      #base1=line.price_unit
                      base=line.price_subtotal
                   else:
                      amount=line.price_subtotal * tax1.amount/100
                      base=line.price_unit
                   
                vals={'amount': amount, 'base': base, 'name': tax1.name, 'sequence': 1, 'account_analytic_id': False, 'invoice_id': self.id, 'manual': False, 'account_id': tax1.account_id.id, 'tax_id': tax1.id}

                tax_lines += tax_lines.new(vals)
        self.tax_line_ids = tax_lines
        return

    @api.one
    @api.depends('invoice_line_ids')
    def _compute_pay_separately(self):
        pay_seprately_tax = self.invoice_line_ids.mapped('invoice_line_tax_ids').filtered(lambda tax: tax.pay_seprately) and True or False
        if pay_seprately_tax:
            self.payment_fields_boolean = pay_seprately_tax

    # @api.multi
    # def action_invoice_open(self):
    #     to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
    #     if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
    #         pass
    #     for invoice in self:
    #         if self._context.get('tax_pay_menu'):
    #             if not invoice.payment_proof and not invoice.payment_date:
    #                 raise UserError(_('Please fill Payment Proof and Payment Date.'))
    #             else:
    #                 invoice.action_tax_move_create()
    #                 invoice.tax_paid_status = 'paid'
    #         else:
    #             to_open_invoices.action_date_assign()
    #             to_open_invoices.action_move_create()
    #     return to_open_invoices.invoice_validate()

    @api.multi
    def action_tax_invoice_open(self):
        for invoice in self:
            if not invoice.payment_proof and not invoice.payment_date:
                raise UserError(_('Please fill Payment Proof and Payment Date.'))
            else:
                invoice.action_tax_move_create()
                invoice.tax_paid_status = 'paid'

    @api.multi
    def action_invoice_cancel(self):
        res = super(Invoice, self).action_invoice_cancel()
        for invoice in self:
            invoice.payment_proof = ''
            invoice.payment_date = ''
            invoice.tax_paid_status = 'unpaid'
        return res

    @api.multi
    def open_invoice(self):
        domain = []
        _name = ''
        rq_tree = rq_form = ''
        if self._context.get('invoice_form'):
            domain = [('id', '=', self.id)]
            _name = self.name
            model = 'account.invoice'
            rq_form = self.env.ref('account.invoice_form', False)
        views = [(rq_form.id, 'form')]
        if rq_form:
            
            return {
                'name': _name,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': model,
                'views': views,
                'res_id': self.id,
                'view_id': rq_form.id,
                'target': 'current',
                'domain': domain,

            }    

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(line.amount) for line in self.tax_line_ids)
        amountss = 0.0
        amountadd = 0.0
        amountadd1 = 0.0
        pay_separate_tax = 0.0
        if self.tax_line_ids:
            for line in self.tax_line_ids:
                if line.tax_id.price_include_total:
                    amountss += round_curr(line.amount)
                elif line.tax_id.price_include_total:
                    amountadd += round_curr(line.amount)
                    self.amount_untaxed = self.amount_untaxed - amountadd
                else:
                    amountadd1 +=round_curr(line.amount)
                    amountadd += round_curr(line.amount)
                self.amount_total = self.amount_untaxed + amountadd - abs(amountss)
                if line.tax_id.pay_seprately:
                    pay_separate_tax += round_curr(line.amount)
                    self.payment_fields_boolean = True
        else:
            self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
        self.ppn = ("""%s %s""") % (amountadd1,self.company_currency_id.symbol)
        self.pph = ("""%s %s""") % (amountss,self.company_currency_id.symbol)
        self.separate_tax_amount = pay_separate_tax

    @api.model
    def tax_pay_line_move_line_get(self):
        res = []
        company_currency = self.journal_id.company_id.currency_id.id
        current_currency = self.currency_id.id or company_currency
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount:
                tax = tax_line.tax_id
                if tax.pay_seprately == True:
                    if tax.amount_type == "group":
                        for child_tax in tax.children_tax_ids:
                            done_taxes.append(child_tax.id)
                    date_due = self.payment_date
                    name = 'Payment Tax ' + str(self.name)

                    move_line_credit_vals = {
                        'name': name,
                        'account_id': tax.tax_paid_account.id,
                        'debit':  abs(tax_line.amount),
                        'credit': 0.0,
                        'partner_id': self.env['res.partner']._find_accounting_partner(self.partner_id).id,
                        'date': self.payment_date,
                        'journal_id': self.journal_id.id,
                        'tax_line_id': tax_line.tax_id.id,
                        'currency_id': self.currency_id.id or False,
                        'date_maturity': date_due,
                        'amount_currency': (-1 * abs(tax_line.amount)  # amount < 0 for refunds
                                            if company_currency != current_currency else 0.0),
                    }
                    move_line_debit_vals = {
                        'name': name,
                        'account_id': tax.account_id.id,
                        'debit': 0.0,
                        'credit': abs(tax_line.amount),
                        'partner_id': self.env['res.partner']._find_accounting_partner(self.partner_id).id,
                        'date': self.payment_date,
                        'tax_line_id': tax_line.tax_id.id,
                        'journal_id': self.journal_id.id,
                        'currency_id': self.currency_id.id or False,
                        'date_maturity': date_due,
                        'amount_currency': (-1 * abs(tax_line.amount)  # amount < 0 for refunds
                                            if company_currency != current_currency else 0.0),
                    }
                    res.append((0, 0, move_line_credit_vals))
                    res.append((0, 0, move_line_debit_vals))
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
    def action_tax_move_create(self):
        account_move = self.env['account.move']
        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            ctx = dict(self._context, lang=inv.partner_id.lang)
            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            iml = []
            iml += inv.tax_pay_line_move_line_get()
            journal = inv.journal_id.with_context(ctx)
            date = inv.payment_date and inv.payment_date or inv.date_invoice
            move_vals = {
                'name': '/',
                'ref': inv.number and inv.number or '',
                'line_ids': iml,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
                'partner_id': self.env['res.partner']._find_accounting_partner(inv.partner_id).id,
            }
            move = account_move.create(move_vals)
            move.post()
            for lm in move.line_ids:
                lm.name = 'Payment Tax ' + move.name
        return True
