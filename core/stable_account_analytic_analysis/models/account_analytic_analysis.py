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
from dateutil.relativedelta import relativedelta
import datetime
import logging
import time

from odoo import models, fields, api
from odoo.exceptions import except_orm
from odoo import tools
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

class account_analytic_invoice_line(models.Model):
    _name = 'account.analytic.invoice.line'

    @api.multi
    def _amount_line(self):
        for line in self:
            price_subtotal = line.quantity * line.price_unit
            if line.analytic_account_id.pricelist_id:
                cur = line.analytic_account_id.pricelist_id.currency_id
                price_subtotal = cur.round(price_subtotal)
            line.price_subtotal = price_subtotal

    product_id          = fields.Many2one('product.product', 'Product', required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', ondelete='cascade')
    name                = fields.Text('Description', required=True)
    quantity            = fields.Float('Quantity', required=True, default=1)
    uom_id              = fields.Many2one('product.uom', 'Unit of Measure',required=True)
    price_unit          = fields.Float('Unit Price', required=True)
    price_subtotal      = fields.Float(compute='_amount_line', string='Sub Total')

    @api.onchange('product_id')
    def product_id_change(self):
        context = self.env.context or {}
        uom_obj = self.env['product.uom']

        # local_context = dict(context, company_id=company_id, force_company=company_id, pricelist=pricelist_id)

        if not self.product_id:
            self.price_unit = 0.0
            return {'domain': {
                'product_uom': []
            }}
        if self.analytic_account_id and self.analytic_account_id.partner_id:
            part = self.analytic_account_id.partner_id

        result = {}
        res = self.product_id
        price = False
        if self.price_unit is not False:
            price = self.price_unit
        elif self.pricelist_id:
            price = res.price
        if price is False:
            price = res.list_price
        if not self.name:
            name = self.product_id.name_get()[0][1]
            if res.description_sale:
                name += '\n' + res.description_sale
        result.update({
            'name'      : name or False,
            'uom_id'    : self.uom_id or res.uom_id.id or False,
            'price_unit': price
        })
        res_final = {
            'value': result
        }
        if result['uom_id'] != res.uom_id.id:
            selected_uom = uom_obj.browse(result['uom_id'])
            new_price = uom_obj._compute_price(res.uom_id.id, res_final['value']['price_unit'], result['uom_id'])
            res_final['value']['price_unit'] = new_price
        return res_final

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    def _analysis_all(self):
        dp = 2
        parent_ids = tuple(self._ids) #We don't want consolidation for each of these fields because those complex computation is resource-greedy.

        for record in self:
            # user_ids
            self.env.cr.execute('SELECT MAX(id) FROM res_users')
            max_user = self.env.cr.fetchone()[0]
            if parent_ids:
                self.env.cr.execute('SELECT DISTINCT("user") FROM account_analytic_analysis_summary_user ' \
                           'WHERE account_id IN %s', (parent_ids,))
                result = self.env.cr.fetchall()
            else:
                result = []
            record.user_ids = [int((record.id * max_user) + x[0]) for x in result]

            # month_ids
            if parent_ids:
                self.env.cr.execute('SELECT DISTINCT(month) FROM account_analytic_analysis_summary_month ' \
                           'WHERE account_id IN %s', (parent_ids,))
                result = self.env.cr.fetchall()
            else:
                result = []
            record.month_ids = [int(record.id * 1000000 + int(x[0])) for x in result]

            # last_worked_invoiced_date
            if parent_ids:
                self.env.cr.execute("SELECT account_analytic_line.account_id, MAX(date) \
                        FROM account_analytic_line \
                        WHERE account_id IN %s \
                            AND invoice_id IS NOT NULL \
                        GROUP BY account_analytic_line.account_id;", (parent_ids,))
                for account_id, sum in self.env.cr.fetchall():
                    if account_id not in self._ids:
                        record.last_worked_invoiced_date = {}
                    record.last_worked_invoiced_date = sum

            # ca_to_invoice
            ca_to_invoice = 0.0
            self.env.cr.execute("""
                SELECT product_id, sum(amount), user_id, to_invoice, sum(unit_amount), product_uom_id, line.name
                FROM account_analytic_line line
                WHERE account_id = %s
                    AND invoice_id IS NULL
                    AND to_invoice IS NOT NULL
                GROUP BY product_id, user_id, to_invoice, product_uom_id, line.name""", (record.id,))

            ca_to_invoice = 0.0
            for product_id, price, user_id, factor_id, qty, uom, description in self.env.cr.fetchall():
                price = -price
                if product_id:
                    price = self.env['account.analytic.line']._get_invoice_price(record, product_id, user_id, qty)
                factor = self.env['hr_timesheet_invoice.factor'].browse(factor_id)
                ca_to_invoice += price * qty * (100-factor.factor or 0.0) / 100.0

            # sum both result on account_id
            record.ca_to_invoice = round(ca_to_invoice, 2)

            # last_invoice_date
            last_invoice_date = False
            if parent_ids:
                self.env.cr.execute ("SELECT account_analytic_line.account_id, \
                            DATE(MAX(account_invoice.date_invoice)) \
                        FROM account_analytic_line \
                        JOIN account_invoice \
                            ON account_analytic_line.invoice_id = account_invoice.id \
                        WHERE account_analytic_line.account_id = %s \
                            AND account_analytic_line.invoice_id IS NOT NULL \
                        GROUP BY account_analytic_line.account_id",(record.id,))
                for account_id, lid in self.env.cr.fetchall():
                    record.last_invoice_date = lid

            # last_worked_date
            if parent_ids:
                self.env.cr.execute("SELECT account_analytic_line.account_id, MAX(date) \
                        FROM account_analytic_line \
                        WHERE account_id = %s \
                            AND invoice_id IS NULL \
                        GROUP BY account_analytic_line.account_id",(record.id,))
                for account_id, lwd in self.env.cr.fetchall():
                    record.last_worked_date = lwd
            # hours_qtt_non_invoiced
            if parent_ids:
                self.env.cr.execute("SELECT account_analytic_line.account_id, COALESCE(SUM(unit_amount), 0.0) \
                        FROM account_analytic_line \
                        WHERE account_analytic_line.account_id = %s \
                            AND invoice_id IS NULL \
                            AND to_invoice IS NOT NULL \
                        GROUP BY account_analytic_line.account_id;",(record.id,))
                for account_id, sua in self.env.cr.fetchall():
                    record.hours_qtt_non_invoiced = round(sua, dp)

            # hours_quantity
            if parent_ids:
                self.env.cr.execute("SELECT account_analytic_line.account_id, COALESCE(SUM(unit_amount), 0.0) \
                        FROM account_analytic_line \
                        WHERE account_analytic_line.account_id = %s \
                        GROUP BY account_analytic_line.account_id",(record.id,))
                ff =  self.env.cr.fetchall()
                for account_id, hq in ff:
                    record.hours_quantity = round(hq, dp)

            # ca_theorical
            # Warning
            # This computation doesn't take care of pricelist !
            # Just consider list_price
            if parent_ids:
                self.env.cr.execute("""SELECT account_analytic_line.account_id AS account_id, \
                            COALESCE(SUM((account_analytic_line.unit_amount * pt.list_price) \
                                - (account_analytic_line.unit_amount * pt.list_price \
                                    * hr.factor)), 0.0) AS somme
                        FROM account_analytic_line \
                        JOIN product_product pp \
                            ON (account_analytic_line.product_id = pp.id) \
                        JOIN product_template pt \
                            ON (pp.product_tmpl_id = pt.id) \
                        JOIN account_analytic_account a \
                            ON (a.id=account_analytic_line.account_id) \
                        JOIN hr_timesheet_invoice_factor hr \
                            ON (hr.id=a.to_invoice) \
                    WHERE account_analytic_line.account_id = %s \
                        AND a.to_invoice IS NOT NULL \
                    GROUP BY account_analytic_line.account_id""",(record.id,))
                for account_id, sum in self.env.cr.fetchall():
                    record.ca_theorical = round(sum, dp)

    @api.multi
    def _ca_invoiced_calc(self):
        res = {}
        res_final = {}
        child_ids = tuple(self._ids) #We don't want consolidation for each of these fields because those complex computation is resource-greedy.
        for i in child_ids:
            res[i] =  0.0
        if not child_ids:
            return res

        if child_ids:
            #Search all invoice lines not in cancelled state that refer to this analytic account
            inv_line_obj = self.env["account.invoice.line"]
            inv_lines = inv_line_obj.search(['&', ('account_analytic_id', 'in', child_ids),
                                             ('invoice_id.state', 'not in', ['draft', 'cancel']),
                                             ('invoice_id.type', 'in', ['out_invoice', 'out_refund'])])
            for line in inv_lines:
                if line.invoice_id.type == 'out_refund':
                    res[line.account_analytic_id.id] -= line.price_subtotal
                else:
                    res[line.account_analytic_id.id] += line.price_subtotal

        for acc in self:
            acc.ca_invoiced = res[acc.id] - (acc.timesheet_ca_invoiced or 0.0)

    @api.multi
    def _total_cost_calc(self):
        res = {}
        res_final = {}
        child_ids = tuple(self._ids) #We don't want consolidation for each of these fields because those complex computation is resource-greedy.
        for i in child_ids:
            res[i] =  0.0
        if not child_ids:
            return res
        if child_ids:
            self.env.cr.execute("""SELECT account_analytic_line.account_id, COALESCE(SUM(amount), 0.0) \
                    FROM account_analytic_line \
                    WHERE account_analytic_line.account_id IN %s \
                        AND amount<0 \
                    GROUP BY account_analytic_line.account_id""",(child_ids,))
            for account_id, sum in self.env.cr.fetchall():
                res[account_id] = round(sum,2)

        for record in self:
            record.total_cost = res[record.id]

    @api.multi
    def _remaining_hours_calc(self):
        res = {}
        for account in self:
            if account.quantity_max != 0:
                res[account.id] = account.quantity_max - account.hours_quantity
            else:
                res[account.id] = 0.0
        for account in self:
            account.remaining_hours = round(res.get(id, 0.0),2)

    @api.multi
    def _remaining_hours_to_invoice_calc(self):
        for account in self:
            account.remaining_hours_to_invoice = max(account.hours_qtt_est - account.timesheet_ca_invoiced, account.ca_to_invoice)

    @api.multi
    def _hours_qtt_invoiced_calc(self):
        res = {}
        for account in self:
            res[account.id] = account.hours_quantity - account.hours_qtt_non_invoiced
            if res[account.id] < 0:
                res[account.id] = 0.0
        for id in self._ids:
            res[id] = round(res.get(id, 0.0),2)

        for account in self:
            account.hours_qtt_invoiced = res[account.id]

    @api.multi
    def _revenue_per_hour_calc(self):
        res = {}
        for account in self:
            if account.hours_qtt_invoiced == 0:
                res[account.id]=0.0
            else:
                res[account.id] = account.ca_invoiced / account.hours_qtt_invoiced

        for account in self:
            account.revenue_per_hour = round(res.get(id, 0.0),2)

    @api.multi
    def _real_margin_rate_calc(self):
        res = {}
        for account in self:
            if account.ca_invoiced == 0:
                res[account.id]=0.0
            elif account.total_cost != 0.0:
                res[account.id] = -(account.real_margin / account.total_cost) * 100
            else:
                res[account.id] = 0.0
        for account in self:
            account.real_margin_rate = round(res.get(id, 0.0), 2)

    @api.multi
    def _fix_price_to_invoice_calc(self):
        sale_obj = self.env['sale.order']
        res = {}
        for account in self:
            res[account.id] = 0.0
            sales = sale_obj.search([('project_id','=', account.id), ('state', '=', 'manual')])
            for sale in sales:
                res[account.id] += sale.amount_untaxed
                for invoice in sale.invoice_ids:
                    if invoice.state != 'cancel':
                        res[account.id] -= invoice.amount_untaxed
            account.fix_price_to_invoice = res[account.id]

    @api.multi
    def _timesheet_ca_invoiced_calc(self):
        lines_obj = self.env['account.analytic.line']
        res = {}
        inv_ids = []
        for account in self:
            res[account.id] = 0.0
            lines = lines_obj.search([('account_id','=', account.id), ('invoice_id','!=',False), ('invoice_id.state', 'not in', ['draft', 'cancel']), ('to_invoice','!=', False), ('invoice_id.type', 'in', ['out_invoice', 'out_refund'])])
            for line in lines:
                if line.invoice_id not in inv_ids:
                    inv_ids.append(line.invoice_id)
                    if line.invoice_id.type == 'out_refund':
                        res[account.id] -= line.invoice_id.amount_untaxed
                    else:
                        res[account.id] += line.invoice_id.amount_untaxed
            account.timesheet_ca_invoiced = res[account.id]

    @api.multi
    def _remaining_ca_calc(self):
        res = {}
        for account in self:
            account.remaining_ca = max(account.amount_max - account.ca_invoiced, account.fix_price_to_invoice)

    @api.multi
    def _real_margin_calc(self):
        for account in self:
            real_margin = account.ca_invoiced + account.total_cost
            account.real_margin = round(real_margin, 2)

    @api.multi
    def _theorical_margin_calc(self):
        res = {}
        for account in self:
            theorical_margin = account.ca_theorical + account.total_cost
            account.theorical_margin = round(theorical_margin, 2)

    @api.multi
    def _is_overdue_quantity(self):
        for record in self:
            if record.quantity_max > 0.0:
                record.is_overdue_quantity = int(record.hours_quantity > record.quantity_max)
            else:
                record.is_overdue_quantity = 0

    @api.multi
    def _get_analytic_account(self, cr, uid, ids, context=None):
        result = set()
        for line in self.pool.get('account.analytic.line').browse(cr, uid, ids, context=context):
            result.add(line.account_id.id)
        return list(result)

    @api.model
    def _get_total_estimation(self, account):
        tot_est = 0.0
        if account.fix_price_invoices:
            tot_est += account.amount_max 
        if account.invoice_on_timesheets:
            tot_est += account.hours_qtt_est
        return tot_est

    @api.model
    def _get_total_invoiced(self, account):
        total_invoiced = 0.0
        if account.fix_price_invoices:
            total_invoiced += account.ca_invoiced
        if account.invoice_on_timesheets:
            total_invoiced += account.timesheet_ca_invoiced
        return total_invoiced

    @api.model
    def _get_total_remaining(self, account):
        total_remaining = 0.0
        if account.fix_price_invoices:
            total_remaining += account.remaining_ca
        if account.invoice_on_timesheets:
            total_remaining += account.remaining_hours_to_invoice
        return total_remaining

    @api.model
    def _get_total_toinvoice(self, account):
        total_toinvoice = 0.0
        if account.fix_price_invoices:
            total_toinvoice += account.fix_price_to_invoice
        if account.invoice_on_timesheets:
            total_toinvoice += account.ca_to_invoice
        return total_toinvoice

    @api.multi
    def _sum_of_fields(self):
        for account in self:
            account.est_total       = self._get_total_estimation(account)
            account.invoiced_total  = self._get_total_invoiced(account)
            account.remaining_total = self._get_total_remaining(account)
            account.toinvoice_total = self._get_total_toinvoice(account)

    is_project          = fields.Boolean('Is Project', default=False)
    is_overdue_quantity = fields.Boolean(compute='_is_overdue_quantity', string='Overdue Quantity')
    ca_invoiced = fields.Float(compute='_ca_invoiced_calc', string='Invoiced Amount',
            help="Total customer invoiced amount for this account.")
    total_cost = fields.Float(compute='_total_cost_calc', string='Total Costs',
            help="Total of costs for this account. It includes real costs (from invoices) and indirect costs, like time spent on timesheets.")
    ca_to_invoice = fields.Float(compute='_analysis_all', string='Uninvoiced Amount',
            help="If invoice from analytic account, the remaining amount you can invoice to the customer based on the total costs.")
    ca_theorical = fields.Float(compute='_analysis_all', string='Theoretical Revenue',
            help="Based on the costs you had on the project, what would have been the revenue if all these costs have been invoiced at the normal sale price provided by the pricelist.")
    hours_quantity = fields.Float(compute='_analysis_all', string='Total Worked Time',
            help="Number of time you spent on the analytic account (from timesheet). It computes quantities on all journal of type 'general'.")
    last_invoice_date = fields.Date(compute='_analysis_all', multi='analytic_analysis', type='date', string='Last Invoice Date',
            help="If invoice from the costs, this is the date of the latest invoiced.")
    last_worked_invoiced_date = fields.Date(compute='_analysis_all', string='Date of Last Invoiced Cost',
            help="If invoice from the costs, this is the date of the latest work or cost that have been invoiced.")
    last_worked_date = fields.Date(compute='_analysis_all', string='Date of Last Cost/Work',
            help="Date of the latest work done on this account.")
    hours_qtt_non_invoiced = fields.Float(compute='_analysis_all', string='Uninvoiced Time',
            help="Number of time (hours/days) (from journal of type 'general') that can be invoiced if you invoice based on analytic account.")
    hours_qtt_invoiced = fields.Float(compute='_hours_qtt_invoiced_calc', string='Invoiced Time',
            help="Number of time (hours/days) that can be invoiced plus those that already have been invoiced.")
    remaining_hours = fields.Float(compute='_remaining_hours_calc', string='Remaining Time',
            help="Computed using the formula: Maximum Time - Total Worked Time")
    remaining_hours_to_invoice = fields.Float(compute='_remaining_hours_to_invoice_calc', string='Remaining Time',
            help="Computed using the formula: Expected on timesheets - Total invoiced on timesheets")
    fix_price_to_invoice = fields.Float(compute='_fix_price_to_invoice_calc', string='Remaining Time',
            help="Sum of quotations for this contract.")
    timesheet_ca_invoiced = fields.Float(compute='_timesheet_ca_invoiced_calc', string='Remaining Time',
            help="Sum of timesheet lines invoiced for this contract.")
    remaining_ca = fields.Float(compute='_remaining_ca_calc', string='Remaining Revenue',
            help="Computed using the formula: Max Invoice Price - Invoiced Amount.")
    revenue_per_hour = fields.Float(compute='_revenue_per_hour_calc', string='Revenue per Time (real)',
            help="Computed using the formula: Invoiced Amount / Total Time")
    real_margin = fields.Float(compute='_real_margin_calc', type='float', string='Real Margin',
            help="Computed using the formula: Invoiced Amount - Total Costs.")
    theorical_margin = fields.Float(compute='_theorical_margin_calc', string='Theoretical Margin',
            help="Computed using the formula: Theoretical Revenue - Total Costs")
    real_margin_rate = fields.Float(compute='_real_margin_rate_calc', string='Real Margin Rate (%)',
            help="Computes using the formula: (Real Margin / Total Costs) * 100.")
    fix_price_invoices = fields.Boolean('Fixed Price')
    invoice_on_timesheets = fields.Boolean("On Timesheets")
    month_ids = fields.Many2many(compute='_analysis_all', type='many2many', relation='account_analytic_analysis.summary.month', string='Month')
    user_ids = fields.Many2many(compute='_analysis_all', type="many2many", relation='account_analytic_analysis.summary.user', string='User')
    hours_qtt_est = fields.Float('Estimation of Hours to Invoice')
    est_total = fields.Float(compute='_sum_of_fields', string="Total Estimation")
    invoiced_total = fields.Float(compute='_sum_of_fields', string="Total Invoiced")
    remaining_total = fields.Float(compute='_sum_of_fields', string="Total Remaining", help="Expectation of remaining income for this contract. Computed as the sum of remaining subtotals which, in turn, are computed as the maximum between '(Estimation - Invoiced)' and 'To Invoice' amounts")
    toinvoice_total = fields.Float(compute='_sum_of_fields', string="Total to Invoice", help=" Sum of everything that could be invoiced for this contract.")
    recurring_invoice_line_ids = fields.One2many('account.analytic.invoice.line', 'analytic_account_id', 'Invoice Lines', copy=True)
    recurring_invoices = fields.Boolean('Generate recurring invoices automatically')
    recurring_rule_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)')
    ], 'Recurrency', help="Invoice automatically repeat at specified interval")
    recurring_interval = fields.Integer('Repeat Every', help="Repeat every (Days/Week/Month/Year)")
    recurring_next_date = fields.Date('Date of Next Invoice')
    description = fields.Text('Description')
    use_timesheets = fields.Boolean('Timesheets', default=True, help="Check this field if this project manages timesheets")
    date_end = fields.Datetime('Expiration Date')
    manager_id = fields.Many2one('res.users', string='Account Manager')
    contract_type_id = fields.Many2one('account.analytic.account.contracttype', string='Contract Type')

    _defaults = {
        'recurring_interval': 1,
        'recurring_next_date': lambda *a: time.strftime('%Y-%m-%d'),
        'recurring_rule_type':'monthly'
    }

    @api.multi
    def open_sale_order_lines(self):
        context  = self.env.context
        sales = self.env['sale.order'].search([('project_id', '=', context.get('search_default_project_id', False)), ('partner_id', 'in', context.get('search_default_partner_id', False))])
        names = [record.name for record in self]
        name = _('Sales Order Lines to Invoice of %s') % ','.join(names)
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': context,
            'domain' : [('order_id','in', sales._ids)],
            'res_model': 'sale.order.line',
            'nodestroy': True,
        }

    @api.onchange('template_id')
    def on_change_template(self):
        if not self.template_id:
            return {}
        res = super(account_analytic_account, self).on_change_template()

        template = self.template_id
        
        if not self._ids:
            res['value']['fix_price_invoices'] = template.fix_price_invoices
            res['value']['amount_max'] = template.amount_max
        if not self._ids:
            res['value']['invoice_on_timesheets'] = template.invoice_on_timesheets
            res['value']['hours_qtt_est'] = template.hours_qtt_est
        
        if template.to_invoice.id:
            res['value']['to_invoice'] = template.to_invoice.id
        if template.pricelist_id.id:
            res['value']['pricelist_id'] = template.pricelist_id.id
        if not self._ids:
            invoice_line_ids = []
            for x in template.recurring_invoice_line_ids:
                invoice_line_ids.append((0, 0, {
                    'product_id': x.product_id.id,
                    'uom_id': x.uom_id.id,
                    'name': x.name,
                    'quantity': x.quantity,
                    'price_unit': x.price_unit,
                    'analytic_account_id': x.analytic_account_id and x.analytic_account_id.id or False,
                }))
            res['value']['recurring_invoices'] = template.recurring_invoices
            res['value']['recurring_interval'] = template.recurring_interval
            res['value']['recurring_rule_type'] = template.recurring_rule_type
            res['value']['recurring_invoice_line_ids'] = invoice_line_ids
        return res

    @api.onchange('recurring_invoices')
    def onchange_recurring_invoices(self):
        if self.date_start and self.recurring_invoices:
            self.recurring_next_date = self.date_start

    @api.model
    def cron_account_analytic_account(self):
        remind = {}

        def fill_remind(key, domain, write_pending=False):
            base_domain = [
                ('type', '=', 'contract'),
                ('partner_id', '!=', False),
                ('manager_id', '!=', False),
                ('manager_id.email', '!=', False),
            ]
            base_domain.extend(domain)

            accounts = self.search(base_domain, order='name asc')
            for account in accounts:
                if write_pending:
                    account.write({'state' : 'pending'})
                remind_user = remind.setdefault(account.manager_id.id, {})
                remind_type = remind_user.setdefault(key, {})
                remind_partner = remind_type.setdefault(account.partner_id, []).append(account)

        # Already expired
        fill_remind("old", [('state', 'in', ['pending'])])

        # Expires now
        fill_remind("new", [('state', 'in', ['draft', 'open']), '|', '&', ('date', '!=', False), ('date', '<=', time.strftime('%Y-%m-%d')), ('is_overdue_quantity', '=', True)], True)

        # Expires in less than 30 days
        fill_remind("future", [('state', 'in', ['draft', 'open']), ('date', '!=', False), ('date', '<', (datetime.datetime.now() + datetime.timedelta(30)).strftime("%Y-%m-%d"))])

        context = self.env.context
        context['base_url']  = self.env['ir.config_parameter'].get_param('web.base.url')
        context['action_id'] = self.env.ref('stable_account_analytic_analysis.action_account_analytic_overdue_all').id
        template = self.env.ref('stable_account_analytic_analysis.account_analytic_cron_email_template')
        for user_id, data in remind.items():
            context["data"] = data
            _logger.debug("Sending reminder to uid %s", user_id)
            template.with_context(context).send_mail(user_id, force_send=True)

        return True

    @api.onchange('invoice_on_timesheets')
    def onchange_invoice_on_timesheets(self):
        if not self.invoice_on_timesheets:
            self.to_invoice = False
        else:
            self.use_timesheets = True
            try:
                to_invoice = self.env.ref('stable_hr_timesheet_invoice.timesheet_invoice_factor1')
                self.to_invoice = to_invoice.id
            except ValueError:
                pass

    @api.multi
    def hr_to_invoice_timesheets(self):
        domain = [('invoice_id','=',False),('to_invoice','!=',False), ('journal_id.type', '=', 'general'), ('account_id', 'in', self._ids)]
        names = [record.name for record in self]
        name = _('Timesheets to Invoice of %s') % ','.join(names)
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain' : domain,
            'res_model': 'account.analytic.line',
            'nodestroy': True,
        }

    @api.model
    def _prepare_invoice_data(self, contract):
        context = self.env.context or {}

        journal_obj = self.pool.get('account.journal')
        fpos_obj = self.pool['account.fiscal.position']
        partner = contract.partner_id

        if not partner:
            raise except_orm(_('No Customer Defined!'),_("You must first select a Customer for Contract %s!") % contract.name )

        # fpos_id = self.env['account.fiscal.position'].get_fiscal_position(partner.id)
        fpos_id = self.env['account.fiscal.position'].with_context(force_company=contract.company_id.id).get_fiscal_position(partner.id)
        # journals = journal_obj.search([('type', '=','sale'),('company_id', '=', contract.company_id.id or False)], limit=1)
        # if not journals:
        #     raise except_orm(_('Error!'),
        #     _('Please define a sale journal for the company "%s".') % (contract.company_id.name or '', ))

        partner_payment_term = partner.property_payment_term_id and partner.property_payment_term_id.id or False

        currency_id = False
        if contract.pricelist_id:
            currency_id = contract.pricelist_id.currency_id.id
        elif partner.property_product_pricelist:
            currency_id = partner.property_product_pricelist.currency_id.id
        elif contract.company_id:
            currency_id = contract.company_id.currency_id.id

        invoice = {
           'account_id': partner.property_account_receivable_id and partner.property_account_receivable_id.id,
           'type': 'out_invoice',
           'partner_id': partner.id,
           'currency_id': currency_id,
           # 'journal_id': len(journals._ids) and journals._ids[0] or False,
           'date_invoice': contract.recurring_next_date,
           'origin': contract.code,
           'fiscal_position_id': fpos_id,
           'payment_term': partner_payment_term,
           'company_id': contract.company_id.id or False,
           'user_id': contract.manager_id.id or self.env._uid,
           'comment': contract.description,
        }
        return invoice

    @api.model
    def _prepare_invoice_line(self, line, fiscal_position):
        res = line.product_id
        account_id = res.property_account_income_id.id
        if not account_id:
            account_id = res.categ_id.property_account_income_categ_id.id
        account_id = fiscal_position.map_account(account_id)

        tax = line.product_id.taxes_id.filtered(lambda r: r.company_id == line.analytic_account_id.company_id)
        tax = fiscal_position.map_tax(tax)
        # taxes = res.taxes_id or False
        # tax_id = fiscal_position.map_tax(tax)
        values = {
            'name': line.name,
            'account_id': account_id,
            'account_analytic_id': line.analytic_account_id.id,
            'price_unit': line.price_unit or 0.0,
            'quantity': line.quantity,
            'uos_id': line.uom_id.id or False,
            'product_id': line.product_id.id or False,
            'invoice_line_tax_id': [(6, 0, tax.ids)],
        }
        return values

    @api.model
    def _prepare_invoice_lines(self, contract, fiscal_position_id):
        fiscal_position = self.env['account.fiscal.position'].browse(fiscal_position_id)
        invoice_lines = []
        for line in contract.recurring_invoice_line_ids:
            values = self._prepare_invoice_line(line, fiscal_position)
            invoice_lines.append((0, 0, values))
        return invoice_lines

    @api.model
    def _prepare_invoice(self, contract):
        invoice = self._prepare_invoice_data(contract)
        invoice['invoice_line_ids'] = self._prepare_invoice_lines(contract, invoice['fiscal_position_id'])
        return invoice

    @api.multi
    def recurring_create_invoice(self):
        return self._recurring_create_invoice()

    @api.model
    def _cron_recurring_create_invoice(self):
        accounts = self.browse([])
        accounts._recurring_create_invoice(automatic=True)

    @api.multi
    def _recurring_create_invoice(self, automatic=False):
        invoice_ids = []
        current_date =  time.strftime('%Y-%m-%d')
        if self._ids:
            contract_ids = self._ids
        else:
            contract_ids = self.search([('recurring_next_date','<=', current_date), ('state','=', 'open'), ('recurring_invoices','=', True), ('type', '=', 'contract')])._ids
        if contract_ids:
            self.env.cr.execute('SELECT company_id, array_agg(id) as ids FROM account_analytic_account WHERE id IN %s GROUP BY company_id', (tuple(contract_ids),))
            for company_id, ids in self.env.cr.fetchall():
                for contract in self.with_context({'company_id': company_id, 'force_company': company_id}).browse(ids):
                    try:
                        invoice_values = self._prepare_invoice(contract)
                        invoice_ids.append(self.env['account.invoice'].create(invoice_values))
                        next_date = datetime.datetime.strptime(contract.recurring_next_date or current_date, "%Y-%m-%d")
                        interval = contract.recurring_interval
                        if contract.recurring_rule_type == 'daily':
                            new_date = next_date+relativedelta(days=+interval)
                        elif contract.recurring_rule_type == 'weekly':
                            new_date = next_date+relativedelta(weeks=+interval)
                        elif contract.recurring_rule_type == 'monthly':
                            new_date = next_date+relativedelta(months=+interval)
                        else:
                            new_date = next_date+relativedelta(years=+interval)
                        contract.write({'recurring_next_date': new_date.strftime('%Y-%m-%d')})
                        if automatic:
                            self.env.cr.commit()
                    except Exception:
                        if automatic:
                            self.env.cr.rollback()
                            _logger.exception('Fail to create recurring invoice for contract %s', contract.code)
                        else:
                            raise
        return invoice_ids

