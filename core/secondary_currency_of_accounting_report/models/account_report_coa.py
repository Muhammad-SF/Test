# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools.misc import formatLang

class report_account_coa(models.AbstractModel):
    _inherit = "account.coa.report"
    _description = "Chart of Account Report"

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.coa'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_from': context_id.date_from,
            'date_to': context_id.date_to,
            'state': context_id.all_entries and 'all' or 'posted',
            'cash_basis': context_id.cash_basis,
            'hierarchy_3': context_id.hierarchy_3,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'periods_number': context_id.periods_number,
            'periods': [[context_id.date_from, context_id.date_to]] + context_id.get_cmp_periods(),
            'change_currency':context_id.change_currency_id,
        })
        return self.with_context(new_context)._lines(line_id)

    @api.model
    def _lines(self, line_id=None):
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        grouped_accounts = {}
        period_number = 0
        initial_balances = {}
        context['periods'].reverse()
        for period in context['periods']:
            res = self.with_context(date_from_aml=period[0], date_to=period[1], date_from=period[0] and company_id.compute_fiscalyear_dates(datetime.strptime(period[0], "%Y-%m-%d"))['date_from'] or None).group_by_account_id(line_id)  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
            if period_number == 0:
                initial_balances = dict([(k, res[k]['initial_bal']['balance']) for k in res])
            for account in res:
                if account not in grouped_accounts.keys():
                    grouped_accounts[account] = [{'balance': 0, 'debit': 0, 'credit': 0, 'initial_bal': {'credit': 0.0, 'debit': 0.0}} for p in context['periods']]
                grouped_accounts[account][period_number]['debit'] = res[account]['debit'] - res[account]['initial_bal']['debit']
                grouped_accounts[account][period_number]['credit'] = res[account]['credit'] - res[account]['initial_bal']['credit']
            period_number += 1
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        initial_bal_total = 0.0
        debit_credit_total = {}
        for p in xrange(len(context['periods'])):
            debit_credit_total.update({p: [0.0, 0.0, 0.0]})
        for account in sorted_accounts:
            debit_credit = []
            initial_bal = [account in initial_balances and self._format(initial_balances[account]) or self._format(0.0)]
            initial_bal_total += (account in initial_balances and initial_balances[account] or 0.0)
            for count in xrange(len(context['periods'])):
                debit = grouped_accounts[account][count].get('debit')
                credit = grouped_accounts[account][count].get('credit')
                balance = initial_balances.get(account, 0.0) + debit - credit
                debit_credit.extend([self._format(debit), self._format(credit), self._format(balance)])
                debit_credit_total.update({count: [debit_credit_total.get(count)[0] + debit, debit_credit_total.get(count)[1] + credit, debit_credit_total.get(count)[2] + balance]})
            lines.append({
                'id': account.id,
                'type': 'account_id',
                'name': account.code + " " + account.name,
                'footnotes': self.env.context['context_id']._get_footnotes('account_id', account.id),
                'columns': initial_bal + debit_credit,
                'level': 1,
                'unfoldable': False,
            })

        # Total line at bottom
        initial_bal = [self._format(abs(initial_bal_total))]
        debit_credit = []
        for l in debit_credit_total.values():
            for i in l:
                debit_credit.append(self._format(i))
        lines.append({
            'id': 0,
            'type': 'o_account_reports_domain_total',
            'name': _('Total '),
            'footnotes': {},
            'columns': initial_bal + debit_credit,
            'level': 1,
        })
        return lines

    @api.model
    def get_title(self):
        return _("Trial Balance")

    @api.model
    def get_name(self):
        return 'coa'

    @api.model
    def get_report_type(self):
        return self.env.ref('enterprise_accounting_report.account_report_type_date_range')


class account_context_coa(models.TransientModel):
    _inherit = "account.context.coa"
    _description = "A particular context for the chart of account"

    fold_field = 'unfolded_accounts'
    fold_model = 'account.account'
    unfolded_accounts = fields.Many2many('account.account', 'context_to_account_coa', string='Unfolded lines')

    @api.model
    def _context_add(self):
        return {'has_hierarchy': True}

    def get_report_obj(self):
        return self.env['account.coa.report']

    def get_special_date_line_names(self):
        temp = self.get_full_date_names(self.date_to, self.date_from)
        if not isinstance(temp, unicode):
            temp = temp.decode("utf-8")
        columns = []
        if self.comparison and (self.periods_number == 1 or self.date_filter_cmp == 'custom'):
            columns += [self.get_cmp_date()]
        elif self.comparison:
            periods = self.get_cmp_periods(display=True)
            periods.reverse()
            for period in periods:
                columns += [str(period)]
        return columns + [temp]


    def get_columns_names(self):
        columns = [_('Initial Balance')]
        if self.comparison and (self.periods_number == 1 or self.date_filter_cmp == 'custom'):
            columns += [_('Debit'), _('Credit'), _('Ending Balance')]
        elif self.comparison:
            for period in self.get_cmp_periods(display=True):
                columns += [_('Debit'), _('Credit'), _('Ending Balance')]
        return columns + [_('Debit'), _('Credit'), _('Ending Balance')]

    @api.multi
    def get_columns_types(self):
        types = ['number']
        if self.comparison and (self.periods_number == 1 or self.date_filter_cmp == 'custom'):
            types += ['number', 'number', 'number']
        else:
            for period in self.get_cmp_periods(display=True):
                types += ['number', 'number', 'number']
        return types + ['number', 'number', 'number']
