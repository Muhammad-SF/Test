import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import datetime


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(selection_add=[
        ('progress_bill', 'Progressive Billing %'),
        ('retention_bill', 'Retention Rate')
    ])
    progressive_bill_per = fields.Float(string='Progressive Billing %', digits=dp.get_precision('Account'))

    @api.onchange('progressive_bill_per')
    def _onchange_progressive_bill_per(self):
        warning = {}
        for rec in self:
            if rec.progressive_bill_per and (rec.progressive_bill_per < 0 or rec.progressive_bill_per > 100):
                warning = {'title': 'Value Error', 'message': "Please input between 0 to 100% in Progressive Billing %."}
        return {'warning': warning}

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        elif self.advance_payment_method == 'progress_bill':
            if self.progressive_bill_per and (self.progressive_bill_per < 0 or self.progressive_bill_per > 100):
                raise UserError(_("Please input between 0 to 100% in Progressive Billing %."))
            else:
                self.generate_progressive_bill_invoice(sale_orders)
        elif self.advance_payment_method == 'retention_bill':
            self.generate_retention_rate_invoice(sale_orders)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                context = {'lang': order.partner_id.lang}
                so_line = sale_line_obj.create({'name': _('Advance: %s') % (time.strftime('%m %Y'),), 'price_unit': amount, 'product_uom_qty': 0.0, 'order_id': order.id, 'discount': 0.0, 'product_uom': self.product_id.uom_id.id, 'product_id': self.product_id.id, 'tax_id': [(6, 0, tax_ids)], })
                del context
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id or self.product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        del context
        taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'account_analytic_id': order.project_id.id or False,
                'is_down_payment': True,
                'sale_order_ref_id': order.id,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
            'user_id': order.user_id.id,
            'comment': order.note,
        })
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice, 'origin': order},
                                       subtype_id=self.env.ref('mail.mt_note').id)
        return invoice


    @api.multi
    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    @api.multi
    def generate_progressive_bill_invoice(self, sale_orders):
        invoice_obj = self.env["account.invoice"]
        invoice_line_obj = self.env["account.invoice.line"]
        res = {}

        for order in sale_orders:
            # Create Invoice

            total_order_amount = order.amount_total

            progressive_bill = self.progressive_bill_per
            progressive_bill_for_calculate = 0.0
            previously_invoiced_amount = ''

            retention_rate = order.retention_per

            # Calculate progressive billing values
            current_billing_per = progressive_bill
            total_billing_per_of_job_cost = order.total_invoiced_per
            total_amount_paid_of_job_cost = order.total_invoice_amount_paid or 0.0
            total_downpayment_paid_of_so = order.total_down_payment_paid or 0.0

            curr_invoice = {
                'partner_id': order.partner_id.id,
                'account_id': order.partner_id.property_account_receivable_id.id,
                'state': 'draft',
                'type': 'out_invoice',
                'date_invoice': datetime.datetime.now(),
                'origin': order.name,
                'retention_per': retention_rate,
                'target': 'new'
            }
            inv_ids = invoice_obj.create(curr_invoice)

            # Calculate next billing value based on previously validated invoice
            previous_invoice_line = invoice_line_obj.search([("sale_order_ref_id", "=", order.id)])
            if len(previous_invoice_line) == 0:
                progressive_bill_for_calculate = current_billing_per
            elif len(previous_invoice_line) > 0:
                progressive_bill_for_calculate = current_billing_per
                previously_invoiced_amount = str(total_amount_paid_of_job_cost) + " (" + str(total_billing_per_of_job_cost) + "%)"

            # Find income account for progressive billing product
            account_id, product_id = invoice_line_obj.find_progressive_retention_income_account(order, "progressive")
            if account_id:
                prd_account_id = account_id
            else:
                prd_account_id = self._default_account()

            if product_id:
                prd_product_id = product_id
            else:
                prd_product_id = False

            # Create Invoice line
            curr_invoice_line = {
                'name': "Progressive Billing at " + str(progressive_bill) + "%",
                'price_unit': total_order_amount,
                'quantity': 1.0,
                'product_id': prd_product_id,
                'account_id': prd_account_id,
                'invoice_id': inv_ids.id,
                'billing': progressive_bill,
                'sale_order_ref_id': order.id,
                'billing_for_calculate': progressive_bill_for_calculate,
                'previously_invoiced_amount': previously_invoiced_amount,
                'total_downpayment_paid': float(total_downpayment_paid_of_so),
                'total_amount_paid': float(total_amount_paid_of_job_cost),
            }
            invoice_line_obj.create(curr_invoice_line)
            invoice_line_obj._compute_price()
        return res

    @api.multi
    def generate_retention_rate_invoice(self, sale_orders):
        invoice_obj = self.env["account.invoice"]
        invoice_line_obj = self.env["account.invoice.line"]
        res = {}

        for order in sale_orders:
            # Create Invoice

            total_order_amount = order.amount_total

            retention_rate = order.retention_per

            curr_invoice = {
                'partner_id': order.partner_id.id,
                'account_id': order.partner_id.property_account_receivable_id.id,
                'state': 'draft', 'type': 'out_invoice',
                'date_invoice': datetime.datetime.now(),
                'origin': order.name,
                'retention_per': retention_rate,
                'target': 'new'
            }

            inv_ids = invoice_obj.create(curr_invoice)

            # Find income account for retention product
            account_id, product_id = invoice_line_obj.find_progressive_retention_income_account(order, "retention")
            if account_id:
                prd_account_id = account_id
            else:
                prd_account_id = self._default_account()

            if product_id:
                prd_product_id = product_id
            else:
                prd_product_id = False

            # Create Invoice line
            curr_invoice_line = {
                'name': "Retention Rate at " + str(retention_rate) + "%",
                'product_id': prd_product_id,
                'price_unit': float(total_order_amount) * float(retention_rate)/100,
                'quantity': 1.0,
                'account_id': prd_account_id,
                'invoice_id': inv_ids.id,
            }
            invoice_line_obj.create(curr_invoice_line)
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    sale_order_ref_id = fields.Many2one('sale.order', string='Sale Order Ref', index=True)
    retention_per = fields.Float(string='Retention %', related='invoice_id.retention_per', store=True)
    is_down_payment = fields.Boolean(string="Is Down payment invoice", default=lambda *a: False)
    total_downpayment_paid = fields.Float(string='Total Downpayment Paid')
    total_amount_paid = fields.Float(string='Total Paid Amount', digits=dp.get_precision('Account'))

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity', 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id', 'invoice_id.date_invoice', 'invoice_id.date', 'job_cost', 'billing')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        subtotal_price = self.price_subtotal
        if self.job_cost:
            if self.billing_for_calculate and self.billing_for_calculate > 0:
                self.price_subtotal = subtotal_price * float(self.billing_for_calculate) / 100
                price_subtotal_signed = subtotal_price * float(self.billing_for_calculate) / 100
        if self.sale_order_ref_id:
            if self.billing_for_calculate and self.billing_for_calculate >= 0:
                if self.retention_per and self.retention_per > 0:
                    self.price_subtotal = (((subtotal_price * float(self.billing_for_calculate) / 100) - (self.total_downpayment_paid * float(self.billing_for_calculate) / 100)) - (
                                subtotal_price * float(self.retention_per) / 100)) - float(self.total_amount_paid)
                    price_subtotal_signed = (((subtotal_price * float(self.billing_for_calculate) / 100) - (self.total_downpayment_paid * float(self.billing_for_calculate) / 100)) - (
                                subtotal_price * float(self.retention_per) / 100)) - float(self.total_amount_paid)
                else:
                    self.price_subtotal = ((subtotal_price * float(self.billing_for_calculate) / 100) - (self.total_downpayment_paid * float(self.billing_for_calculate) / 100)) - float(self.total_amount_paid)
                    price_subtotal_signed = ((subtotal_price * float(self.billing_for_calculate) / 100) - (self.total_downpayment_paid * float(self.billing_for_calculate) / 100)) - float(self.total_amount_paid)

        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    @api.multi
    def find_progressive_retention_income_account(self, order, product_type=""):
        ir_property_obj = self.env['ir.property']
        if product_type == "progressive":
            progressive_id = self.env.ref('so_progress_billing.so_progress_bill_product_progress_bill')
            product_id = progressive_id
        elif product_type == "retention":
            progressive_id = self.env.ref('so_progress_billing.so_progress_bill_product_retention_rate')
            product_id = progressive_id
        else:
            product_id = False

        account_id = False
        if product_id.id:
            account_id = product_id.property_account_income_id.id or product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _(
                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (product_id.name,))

        product_id_to_return = product_id.id

        return account_id, product_id_to_return


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()

        # Save total invoiced percentage value for selected job cost/sales order item.
        for inv in self:
            if inv.invoice_line_ids:
                for line in inv.invoice_line_ids:
                    if line.job_cost:
                        existing_completed_invoice = line.job_cost.total_invoice_amount_paid
                        new_amount = float(line.price_subtotal) + float(existing_completed_invoice)
                        line.job_cost.write({'total_invoiced_per': line.billing, 'total_invoice_amount_paid': new_amount})
                    elif line.sale_order_ref_id and not line.is_down_payment:
                        existing_completed_invoice = line.sale_order_ref_id.total_invoice_amount_paid
                        new_amount = float(line.price_subtotal) + float(existing_completed_invoice)
                        line.sale_order_ref_id.write({'total_invoiced_per': line.billing, 'total_invoice_amount_paid': new_amount})
                    elif line.sale_order_ref_id and line.is_down_payment:
                        existing_completed_invoice = line.sale_order_ref_id.total_down_payment_paid
                        new_amount = float(line.price_subtotal) + float(existing_completed_invoice)
                        line.sale_order_ref_id.write({'total_down_payment_paid': new_amount})

        return to_open_invoices.invoice_validate()





