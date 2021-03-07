# -*- coding: utf-8 -*-
# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

import ast
from odoo import models, fields, api, exceptions, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class BankBalanceComputation(models.TransientModel):
    _name = "bank.balance.computation"

    """ SHORT TERMS:
    abs = account.bank.statement
    absl = account.bank.statement.line
    aml = account.move.line
    """

    date_start = fields.Date(
        string='Date start',
        required=True,
        default=fields.Date.today()
        )
    date_end = fields.Date(
        string='Date end',
        default=fields.Date.today(),
        required=True)
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journals',
        domain="[('type', '=', 'bank')]",
        help="""Select all journal about which you want to know the balance.
                By default, all journals will be selected""",
        default=lambda self: self._get_default_journals(),
        )
    bank_balances = fields.Text(string='Bank balances')
    final_query = fields.Text(string='Final Query')

    forecast_options = fields.Boolean(string='CF options')
    daily_balances = fields.Boolean(string='Daily balance')
    include_account_moves = fields.Boolean(string='Incl. accout moves')

    include_draft_invoices = fields.Boolean(string='Incl. draft invoices')
    include_sale_orders = fields.Boolean(string='Incl. sale orders')

    include_bank_fc_line = fields.Boolean(string='Incl. forecasted lines')

    def _get_additional_subquery(self, journal_list, fc_journal_list, date_start, date_end):
        """
        Add here your additional queries inheriting this method and adding the query
        and adding "UNION" at the beginning". See the existing additional queries subquery.
        """

        additional_subquery = ""

        # adding bank forecasted bank statement lines
        if self.include_bank_fc_line and not fc_journal_list:
            raise UserError(_("Please select at least one treasury planning journal."))

        if self.include_bank_fc_line:
                additional_subquery += """
                UNION

                SELECT CAST('FBK' AS text) AS type, absl.id AS ID, absl.date, absl.name,
                    absl.amount_main_currency as amount, absl.cf_forecast, journal_id
                FROM account_bank_statement_line absl
                WHERE journal_id IN {}
                AND date BETWEEN '{}' AND '{}'
            """.format(str(fc_journal_list), date_start, date_end)

        # adding account move lines
        if self.include_account_moves:
            additional_subquery += """
                UNION

                SELECT CAST('FPL' AS text) AS type, aml.id AS ID, aml.treasury_date AS date, am.name AS name,
                       aml.amount_residual AS amount, NULL AS cf_forecast, NULL AS journal_id
                FROM account_move_line aml
                LEFT JOIN account_move am ON (aml.move_id = am.id)
                WHERE aml.treasury_planning AND aml.amount_residual != 0
                AND aml.treasury_date BETWEEN '{}' AND '{}'
            """.format(date_start, date_end)

        # adding draft invoices
        if self.include_draft_invoices:
            additional_subquery += """
                UNION

                SELECT CAST('DFT' AS text) AS type, ai.id AS ID, ai.date_treasury AS date, rp.name AS name,
                       CASE WHEN ai.type = 'out_invoice' THEN ai.amount_total ELSE (ai.amount_total * -1) END AS amount, 
                       NULL AS cf_forecast, NULL AS journal_id
                FROM account_invoice ai
                LEFT JOIN res_partner rp ON (ai.partner_id = rp.id)
                WHERE ai.state IN ('draft')
                AND ai.date_treasury BETWEEN '{}' AND '{}'
            """.format(date_start, date_end)

        return additional_subquery

    @api.multi
    def compute_bank_balances(self):
        """Computes balances of all journals"""

        self.ensure_one()
        if not self.journal_ids:
            raise UserError(_("Please select at least one bank journal!"))

        # distinguish between reports with all operation or daily totals
        if self.daily_balances:
            journal_header = (_("Date"), _("Total"))
            empty_columns = ("",)
            report_type = "SELECT DISTINCT ON (date) date,"
            css_dict = ""
        else:
            journal_header = (_("Date"), _("Type"), _("Name"), _("Amount"), _("Total"))
            report_type = "SELECT date, type, name, amount AS amount,"
            empty_columns = ("", "", "", "",)
            css_dict = ast.literal_eval(self.env['ir.values'].sudo().get_default(
                'treasury.management.config.settings',
                'fc_css_dict',
                for_all_users=True) or '{}')

        journals_balances = ""
        balances_list = ()

        # preparing lists of normal and forecasting
        # the list of journal IDs is multiplied by 2 to avoid error on single ID
        journal_list = tuple((k.id for k in self.journal_ids if not k.treasury_planning)) * 2
        fc_journal_list = tuple((k.id for k in self.journal_ids if k.treasury_planning)) * 2

        total_initial_saldo = 0
        # creating the operation and saldo column for each existing journal which is not for treasury planning
        for journal in self.journal_ids:
            if not journal.treasury_planning:
                initial_balance = self._compute_detailed_balance(
                    journal, self.date_start)
                total_initial_saldo += initial_balance
                balances_list += (initial_balance,)
                journals_balances += """
                \nSUM(CASE WHEN journal_id = {} THEN amount ELSE 0 END)
                    OVER (ORDER BY date) + {},
                """.format(journal.id, initial_balance)
                journal_header += (journal.name,)

        all_balances = empty_columns + (total_initial_saldo,) + balances_list
        journal_header += (_("Date"),)

        additional_subquery = self._get_additional_subquery(
            journal_list, fc_journal_list, self.date_start, self.date_end)

        # the main subquery, which always includes ABSL
        main_query = """
            WITH global_forecast AS (
                SELECT CAST('BNK' AS text) AS type, absl.id AS ID, absl.date, absl.name,
                    absl.amount_main_currency as amount, absl.cf_forecast, journal_id
                FROM account_bank_statement_line absl
                WHERE journal_id IN {_01}
                AND date BETWEEN '{_02}' AND '{_03}'
                {_04}
            )

            {_05}
            sum(amount) OVER (ORDER BY date) + {_06},
            {_07} date
            FROM global_forecast
            GROUP BY ID, type, name, date, amount, journal_id
        """.format(_01=str(journal_list),  # list of bank journals
                   _02=self.date_start,
                   _03=self.date_end,
                   _04=additional_subquery,  # adding acc. moves, orders, draft inv.
                   _05=report_type, # all operations or dayly totals
                   _06=total_initial_saldo,
                   _07=journals_balances)

        self.final_query = main_query
        self.env.cr.execute(main_query)
        report_lines = self.env.cr.fetchall()

        self.bank_balances = self._tuple_to_table(
            'bank', css_dict, journal_header, all_balances, report_lines)

        return {
            "type": "ir.actions.do_nothing",
            }

    def _get_background_color(self, kind, line, css_dict):
        if kind == 'bank':
            color = css_dict[line[1]] if css_dict else ''

        return color

    def _tuple_to_table(self, kind, css_dict, header, balances, report_lines):
        # creating the table header

        result = "<table class='table'> \n<tr>"
        for head in header:
            result += "<th>{}</th>".format(head.encode('utf8'))
        result += "\n</tr>\n<tr>"
        for balance in balances:
            result += "<td>{}</td>".format(formatLang(
                    self.env, balance, 2, monetary=True))
        result += "\n</tr>"

        # creating single lines
        for line in report_lines:
            color = self._get_background_color('bank', line, css_dict)
            table_line = "<tr style='background-color:{};'>".format(color)

            for value in line:
                if isinstance(value, unicode):
                    table_line += "<td> {} </td>".format(value.encode('utf-8'))
                elif isinstance(value, float):
                    table_line += "<td> {} </td>".format(
                        formatLang(self.env, value, 2, monetary=True))
                elif isinstance(value, basestring):
                    table_line += "<td> {} </td>".format(value)

            table_line += "</tr>"
            result += table_line

        result += "</table>"
        return result

    def _compute_detailed_balance(self, journal, date):
        """Computes detailed balance of each journal"""
        # take the most recent bank statement
        statememt_list = self.env['account.bank.statement'].search([
            ('initial_date', '<=', date),
            ('journal_id', '=', journal.id),
        ])
        balance = 0
        if statememt_list:
            statement = statememt_list.sorted(key=lambda r: r.initial_date)[-1]
            balance = statement.balance_start
            for line in statement.line_ids:
                if line.date < date:
                    balance += line.amount_main_currency
        return balance

    @api.multi
    @api.onchange('date_start')
    def onchange_date_start(self):
        if self.date_end == "" or self.date_end < self.date_start :
            self.date_end = self.date_start

    @api.multi
    @api.onchange('forecast_options')
    def onchange_forecast_options(self):
        self.include_account_moves = False
        self.include_draft_invoices = False
        self.include_bank_fc_line = False

    @api.model
    def _get_default_journals(self):
        journal_list = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('treasury_planning', '!=', True)
        ])
        return journal_list