class account_analytic_account_summary_user(models.Model):
    _name = "account_analytic_analysis.summary.user"
    _description = "Hours Summary by User"
    _order='user'
    # _auto = False
    _rec_name = 'user'

    @api.multi
    def _unit_amount(self):
        res = {}
        self.env.cr.execute('SELECT MAX(id) FROM res_users')
        max_user = self.env.cr.fetchone()[0]
        account_ids = [int(str(x/max_user - (x%max_user == 0 and 1 or 0))) for x in self._ids]
        user_ids = [int(str(x-((x/max_user - (x%max_user == 0 and 1 or 0)) *max_user))) for x in self._ids]
        parent_ids = tuple(account_ids) #We don't want consolidation for each of these fields because those complex computation is resource-greedy.
        if parent_ids:
            self.env.cr.execute('SELECT id, unit_amount ' \
                    'FROM account_analytic_analysis_summary_user ' \
                    'WHERE account_id IN %s ' \
                        'AND "user" IN %s',(parent_ids, tuple(user_ids),))
            for sum_id, unit_amount in self.env.cr.fetchall():
                res[sum_id] = unit_amount
        for record in self:
            record.unit_amount = round(res.get(id, 0.0), 2)

    account_id  = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    unit_amount = fields.Float('Total Time', compute='_unit_amount')
    user        = fields.Many2one('res.users', 'User')

    # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, 'account_analytic_analysis_summary_user')
    #     self.env.cr.execute('''CREATE OR REPLACE VIEW account_analytic_analysis_summary_user AS (
    #         with mu as
    #             (select max(id) as max_user from res_users)
    #         , lu AS
    #             (SELECT
    #              l.account_id AS account_id,
    #              coalesce(l.user_id, 0) AS user_id,
    #              SUM(l.unit_amount) AS unit_amount
    #          FROM account_analytic_line AS l,
    #              account_analytic_journal AS j
    #          WHERE (j.type = 'general' ) and (j.id=l.journal_id)
    #          GROUP BY l.account_id, l.user_id
    #         )
    #         select (lu.account_id::bigint * mu.max_user) + lu.user_id as id,
    #                 lu.account_id as account_id,
    #                 lu.user_id as "user",
    #                 unit_amount
    #         from lu, mu)''')

