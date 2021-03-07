# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api, _
from odoo.tools.misc import formatLang
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)

class report_account_general_ledger(models.AbstractModel):
    _inherit = "account.general.ledger"

    def _format(self, value, currency=False):
        if self.env.context.get('no_format'):
            return value
        currency_id = currency or self.env.user.company_id.currency_id
        if self.env.context.get('change_currency'):
            currency_id = self.env.context.get('change_currency')
        if currency_id.is_zero(value):
            value = abs(value)
        res = formatLang(self.env, value, currency_obj=currency_id)
        if '-' in res:
            res = res.replace('-', '')
            if ' ' in res:
                data = res.split(' ')
                if any(i.isdigit() for i in data[0]):
                    res = '(' + data[0] + ') ' + data[1]
                else:
                    res = data[0] + ' (' + data[1] + ')'
            else:
                res = '(' + res + ')'
        return res

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.general.ledger'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_from': context_id.date_from,
            'date_to': context_id.date_to,
            'state': context_id.all_entries and 'all' or 'posted',
            'cash_basis': context_id.cash_basis,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'journal_ids': context_id.journal_ids.ids,
            'analytic_account_ids': context_id.analytic_account_ids,
            'analytic_tag_ids': context_id.analytic_tag_ids,
            'change_currency' : context_id.change_currency_id,
        })
        return self.with_context(new_context)._lines(line_id)

    def _get_with_statement(self, user_types, domain=None):
        sql = ''
        params = []

        if self.env.context.get('cash_basis'):
            if not user_types:
                return sql, params
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
            sql = """WITH account_move_line AS (
              SELECT \"account_move_line\".id, \"account_move_line\".date, \"account_move_line\".name, \"account_move_line\".debit_cash_basis, \"account_move_line\".credit_cash_basis, \"account_move_line\".move_id, \"account_move_line\".account_id, \"account_move_line\".journal_id, \"account_move_line\".balance_cash_basis, \"account_move_line\".amount_residual, \"account_move_line\".partner_id, \"account_move_line\".reconciled, \"account_move_line\".company_id, \"account_move_line\".company_currency_id, \"account_move_line\".amount_currency, \"account_move_line\".balance, \"account_move_line\".user_type_id, \"account_move_line\".analytic_account_id
               FROM """ + tables + """
               WHERE (\"account_move_line\".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                 OR \"account_move_line\".move_id NOT IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s))
                 AND """ + where_clause + """
              UNION ALL
              (
               WITH payment_table AS (
                 SELECT aml.move_id, \"account_move_line\".date, CASE WHEN aml.balance = 0 THEN 0 ELSE part.amount / ABS(aml.balance) END as matched_percentage
                   FROM account_partial_reconcile part LEFT JOIN account_move_line aml ON aml.id = part.debit_move_id, """ + tables + """
                   WHERE part.credit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
                 UNION ALL
                 SELECT aml.move_id, \"account_move_line\".date, CASE WHEN aml.balance = 0 THEN 0 ELSE part.amount / ABS(aml.balance) END as matched_percentage
                   FROM account_partial_reconcile part LEFT JOIN account_move_line aml ON aml.id = part.credit_move_id, """ + tables + """
                   WHERE part.debit_move_id = "account_move_line".id
                    AND "account_move_line".user_type_id IN %s
                    AND """ + where_clause + """
               )
               SELECT aml.id, ref.date, aml.name,
                 CASE WHEN aml.debit > 0 THEN ref.matched_percentage * aml.debit ELSE 0 END AS debit_cash_basis,
                 CASE WHEN aml.credit > 0 THEN ref.matched_percentage * aml.credit ELSE 0 END AS credit_cash_basis,
                 aml.move_id, aml.account_id, aml.journal_id,
                 ref.matched_percentage * aml.balance AS balance_cash_basis,
                 aml.amount_residual, aml.partner_id, aml.reconciled, aml.company_id, aml.company_currency_id, aml.amount_currency, aml.balance, aml.user_type_id, aml.analytic_account_id
                FROM account_move_line aml
                RIGHT JOIN payment_table ref ON aml.move_id = ref.move_id
                WHERE journal_id NOT IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                  AND aml.move_id IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s)
              )
            ) """
            params = [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)]
        return sql, params

    def do_query_unaffected_earnings(self, line_id):

        select = '''
        SELECT COALESCE(SUM("account_move_line".balance), 0),
               COALESCE(SUM("account_move_line".amount_currency), 0),
               COALESCE(SUM("account_move_line".debit), 0),
               COALESCE(SUM("account_move_line".credit), 0)'''
        if self.env.context.get('cash_basis'):
            select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        select += " FROM %s WHERE %s"
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types, domain=[('user_type_id.include_initial_balance', '=', False)])
        tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=[('user_type_id.include_initial_balance', '=', False)])
        query = select % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        res = self.env.cr.fetchone()
        return {'balance': res[0], 'amount_currency': res[1], 'debit': res[2], 'credit': res[3]}

    def _do_query(self, line_id, group_by_account=True, limit=False):
        AmlObj = self.env['account.move.line']
        if group_by_account:
            select = "SELECT \"account_move_line\".account_id"
            select += ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".amount_currency),SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
            if self.env.context.get('cash_basis'):
                select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        else:
            select = "SELECT \"account_move_line\".id"
        sql = "%s FROM %s WHERE %s%s"
        if group_by_account:
            sql +=  "GROUP BY \"account_move_line\".account_id"
        else:
            sql += " GROUP BY \"account_move_line\".id"
            sql += " ORDER BY MAX(\"account_move_line\".date),\"account_move_line\".id"
            if limit and isinstance(limit, int):
                sql += " LIMIT " + str(limit)
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        line_clause = line_id and ' AND \"account_move_line\".account_id = ' + str(line_id) or ''
        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        if self.env.context.get('change_currency') and group_by_account:
            results = []
            domain = []
            context = self.env.context

            date_field = 'date'
            if context.get('aged_balance'):
                date_field = 'date_maturity'
            if context.get('date_to'):
                domain += [(date_field, '<=', context['date_to'])]
            if context.get('date_from'):
                if not context.get('strict_range'):
                    domain += ['|', (date_field, '>=', context['date_from']),
                               ('account_id.user_type_id.include_initial_balance', '=', True)]
                elif context.get('initial_bal'):
                    domain += [(date_field, '<', context['date_from'])]
                else:
                    domain += [(date_field, '>=', context['date_from'])]

            if context.get('journal_ids'):
                domain += [('journal_id', 'in', context['journal_ids'])]

            state = context.get('state')
            if state and state.lower() != 'all':
                domain += [('move_id.state', '=', state)]

            if context.get('company_id'):
                domain += [('company_id', '=', context['company_id'])]

            if 'company_ids' in context:
                domain += [('company_id', 'in', context['company_ids'])]

            if context.get('account_tag_ids'):
                domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

            if context.get('analytic_tag_ids'):
                domain += ['|', ('analytic_account_id.tag_ids', 'in', context['analytic_tag_ids'].ids),
                           ('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]

            if context.get('analytic_account_ids'):
                domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]

            AmlSearch = AmlObj.search(domain)
            account_ids = set([aml.account_id.id for aml in AmlSearch])
            if line_id:
                account_ids = [line_id]

            for Account in account_ids:
                AmlSearch = AmlObj.search(domain + [('account_id', '=', Account)])
                Balance = []
                AmountCurrency = []
                Debit = []
                Credit = []
                for Aml in AmlSearch:
                    currency_id = self.env.context.get('change_currency').with_context(date=Aml.date)
                    UsedCurrency = self.env.user.company_id.currency_id.with_context(date=Aml.date)
                    Balance.append(Aml.balance and UsedCurrency.compute(Aml.balance, currency_id) or 0.0)
                    AmountCurrency.append(Aml.amount_currency and UsedCurrency.compute(Aml.amount_currency, currency_id) or 0.0)
                    Debit.append(Aml.debit and UsedCurrency.compute(Aml.debit, currency_id) or 0.0)
                    Credit.append(Aml.credit and UsedCurrency.compute(Aml.credit, currency_id) or 0.0)
                if AmountCurrency or Balance or Debit or Credit:
                    results.append((Account, sum(Balance), sum(AmountCurrency), sum(Debit), sum(Credit)))
        return results

    def do_query(self, line_id):
        results = self._do_query(line_id, group_by_account=True, limit=False)
        used_currency = self.env.user.company_id.currency_id
        compute_table = {
            a.id: a.company_id.currency_id.compute
            for a in self.env['account.account'].browse([k[0] for k in results])
        }
        if not line_id:
            account_ids = [i[0] for i in results]
            other_account_ids = self.env['account.account'].search([('id','not in',account_ids),('user_type_id.type','!=','view'),('company_id','in',self.env.context['context_id'].company_ids.ids)]).ids
            for id in other_account_ids:
                results.append((id, 0.0, 0.0, 0.0, 0.0))
        if self.get_name() == 'general_ledger' and self.env.context.get('context_id').account_ids:
            new_results = []
            account_ids = self.env.context.get('context_id').account_ids.ids
            for item in results:
                if item[0] in account_ids:
                    new_results.append(item)
            results = new_results
        results = dict([(
            k[0], {
                'balance': compute_table[k[0]](k[1], used_currency) if k[0] in compute_table else k[1],
                'amount_currency': k[2],
                'debit': compute_table[k[0]](k[3], used_currency) if k[0] in compute_table else k[3],
                'credit': compute_table[k[0]](k[4], used_currency) if k[0] in compute_table else k[4],
            }
        ) for k in results])
        return results

    def group_by_account_id(self, line_id):
        accounts = {}
        results = self.do_query(line_id)
        initial_bal_date_to = datetime.strptime(self.env.context['date_from_aml'], "%Y-%m-%d") + timedelta(days=-1)
        initial_bal_results = self.with_context(date_to=initial_bal_date_to.strftime('%Y-%m-%d')).do_query(line_id)
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids'])]
        if context.get('journal_ids'):
            base_domain.append(('journal_id', 'in', context['journal_ids']))
        if context['date_from_aml']:
            base_domain.append(('date', '>=', context['date_from_aml']))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        if context.get('account_tag_ids'):
            base_domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]
        if context.get('analytic_tag_ids'):
            base_domain += ['|', ('analytic_account_id.tag_ids', 'in', context['analytic_tag_ids'].ids), ('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]
        if context.get('analytic_account_ids'):
            base_domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]
        for account_id, result in results.items():
            domain = list(base_domain)  # copying the base domain
            domain.append(('account_id', '=', account_id))
            account = self.env['account.account'].browse(account_id)
            accounts[account] = result
            accounts[account]['initial_bal'] = initial_bal_results.get(account.id, {'balance': 0, 'amount_currency': 0, 'debit': 0, 'credit': 0})
            aml_ctx = {}
            if context.get('date_from_aml'):
                aml_ctx = {
                    'strict_range': True,
                    'date_from': context['date_from_aml'],
                }
            aml_ids = self.with_context(**aml_ctx)._do_query(account_id, group_by_account=False)
            aml_ids = [x[0] for x in aml_ids]
            accounts[account]['lines'] = self.env['account.move.line'].browse(aml_ids)
        return accounts

    def _get_taxes(self):
        AmlObj = self.env['account.move.line']
        if self.env.context.get('change_currency'):
            domain = []
            res = {}
            if self.env.context.get('date_from') and self.env.context.get('date_to'):
                domain.append(('date', '>=', self.env.context.get('date_from')))
                domain.append(('date', '<=', self.env.context.get('date_to')))
            if not self.env.context.get('date_from') and self.env.context.get('date_to'):
                domain.append(('date', '<=', self.env.context.get('date_to')))
            if self.env.context.get('state') == 'posted':
                domain.append(('move_id.state', '=', 'posted'))
            if self.env.context.get('journal_ids'):
                domain.append(('journal_id', 'in', self.env.context.get('journal_ids')))
            AmlSearch = AmlObj.search(domain + [('tax_ids', '!=', False)])
            base_amount = {}
            tax_amount = {}
            tax_ids = set([aml.tax_ids for aml in AmlSearch])
            for tax in tax_ids:
                AmountSearch = AmlObj.search(domain + [('tax_ids', 'in', tax.id)])
                Balance = 0.0
                for Aml in AmountSearch:
                    currency_id = self.env.context.get('change_currency').with_context(date=Aml.date)
                    UsedCurrency = self.env.user.company_id.currency_id.with_context(date=Aml.date)
                    Balance += UsedCurrency.compute(Aml.balance, currency_id)
                base_amount[tax] = Balance
                AmountSearch = AmlObj.search(domain + [('tax_line_id', '=', tax.id)])
                Balance = 0.0
                for Aml in AmountSearch:
                    UsedCurrency =  self.env.user.company_id.currency_id.with_context(date=Aml.date)
                    currency_id = self.env.context.get('change_currency').with_context(date=Aml.date)
                    Balance += UsedCurrency.compute((Aml.debit - Aml.credit), currency_id)
                tax_amount[tax] = Balance
                res[tax] = {
                    'base_amount': base_amount[tax],
                    'tax_amount': tax_amount[tax],
                }
                if self.env.context['context_id'].journal_ids[0].type == 'sale':
                    res[tax]['base_amount'] = res[tax]['base_amount'] * -1
                    res[tax]['tax_amount'] = res[tax]['tax_amount'] * -1
        else:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            query = """
                SELECT rel.account_tax_id, SUM("account_move_line".balance) AS base_amount
                FROM account_move_line_account_tax_rel rel, """ + tables + """ 
                WHERE "account_move_line".id = rel.account_move_line_id
                    AND """ + where_clause + """
               GROUP BY rel.account_tax_id"""
            self.env.cr.execute(query, where_params)
            ids = []
            base_amounts = {}
	    for row in self.env.cr.fetchall():
                ids.append(row[0])
                base_amounts[row[0]] = row[1]

        res = {}
        for tax in self.env['account.tax'].browse(ids):
            self.env.cr.execute('SELECT sum(debit - credit) FROM ' + tables + ' '
                ' WHERE ' + where_clause + ' AND tax_line_id = %s', where_params + [tax.id])
            res[tax] = {
                'base_amount': base_amounts[tax.id],
                'tax_amount': self.env.cr.fetchone()[0] or 0.0,
            }
            if self.env.context['context_id'].journal_ids[0].type == 'sale':
                #sales operation are credits
                res[tax]['base_amount'] = res[tax]['base_amount'] * -1
                res[tax]['tax_amount'] = res[tax]['tax_amount'] * -1
        return res

    def _get_journal_total(self):
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        self.env.cr.execute('SELECT COALESCE(SUM(debit), 0) as debit, COALESCE(SUM(credit), 0) as credit, COALESCE(SUM(debit-credit), 0) as balance FROM ' + tables + ' '
                        'WHERE ' + where_clause + ' ', where_params)
        return self.env.cr.dictfetchone()

    @api.model
    def _lines(self, line_id=None):
        lang_code = self.env.lang or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        lines = []
        total_debit = 0.0
        total_credit = 0.0
        total_balance = 0.0
        total_initial_bal = 0.0
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        grouped_accounts = self.with_context(date_from_aml=context['date_from'], date_from=context['date_from'] and company_id.compute_fiscalyear_dates(datetime.strptime(context['date_from'], "%Y-%m-%d"))['date_from'] or None).group_by_account_id(line_id)  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        for account in sorted_accounts:
            initial_bal = grouped_accounts[account]['initial_bal']['balance']
            debit = grouped_accounts[account]['debit'] - grouped_accounts[account]['initial_bal']['debit']
            credit = grouped_accounts[account]['credit'] - grouped_accounts[account]['initial_bal']['credit']
            balance = grouped_accounts[account]['balance']
            total_initial_bal += initial_bal
            total_debit += debit
            total_credit += credit
            total_balance += balance
            amount_currency = '' if not account.currency_id else self._format(grouped_accounts[account]['amount_currency'], currency=account.currency_id)
            amount_currency_rate = account.currency_id.rate if account.currency_id.rate else ''
            lines.append({
                'id': account.id,
                'type': 'line',
                'name': account.code + " " + account.name,
                'footnotes': self.env.context['context_id']._get_footnotes('line', account.id),
                'columns': ['', self._format(initial_bal), self._format(debit), self._format(credit), self._format(balance)],
                'level': 2,
                'unfoldable': True,
                'unfolded': account in context['context_id']['unfolded_accounts'],
                'colspan': 4,
            })
            if account in context['context_id']['unfolded_accounts']:
                domain_lines = [{
                    'id': account.id,
                    'type': 'initial_balance',
                    'name': _('Initial Balance'),
                    'footnotes': self.env.context['context_id']._get_footnotes('initial_balance', account.id),
                    'columns': ['', '', '', '', self._format(initial_bal), '', '', self._format(initial_bal)],
                    'level': 1,
                }]
                amls = grouped_accounts[account]['lines']
                used_currency = self.env.user.company_id.currency_id
                line_balance = initial_bal
                for line in amls:
                    if self.env.context['cash_basis']:
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    if self.env.context.get('change_currency'):
                        currency_id = self.env.context.get('change_currency').with_context(date=line.date)
                        UsedCurrency = self.env.user.company_id.currency_id.with_context(date=line.date)
                        line_debit = UsedCurrency.compute(line_debit, currency_id)
                        line_credit = UsedCurrency.compute(line_credit, currency_id)
                        if self.env.context['cash_basis']:
                            line_debit = UsedCurrency.compute(line_debit, currency_id)
                            line_credit = UsedCurrency.compute(line_credit, currency_id)
                    else:
                        line_debit = line.company_id.currency_id.compute(line_debit, used_currency)
                        line_credit = line.company_id.currency_id.compute(line_credit, used_currency)
                    line_balance += line_debit - line_credit
                    currency = "" if not line.currency_id else self.with_context(no_format=False)._format(line.amount_currency, currency=line.currency_id)
                    currency_rate =  line.currency_id.rate   if line.currency_id.rate else ''
                    name = []
                    name = line.name and line.name or ''
                    if line.ref:
                        name = name and name + ' - ' + line.ref or line.ref
                    if len(name) > 35 and not self.env.context.get('no_format'):
                        name = name[:32] + "..."
                    partner_name = line.partner_id.name
                    if partner_name and len(partner_name) > 35 and not self.env.context.get('no_format'):
                        partner_name = partner_name[:32] + "..."
                    domain_lines.append({
                        'id': line.id,
                        'type': 'move_line_id',
                        'move_id': line.move_id.id,
                        'action': line.get_model_id_and_name(),
                        'name': line.move_id.name if line.move_id.name else '/',
                        'footnotes': self.env.context['context_id']._get_footnotes('move_line_id', line.id),
                        'columns': [
                            datetime.strptime(line.date, DEFAULT_SERVER_DATE_FORMAT).strftime(date_format),
                            line.ref, line.name, partner_name, '',
                            line_debit != 0 and self._format(line_debit) or '',
                            line_credit != 0 and self._format(line_credit) or '',
                            self._format(line_balance)
                        ],
                        'level': 1,
                    })
                domain_lines.append({
                    'id': account.id,
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'footnotes': self.env.context['context_id']._get_footnotes('o_account_reports_domain_total', account.id),
                    'columns': ['', '', '', '', self._format(initial_bal), self._format(debit), self._format(credit), self._format(balance)],
                    'level': 1,
                })
                lines += domain_lines

        if len(context['context_id'].journal_ids) == 1 and context['context_id'].journal_ids.type in ['sale', 'purchase'] and not line_id:
            total = self._get_journal_total()
            lines.append({
                'id': 0,
                'type': 'total',
                'name': _('Total'),
                'footnotes': {},
                'columns': ['', '', '', '', '',self._format(total['debit']), self._format(total['credit']), self._format(total['balance'])],
                'level': 1,
                'unfoldable': False,
                'unfolded': False,
            })
            lines.append({
                'id': 0,
                'type': 'line',
                'name': _('Tax Declaration'),
                'footnotes': {},
                'columns': ['', '', '', '', '', '', '', ''],
                'level': 1,
                'unfoldable': False,
                'unfolded': False,
            })
            lines.append({
                'id': 0,
                'type': 'line',
                'name': _('Name'),
                'footnotes': {},
                'columns': ['', '', '', '', '', _('Base Amount'), _('Tax Amount'), ''],
                'level': 2,
                'unfoldable': False,
                'unfolded': False,
            })
            for tax, values in self._get_taxes().items():
                lines.append({
                    'id': tax.id,
                    'name': tax.name + ' (' + str(tax.amount) + ')',
                    'type': 'tax_id',
                    'footnotes': self.env.context['context_id']._get_footnotes('tax_id', tax.id),
                    'unfoldable': False,
                    'columns': ['', '', '', '', '', values['base_amount'], values['tax_amount'], ''],
                    'level': 1,
                })
        # Total line at bottom
        if not line_id:
            lines.append({
                'id': 0,
                'type': 'o_account_reports_domain_total',
                'name': _('Total '),
                'footnotes': {},
                'columns': ['', '', '', '', self._format(total_initial_bal), self._format(total_debit), self._format(total_credit), self._format(total_balance)],
                'level': 1,
            })
        return lines

    @api.model
    def get_title(self):
        return _("General Ledger")

    @api.model
    def get_name(self):
        return 'general_ledger'

    @api.model
    def get_report_type(self):
        return self.env.ref('enterprise_accounting_report.account_report_type_general_ledger')

    def get_template(self):
        return 'enterprise_accounting_report.report_financial'

class account_context_general_ledger(models.TransientModel):
    _inherit = "account.context.general.ledger"

    def get_columns_names(self):
        return [_("Date"), _("Reference"), _("Label"), _("Partner"), _("Initial Balance"), _("Debit"), _("Credit"), _("Balance")]

    @api.multi
    def get_columns_types(self):
        return ["date", "text", "text", "text", "number", "number","number", "number"]
