# -*- coding: utf-8 -*-
# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

from odoo import models, fields, api, _
from odoo.tools.misc import formatLang
from datetime import timedelta
from odoo.exceptions import UserError


class TreasuryForecast(models.Model):
    _name = "treasury.forecast"
    _order = "date_start desc"
    _description = "Treasury Forecast"

    # General data
    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    statement_id = fields.Many2one(
        string='Statement',
        comodel_name='account.bank.statement')
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ], default='open')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required='True',
                                 default=lambda self: self.env.user.company_id,)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    initial_balance = fields.Float(
        string='Initial balance',
        compute='compute_initial_balance',
        store=True)
    final_balance = fields.Float(
        string='Final balance',
        compute='compute_final_balance',
        store=True)
    previous_forecast_id = fields.Many2one(
        comodel_name='treasury.forecast',
        string='Previous forecast')
    forecast_template_id = fields.Many2one(
        comodel_name='treasury.forecast.template',
        string='Forecast Template')
    periodic_saldo = fields.Float(
        string='Periodic saldo',
        compute='compute_periodic_saldo',
        store=True)
    hide_analysis = fields.Boolean(string='Hide analysis')
    force_initial_balance = fields.Float(string='Force initial balance')

    # text field for reporting table
    forecast_analysis = fields.Text(
        string='Treasury Analysis',
        compute='compute_periodic_saldo',
        store=True)

    # Payables and receivables
    receivable_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='forecast_id',
        domain=[('debit', '>', 0),
                ('journal_id.type', '!=', 'bank'),],
        string='Receivables')
    payable_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='forecast_id',
        domain=[('credit', '>', 0),
                ('journal_id.type', '!=', 'bank')],
        string='Payables')
    recurrent_cost_ids = fields.One2many(
        comodel_name='account.bank.statement.line',
        inverse_name='treasury_forecast_id',
        string='Cost/revenues',
        domain=['|',
                ('statement_fp', '!=', True),
                '&', ('statement_fp', '!=', False),
                ('cf_forecast', '!=', False)
                ],
        store=True)

    @api.onchange('previous_forecast_id')
    def _onchange_date_saldo(self):
        for item in self:
            if item.previous_forecast_id:
                date_draft = fields.Date.from_string(
                    item.previous_forecast_id.date_end) + timedelta(days=1)
                item.date_start = fields.Date.to_string(date_draft)
                item.date_end = item.date_start
                item.initial_balance = item.previous_forecast_id.final_balance

    def _compute_date(self, begin, end, day):
        if day >= 0:
            date_draft = fields.Date.from_string(begin) + timedelta(days=day-1)
        elif day < 0:
            date_draft = fields.Date.from_string(end) + timedelta(days=day+1)
        date = fields.Date.to_string(date_draft)
        return date

    @api.multi
    def compute_forecast_lines(self):
        for item in self:
            if not item.forecast_template_id:
                raise UserError(_("Please select a forecast template."))
            for cost in item.forecast_template_id.recurring_line_ids:
                date = self._compute_date(item.date_start, item.date_end, cost.day)
                statement_id = item.forecast_template_id.bank_statement_id.id
                values = {
                    'name': cost.name,
                    'ref': cost.ref,
                    'partner_id': cost.partner_id.id,
                    'treasury_date': date,
                    'date': date,
                    'amount': cost.amount,
                    'cf_forecast': True,
                    'treasury_forecast_id': item.id,
                    'statement_id': statement_id,
                }
                statement_line_obj = self.env['account.bank.statement.line']
                new_line = statement_line_obj.create(values)
            item.forecast_template_id = ""

    @api.depends('payable_ids', 'payable_ids.amount_residual', 'receivable_ids',
                 'receivable_ids.amount_residual', 'recurrent_cost_ids',
                 'recurrent_cost_ids.cf_forecast',)
    def compute_periodic_saldo(self):
        for item in self:
            # setting reporting variables
            periodic_debit = 0.0
            open_debit = 0.0
            periodic_credit = 0.0
            open_credit = 0.0
            others = 0.0
            open_others = 0.0

            # computing reporting variables
            for line in item.payable_ids:
                periodic_debit += line.balance
                open_debit += line.amount_residual
            for line in item.receivable_ids:
                periodic_credit += line.balance
                open_credit += line.amount_residual
            for line in item.recurrent_cost_ids:
                others += line.amount
                fp = line.statement_id.treasury_planning
                open_others += line.amount if fp else 0

            periodic_saldo = periodic_debit + periodic_credit + others
            item.periodic_saldo = periodic_saldo

            # creating the forecast analysis table
            header = (_(""), _("Receivables"), _("Payables"), _("Other"))
            report_lines = (
                (_("Total"), periodic_credit, periodic_debit, others),
                (_("Open"), open_credit, open_debit, open_others)
                )

            item.forecast_analysis = self._tuple_to_table(
                'forecast', '', header, None, report_lines)

    def _tuple_to_table(self, kind, css, header, balances, report_lines):
        """ REWRITE!!

           Prepare the dict of values to create the new refund from the invoice.
           This method may be overridden to implement custom
           refund generation (making sure to call super() to establish
           a clean extension chain).

           :param record invoice: invoice to refund
           :param string date_invoice: refund creation date from the wizard
           :param integer date: force date from the wizard
           :param string description: description of the refund from the wizard
           :param integer journal_id: account.journal from the wizard
           :return: dict of value to create() the refund
        """
        # creating the table header
        result = "<table class='table' style='{}'> \n<tr>".format(css)
        for head in header:
            result += "<th> {} </th>".format(head.encode('utf8'))
        result += "\n</tr>\n<tr>"
        if balances:
            for balance in balances:
                result += "<td> {} </td>".format(formatLang(
                    self.env, balance, 2, monetary=True))
            result += "\n</tr>"

        # creating single lines
        for line in report_lines:
            table_line = "<tr>"
            for value in line:
                if isinstance(value, unicode):
                    table_line += "<td> {} </td>".format(value)
                elif isinstance(value, float):
                    table_line += "<td> {} </td>".format(
                        formatLang(self.env, value, 2, monetary=True))
            table_line += "</tr>"
            result += table_line

        result += "</table>"
        return result

    @api.multi
    def compute_forecast_data(self):
        for item in self:
            # compute treasury date of all account moves
            query = """
            SELECT id, treasury_planning, treasury_date, date_maturity
            FROM account_move_line
            WHERE (treasury_planning IS TRUE
                AND treasury_date IS NOT NULL
                AND treasury_date BETWEEN '{_01}' AND '{_02}')
                OR
                (treasury_planning IS TRUE 
                AND treasury_date IS NULL
                AND date_maturity BETWEEN '{_01}' AND '{_02}')
            """.format(
                _01=item.date_start,
                _02=item.date_end)
            self.env.cr.execute(query)
            move_list = [r[0] for r in self._cr.fetchall()]

            for num in move_list:
                move = self.env['account.move.line'].browse(num)
                if not move.treasury_date:
                    move.treasury_date = move.date_maturity
                move._compute_treasury_forecast()

            bank_line_obj = self.env['account.bank.statement.line']
            bank_line_list = bank_line_obj.search([
                ('date', '>=', item.date_start),
                ('date', '<=', item.date_end),
                ])
            for line in bank_line_list:
                line.compute_treasury_forecast()

    @api.depends('previous_forecast_id.final_balance', 'force_initial_balance')
    def compute_initial_balance(self):
        for item in self:
            if item.previous_forecast_id.final_balance:
                item.initial_balance = item.previous_forecast_id.final_balance

            if item.force_initial_balance != 0.0:
                 item.initial_balance = item.force_initial_balance

    @api.depends('initial_balance', 'periodic_saldo')
    def compute_final_balance(self):
        for item in self:
            item.final_balance = item.initial_balance + item.periodic_saldo

    @api.multi
    def refresh_page(self):
        pass