class account_analytic_account_summary_month(models.Model):
    _name = 'account_analytic_analysis.summary.month'
    _description = 'Hours summary by month'
    # _auto = False
    _rec_name = 'month'

    account_id  = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    unit_amount = fields.Float('Total Time')
    month       = fields.Char('Month', size=32, readonly=True)

    # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, 'account_analytic_analysis_summary_month')
    #     self.env.cr.execute('CREATE VIEW account_analytic_analysis_summary_month AS (' \
    #             'SELECT ' \
    #                 '(TO_NUMBER(TO_CHAR(d.month, \'YYYYMM\'), \'999999\') + (d.account_id  * 1000000::bigint))::bigint AS id, ' \
    #                 'd.account_id AS account_id, ' \
    #                 'TO_CHAR(d.month, \'Mon YYYY\') AS month, ' \
    #                 'TO_NUMBER(TO_CHAR(d.month, \'YYYYMM\'), \'999999\') AS month_id, ' \
    #                 'COALESCE(SUM(l.unit_amount), 0.0) AS unit_amount ' \
    #             'FROM ' \
    #                 '(SELECT ' \
    #                     'd2.account_id, ' \
    #                     'd2.month ' \
    #                 'FROM ' \
    #                     '(SELECT ' \
    #                         'a.id AS account_id, ' \
    #                         'l.month AS month ' \
    #                     'FROM ' \
    #                         '(SELECT ' \
    #                             'DATE_TRUNC(\'month\', l.date) AS month ' \
    #                         'FROM account_analytic_line AS l, ' \
    #                             'account_analytic_journal AS j ' \
    #                         'WHERE j.type = \'general\' ' \
    #                         'GROUP BY DATE_TRUNC(\'month\', l.date) ' \
    #                         ') AS l, ' \
    #                         'account_analytic_account AS a ' \
    #                     'GROUP BY l.month, a.id ' \
    #                     ') AS d2 ' \
    #                 'GROUP BY d2.account_id, d2.month ' \
    #                 ') AS d ' \
    #             'LEFT JOIN ' \
    #                 '(SELECT ' \
    #                     'l.account_id AS account_id, ' \
    #                     'DATE_TRUNC(\'month\', l.date) AS month, ' \
    #                     'SUM(l.unit_amount) AS unit_amount ' \
    #                 'FROM account_analytic_line AS l, ' \
    #                     'account_analytic_journal AS j ' \
    #                 'WHERE (j.type = \'general\') and (j.id=l.journal_id) ' \
    #                 'GROUP BY l.account_id, DATE_TRUNC(\'month\', l.date) ' \
    #                 ') AS l '
    #                 'ON (' \
    #                     'd.account_id = l.account_id ' \
    #                     'AND d.month = l.month' \
    #                 ') ' \
    #             'GROUP BY d.month, d.account_id ' \
    #             ')')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    num_of_contracts_count = fields.Integer(compute='_compute_num_of_contracts_count', string="Contracts", type='integer')
    
    
    @api.multi
    def _compute_num_of_contracts_count(self):
        obj = self.env['account.analytic.account']
        for partner in self:
            partner.num_of_contracts_count = obj.search_count([('partner_id', '=', partner.id)])

