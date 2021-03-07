# -*- coding: utf-8 -*-
from openerp import _
from openerp import SUPERUSER_ID
from openerp import models, fields, api
from openerp.osv import osv
from dateutil.relativedelta import relativedelta
from openerp import exceptions
import datetime as dt
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import calendar
from openerp.exceptions import UserError
import logging

from odoo import registry
from odoo import models as modelx
from odoo import fields as fieldx
from odoo import api as apix

_logger = logging.getLogger(__name__)

""" this method add months to a date and return tuple of date """


def add_months(source_date, subtracted_months):
        month = source_date.month - 1 + subtracted_months
        year = int(source_date.year + month / 12)
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return dt.datetime(year, month, day, 23, 59)


class planif_invoice_sale_order(models.Model):
    _name = 'planif.invoice.sale.order'

    @api.model
    def action_planif(self,context={}):
        """
        Function to process the recurrencing Sale Orders
        """
        try:
            cr = registry(self._cr.dbname).cursor()
            uid = SUPERUSER_ID
            current_datetime = dt.datetime.now().date()
            current_datetime_str = current_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            monthly_date1 = add_months(current_datetime, -1)
            quarter_date1 = add_months(current_datetime, -3)
            halfyear_date1 = add_months(current_datetime, -6)
            yearly_date1 = add_months(current_datetime, -12)
            so_obj = self.env['sale.order']

            so_ids = so_obj.search([
                ('subscription', '=', True),
                ('subscription_terminated', '=', False),
                ('state', '=', 'done'),
            ])

            for so in so_ids:
                context = {'email_to': so['mail_to_client_string'],
                           'attachment_ids': so['invoice_report'],
                           'is_subscription_mail': True,
                           'email_cc': so['mail_cc_client_string']}
                _logger.info("after context")
                if so['periodicity'] == 'month':
                    date_test1 = monthly_date1.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                elif so['periodicity'] == 'quarter':
                    date_test1 = quarter_date1.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                elif so['periodicity'] == 'half-year':
                    date_test1 = halfyear_date1.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                elif so['periodicity'] == 'yearly':
                    date_test1 = yearly_date1.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                else:
                    date_test1 = add_months(current_datetime, -12)[0]

                _logger.info("action_planif SO to invoice: " + str(so['name']) + "  -  " + str(so['periodicity']))
                _logger.info("action_planif SO to invoice Dates: " + str(date_test1))

                if current_datetime_str <= so['start_date']:
                    _logger.info("No need to ivnoice: ")
                else:
                    inv_obj = self.env['account.invoice']
                    inv_ids = inv_obj.search( [
                                        ('origin', '=', so['name']),
                                        ('create_date', '>=', date_test1),
                                        ('state', 'in', ['open', 'paid'])
                                      ])
                    if len(inv_ids) == 0 and so._renew_policy_active(current_datetime_str):
                        _logger.info("No invoices in period => Need to invoice again !")
                        inv = so.invoice_create()
                        invx = inv_obj.browse(inv)
                        invx.action_date_assign()
                        invx.action_move_create()
                        context.setdefault('active_ids', inv)
                        self.env['account.invoice.confirm'].invoice_confirm()
                        if so['send_fact']:
                            _logger.info("Need to Send it by mail !")
                            invx.send_invoice_contract()
                        else:
                            _logger.info("No need to mail invoice !")
                    else:
                        _logger.info("action_planif SO to invoices: " + str(invx) + " => No Need to invoice again !")

            return True
        except Exception as usrError:
            _logger.error("action_planif UserError: " + str(usrError))
            pass


class AccountAnalyticLine(osv.Model):
    _inherit = 'account.analytic.line'

    def _get_sale_order_line_vals(self):
        order = self.env['sale.order'].search([('project_id', '=', self.account_id.id)], limit=1)
        if not order:
            return False
        if order.state != 'sale':
            if order.subscription != True:
                raise UserError(_('The Sale Order %s linked to the Analytic Account must be validated before registering expenses.') % order.name)

        last_so_line = self.env['sale.order.line'].search([('order_id', '=', order.id)], order='sequence desc', limit=1)
        last_sequence = last_so_line.sequence + 1 if last_so_line else 100

        fpos = order.fiscal_position_id or order.partner_id.property_account_position_id
        taxes = fpos.map_tax(self.product_id.taxes_id)
        price = self._get_invoice_price(order)

        return {
            'order_id': order.id,
            'name': self.name,
            'sequence': last_sequence,
            'price_unit': price,
            'tax_id': [x.id for x in taxes],
            'discount': 0.0,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': 0.0,
            'qty_delivered': self.unit_amount,
        }



