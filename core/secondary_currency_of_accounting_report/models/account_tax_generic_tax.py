# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import formatLang

class report_account_generic_tax_report(models.AbstractModel):
    _inherit = "account.generic.tax.report"

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.user.company_id.currency_id
        if self.env.context.get('change_currency'):
            currency_id = self.env.context.get('change_currency')
        if currency_id.is_zero(value):
            # don't print -0.0 in reports
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

    def _get_with_statement(self, user_types, domain=None):
        """ This function allow to define a WITH statement as prologue to the usual queries returned by query_get().
            It is useful if you need to shadow a table entirely and let the query_get work normally although you're
            fetching rows from your temporary table (built in the WITH statement) instead of the regular tables.

            @returns: the WITH statement to prepend to the sql query and the parameters used in that WITH statement
            @rtype: tuple(char, list)
        """
        sql = ''
        params = []

        #Cash basis option
        #-----------------
        #In cash basis, we need to show amount on income/expense accounts, but only when they're paid AND under the payment date in the reporting, so
        #we have to make a complex query to join aml from the invoice (for the account), aml from the payments (for the date) and partial reconciliation
        #(for the reconciled amount).
        if self.env.context.get('cash_basis'):
            if not user_types:
                return sql, params
            #we use query_get() to filter out unrelevant journal items to have a shadowed table as small as possible
            tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
            sql = """WITH account_move_line AS (
              SELECT \"account_move_line\".id, \"account_move_line\".date, \"account_move_line\".name, \"account_move_line\".debit_cash_basis, \"account_move_line\".credit_cash_basis, \"account_move_line\".move_id, \"account_move_line\".account_id, \"account_move_line\".journal_id, \"account_move_line\".balance_cash_basis, \"account_move_line\".amount_residual, \"account_move_line\".partner_id, \"account_move_line\".reconciled, \"account_move_line\".company_id, \"account_move_line\".company_currency_id, \"account_move_line\".amount_currency, \"account_move_line\".balance, \"account_move_line\".user_type_id, \"account_move_line\".tax_line_id, \"account_move_line\".tax_exigible
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
                 aml.amount_residual, aml.partner_id, aml.reconciled, aml.company_id, aml.company_currency_id, aml.amount_currency, aml.balance, aml.user_type_id, aml.tax_line_id, aml.tax_exigible
                FROM account_move_line aml
                RIGHT JOIN payment_table ref ON aml.move_id = ref.move_id
                WHERE journal_id NOT IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                  AND aml.move_id IN (SELECT DISTINCT move_id FROM account_move_line WHERE user_type_id IN %s)
              )
            ) """
            params = [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)] + where_params + [tuple(user_types.ids)]
        return sql, params

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.report.context.tax'].search([['id', '=', context_id]])
        return self.with_context(
            date_from=context_id.date_from,
            date_to=context_id.date_to,
            state=context_id.all_entries and 'all' or 'posted',
            comparison=context_id.comparison,
            date_from_cmp=context_id.date_from_cmp,
            date_to_cmp=context_id.date_to_cmp,
            cash_basis=context_id.cash_basis,
            periods_number=context_id.periods_number,
            periods=context_id.get_cmp_periods(),
            context_id=context_id,
            company_ids=context_id.company_ids.ids,
            strict_range=True,
            change_currency = context_id.change_currency_id
        )._lines(line_id)


    def _sql_from_amls_one(self):
        sql = """SELECT "account_move_line".tax_line_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                    FROM %s
                    WHERE %s AND "account_move_line".tax_exigible GROUP BY "account_move_line".tax_line_id"""
        return sql

    def _sql_from_amls_two(self):
        sql = """SELECT r.account_tax_id, COALESCE(SUM("account_move_line".debit-"account_move_line".credit), 0)
                 FROM %s
                 INNER JOIN account_move_line_account_tax_rel r ON ("account_move_line".id = r.account_move_line_id)
                 INNER JOIN account_tax t ON (r.account_tax_id = t.id)
                 WHERE %s AND "account_move_line".tax_exigible GROUP BY r.account_tax_id"""
        return sql

    def _compute_from_amls(self, taxes, period_number):
        used_currency = self.env.user.company_id.currency_id
        sql = self._sql_from_amls_one()
        if self.env.context.get('cash_basis'):
            sql = sql.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        query = sql % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                from_currency = taxes[result[0]]['obj'].company_id.currency_id
                taxes[result[0]]['periods'][period_number]['tax'] = from_currency.compute(result[1], used_currency)
                taxes[result[0]]['show'] = True
        sql = self._sql_from_amls_two()
        if self.env.context.get('cash_basis'):
            sql = sql.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        query = sql % (tables, where_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                from_currency = taxes[result[0]]['obj'].company_id.currency_id
                taxes[result[0]]['periods'][period_number]['net'] = from_currency.compute(result[1], used_currency)
                taxes[result[0]]['show'] = True

    @api.model
    def _lines(self, line_id=None):
        lines = []
        context = self.env.context
        unfold_taxes = context.get('context_id').unfolded_tax_ids.ids
        tax_ids = self.env['account.tax'].search([])
        company_ids = context.get('context_id').multicompany_manager_id.company_ids
        if company_ids:
            tax_ids = self.env['account.tax'].search([('company_id','in',company_ids.ids)])
        if context.get('context_id').tax_ids:
            tax_ids = context.get('context_id').tax_ids
        if line_id:
            tax_ids = self.env['account.tax'].search([('id','=',line_id)])

        final_untaxed_amount_total = 0.0
        final_gst_total = 0.0
        final_amount_total = 0.0
        for tax in tax_ids:
            domain = [('date','>=',context.get('date_from')),('date','<=',context.get('date_to'))]
            domain += [('tax_line_id','=',tax.id)]
            if company_ids:
                domain += [('company_id','in',company_ids.ids)]
            states = []
            if context.get('context_id').tax_report_unpost:
                states.append('draft')
            if context.get('context_id').tax_report_post:
                states.append('posted')
            if not states:
                states = ['draft','posted']
            domain += [('move_id.state', 'in', states)]
            if context.get('context_id').account_ids:
                domain += [('account_id','in',context.get('context_id').account_ids.ids)]
            if context.get('context_id').currency_ids:
                domain += [('currency_id','in',context.get('context_id').currency_ids.ids)]
            untaxed_amount_total = 0.0
            gst_total = 0.0
            amount_total = 0.0

            move_ids = self.env['account.move.line'].search(domain)
            for move in move_ids:
                UsedCurrency = self.env.user.company_id.currency_id.with_context(date=move.date)
                try:
                    if move.invoice_id:
                        invoice_id = move.invoice_id
                        if invoice_id.currency_id and invoice_id.currency_id.id != self.env.user.company_id.currency_id.id:
                            InvoiceCurrency = invoice_id.currency_id.with_context(date=move.date)
                            amount_currency = InvoiceCurrency.compute(
                                invoice_id.amount_untaxed, self.env.user.company_id.currency_id)
                            sub_total = amount_currency
                        elif self.env.context.get('change_currency'):
                            currency_id = self.env.context.get('change_currency').with_context(date=move.date)
                            InvoiceCurrency = invoice_id.currency_id.with_context(date=move.date)
                            amount_currency = InvoiceCurrency.compute(
                                invoice_id.amount_untaxed,
                                currency_id)
                            sub_total = amount_currency

                        else:
                            sub_total = move.invoice_id.amount_untaxed
                    else:
                        if self.env.context.get('change_currency'):
                            currency_id = self.env.context.get('change_currency').with_context(date=move.date)
                            gst_amount = UsedCurrency.compute(move.balance, currency_id)
                            sub_total = round(gst_amount / (tax.amount / 100))
                        else:
                            sub_total = round(move.balance / (tax.amount / 100))

                except:
                    sub_total = 0.0
                gst_amount = abs(round(move.balance, 2))
                if self.env.context.get('change_currency'):
                    currency_id = self.env.context.get('change_currency').with_context(date=move.date)
                    gst_amount = UsedCurrency.compute(gst_amount, currency_id)
                untaxed_amount_total += sub_total
                gst_total += gst_amount
                amount_total += (sub_total + gst_amount)
                # Final total
                final_untaxed_amount_total += sub_total
                final_gst_total += gst_amount
                final_amount_total += (sub_total + gst_amount)

            lines.append({
                'id': tax.id,
                'type': 'line',
                'name': tax.name + ' (' + str(tax.amount) + ')',
                'footnotes': self.env.context.get('context_id')._get_footnotes('line', tax.id),
                'columns': ['', '', '', '', '', self._format(untaxed_amount_total), self._format(gst_total), self._format(amount_total)],
                'level': 2,
                'unfoldable': True,
                'unfolded': tax.id in unfold_taxes,
            })

            if tax.id in unfold_taxes:
                move_ids = self.env['account.move.line'].search(domain)
                for move in move_ids:
                    date = datetime.strptime(move.date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
                    account_name = move.account_id.code + ' - ' + move.account_id.name
                    ref_no = move.move_id.name
                    UsedCurrency = self.env.user.company_id.currency_id.with_context(date=move.date)
                    gst_amount = abs(move.balance)
                    currency_name = ''
                    if self.env.context.get('change_currency'):
                        currency_name = self.env.context.get('change_currency').name
                        currency_id = self.env.context.get('change_currency').with_context(date=move.date)
                        gst_amount = UsedCurrency.compute(gst_amount, currency_id)
                    try:
                        if move.invoice_id:
                            invoice_id = move.invoice_id
                            InvoiceCurrency = invoice_id.currency_id.with_context(date=move.date)
                            if invoice_id.currency_id and invoice_id.currency_id.id != self.env.user.company_id.currency_id.id:
                                amount_currency = InvoiceCurrency.compute(
                                    invoice_id.amount_untaxed, self.env.user.company_id.currency_id)
                                sub_total = amount_currency
                            elif self.env.context.get('change_currency'):
                                currency_id = self.env.context.get('change_currency').with_context(date=move.date)
                                amount_currency = InvoiceCurrency.compute(
                                    invoice_id.amount_untaxed, currency_id)
                                sub_total = amount_currency

                            else:
                                sub_total = move.invoice_id.amount_untaxed
                        else:
                            if self.env.context.get('change_currency'):
                                currency_id = self.env.context.get('change_currency').with_context(date=move.date)
                                gst_amount = UsedCurrency.compute(move.balance, currency_id)
                                sub_total = round(gst_amount / (tax.amount / 100))
                            else:
                                sub_total = round(move.balance / (tax.amount / 100))
                    except:
                        sub_total = 0.0
                    currency = currency_name and currency_name or (move.currency_id.name or move.company_id.currency_id.name)
                    lines.append({
                        'id': tax.id,
                        'name': move.move_id.name or '/',
                        'type': 'move_line_id',
                        'action': ['account.move', move.move_id.id, _('View Journal Entry'), False],
                        'footnotes': self.env.context.get('context_id')._get_footnotes('tax_id', tax.id),
                        'columns': [date, account_name, ref_no, move.move_id.name, context.get('change_currency') and context.get('change_currency').name or currency, self._format(sub_total), self._format(gst_amount), self._format(sub_total+gst_amount)],
                        'level': 1,
                    })
                lines.append({
                    'id': tax.id,
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total') + ' ' + (tax.name),
                    'footnotes': self.env.context.get('context_id')._get_footnotes('o_account_reports_domain_total', tax.id),
                    'columns': ['', '', '', '', '', self._format(untaxed_amount_total), self._format(gst_total), self._format(amount_total)],
                    'level': 1,
                })
        # Final total
        if not line_id:
            lines.append({
                'id': 0,
                'type': 'o_account_reports_domain_total',
                'name': _('Total'),
                'footnotes': self.env.context.get('context_id')._get_footnotes('o_account_reports_domain_total', 0),
                'columns': ['', '', '', '', '', self._format(final_untaxed_amount_total), self._format(final_gst_total), self._format(final_amount_total)],
                'level': 0,
            })
        return lines