class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    def send_invoice_contract(self, cr, uid, ids, context=None):
        data_pool = self.pool['ir.model.data']
        mailmess_pool = self.pool['mail.message']
        mail_pool = self.pool['mail.mail']
        template_pool = self.pool['mail.template']

        try:
            dummy, template_id = data_pool.get_object_reference(cr, uid, 'odoo-report_darbtech', 'email_template_invoice_dyn')
        except ValueError:
            dummy, template_id = data_pool.get_object_reference(cr, uid, 'account', 'email_template_edi_invoice')

        inv_datas = self.browse(cr, uid, ids, context)
        _logger.info("Send action_send_contract_invoice ! self.partner " + str(inv_datas))

        user = inv_datas[0].partner_id[0].user_id
        if not inv_datas[0].partner_id[0].email:
            raise UserError(_("Cannot send email: user %s has no email address.") % user.name)
        if context:
            context['lang'] = user.lang
        else:
            context = {'lang': user.lang}
        _logger.info("Click Send action_send_contract_report ! template_id " + str(template_id))
        mail_id = template_pool.send_mail(cr, SUPERUSER_ID, template_id, ids[0], force_send=True, raise_exception=True, context=context)


class SaleSubscriptionSettings(modelx.TransientModel):
    _inherit = 'sale.config.settings'
    _name = 'sale.config.settings'

    invoice_report_setting = fieldx.Many2one('ir.actions.report.xml', string="Default Invoices report", domain="[('model','=','account.invoice')]")
    default_auto_renew_policy = fieldx.Selection([
                                  ('end', "Terminate at the end of engagement"),
                                  ('renew', "Automatic renewal  with init duration "),
                                  ('infinite', "Continue without engagement"),
                              ], string='Auto renew policy', index=True, default_model='sale.order')
    dft_mail_cci_client = fieldx.Many2many('res.partner', relation='tablex')

    @api.multi
    def set_invoice_report_setting(self):
        #invoice_report_id = self.browse(cr, uid, ids, context=context).invoice_report_setting
        invoice_report_id = self.invoice_report_setting
        res = self.env['ir.values'].sudo().set_default('sale.config.settings', 'invoice_report_setting', invoice_report_id.id)
        return res

    @api.multi
    def set_dft_mail_cci_client(self):
        cci_mails_list = []
        #for variable in self.browse(cr, uid, ids, context=context).dft_mail_cci_client:
        for variable in self.dft_mail_cci_client:
            cci_mails_list.append(variable.id)
        self.env['ir.values'].sudo().set_default('sale.config.settings', 'dft_mail_cci_client', cci_mails_list)
        return cci_mails_list

    _defaults = {
        'auto_renew_policy': default_auto_renew_policy,
    }

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'
    auto_end_subscription_date = fields.Date(compute='_compute_auto_end_subscription_date')
    subscription = fields.Boolean()
    start_date = fields.Date()
    confirmation_date = fields.Date()
    send_fact = fields.Boolean()
    end_subscription_date = fields.Date()
    subscription_terminated = fields.Boolean(default=False)
    periodicity = fields.Selection([
        ('month', "Month"),
        ('quarter', "Quarter"),
        ('half-year', "Half Year"),
        ('yearly', "Yearly"),
    ], string='Periodicity', index=True, default='month')
    subscription_duration = fields.Integer(help="Duration in months")
    to_invoice_contract = fields.Boolean(compute="_compute_to_invoice_contract")

    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice'),
        ('not_started', '*** Contractual invoicing: Subscription not yet started ***'),
        ('active_contractual', '*** Contractual Invoicing: Active Subscription ***'),
        ('inactive_contractual', '*** Contractual Invoicing: Inactive Subscription ***')
        ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True, default='no')

    mail_cc_client = fields.Many2many('res.partner', relation='table_name')
    mail_to_client = fields.Many2many('res.partner', relation='table_name2')
    mail_to_client_string = fields.Char(compute='_compute_to_cc_client')
    mail_cc_client_string = fields.Char(compute='_compute_to_cc_client')
    invoice_report = fields.Many2one('ir.actions.report.xml', string="Invoices report", domain="[('model','=','account.invoice')]", default=lambda self: self.env['ir.actions.report.xml'].browse(self.env['ir.values'].get_default('sale.config.settings', 'invoice_report_setting')))
    auto_renew_policy = fields.Selection([
                                ('end', "Terminate at the end of engagement"),
                                ('renew', "Automatic renewal  with init duration "),
                                ('infinite', "Continue without engagement"),
                           ], string='Auto renew policy', index=True)

    @api.multi
    def _renew_policy_active(self, current_datetime):

            if self.auto_renew_policy == 'end' and self.auto_end_subscription_date <= current_datetime:
                self.subscription_terminated = True
                self.end_subscription_date = current_datetime
                return False
            elif self.auto_renew_policy == 'renew' and self.auto_end_subscription_date <= current_datetime:
                self.start_date = dt.datetime.now().date()
                return True
            else:
                return True

    @api.multi
    def _compute_to_cc_client(self):

        for sale_order in self:
            to_clients = " "
            cc_clients = " "
            for client in sale_order.mail_to_client:
                to_clients += "%s <%s>;" % (client.name, client.email)
            sale_order.update({'mail_to_client_string': to_clients})
            for client in sale_order.mail_cc_client:
                cc_clients += "%s <%s>;" % (client.name, client.email)
            if self.env['ir.values'].get_default('sale.config.settings', 'dft_mail_cci_client'):
                for client_id in self.env['ir.values'].get_default('sale.config.settings', 'dft_mail_cci_client'):
                    cci_client = self.env['res.partner'].browse(client_id)
                    cc_clients += "%s <%s>;" % (cci_client.name, cci_client.email)
            sale_order.update({'mail_cc_client_string': cc_clients})

    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            order.start_date = dt.datetime.now().date()
            order.confirmation_date = dt.datetime.now().date()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            order.order_line._action_procurement_create()
            if not order.project_id:
                for line in order.order_line:
                    if line.product_id.invoice_policy == 'cost':
                        order._create_analytic_account()
                        break
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True

    @api.depends('state', 'order_line.invoice_status')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        for order in self:
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id')
            # Search for refunds as well
            refund_ids = self.env['account.invoice'].browse()
            if invoice_ids:
                refund_ids = refund_ids.search([('type', '=', 'out_refund'), ('origin', 'in', invoice_ids.mapped('number')), ('origin', '!=', False)])

            line_invoice_status = [line.invoice_status for line in order.order_line]

            if order.state not in ('sale', 'done'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                invoice_status = 'upselling'
            else:
                invoice_status = 'no'
            if order.subscription:
                if order.subscription_terminated:
                    invoice_status = 'inactive_contractual'
                elif order.state =='done':
                    invoice_status = 'active_contractual'
                else:
                    invoice_status = 'not_started'
            order.update({
                'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })

    @api.multi
    def _compute_to_invoice_contract(self):
        for so in self:
            if not so.subscription:
                so.to_invoice_contract = False
            else:
                # Calcul sur les dates...
                so.to_invoice_contract = True
        return True

    @api.multi
    def invoice_create(self):
        sale_orders = self
        _logger.info("Invoice_create: sale orders " + str(sale_orders))
        created_invoice = sale_orders.action_invoice_create()
        _logger.info("Invoice_create: created invoices " + str(created_invoice))
        return created_invoice

    @api.multi
    def _create_invoice_contract(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            prop_id = prop and prop.id or False
            account_id = order.fiscal_position_id.map_account(prop_id)
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') % \
                    (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
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
                'invoice_line_tax_ids': [(6, 0, [x.id for x in self.product_id.taxes_id])],
                'account_analytic_id': order.project_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
        })
        invoice.compute_taxes()
        return invoice

    @api.depends('start_date', 'periodicity', 'subscription_duration')
    def _compute_auto_end_subscription_date(self):
        current_datetime = dt.datetime.now().date()
        for so in self:
            if so['start_date']:
                date_start_dt = fields.Datetime.from_string(so.start_date)
            else:
                date_start_dt = current_datetime

            if so.periodicity == 'quarter':
                dat = date_start_dt + relativedelta(months=so.subscription_duration * 3)
            elif so.periodicity == 'half-year':
                dat = date_start_dt + relativedelta(months=so.subscription_duration * 6)
            elif so.periodicity == 'yearly':
                dat = date_start_dt + relativedelta(months=so.subscription_duration * 12)
            else:
                dat = date_start_dt + relativedelta(months=so.subscription_duration)
            so.auto_end_subscription_date = dat

    @api.onchange('subscription_terminated')
    def _onchange_price(self):
        self.end_subscription_date = dt.datetime.now().date()
    @api.one
    @api.constrains('start_date', 'subscription_duration')
    def _check_fields_constraints(self):
        if self.subscription:
            if self.subscription_duration <= 0:
                raise exceptions.ValidationError("Subscription duration must be greater than 0")
            if self.confirmation_date and self.start_date < self.confirmation_date:
                if self.state not in ('draft', 'sent'):
                    raise exceptions.ValidationError("Start date must be greater than or equal confirmation date")
            elif self.start_date < dt.datetime.now().date().isoformat():
                if self.state not in ('draft', 'sent'):
                    raise exceptions.ValidationError("Start date must be greater than or equal today")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """

        for line in self:
            if line.order_id.subscription:
                print 'QTY TO INVOICE: IS RECURRENT ' + str(line.product_uom_qty)
                line.qty_to_invoice = line.product_uom_qty
            elif line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
