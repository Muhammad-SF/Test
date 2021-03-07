# -*- coding: utf-8 -*-

from odoo import models, api, _, fields
from odoo.tools.misc import formatLang
import time
import logging

from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)

class ReportAgedPartnerBalance(models.AbstractModel):
    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines2(self, account_type, date_from, target_move, period_length, target_domain):
        if self.env.context.get('forecast_report', False):
            date_from = '2100-12-31' # setting higher end date to get all invoices
        report_date_query = '(l.date <= %s)'

        context_change_currency_id = self.env.context.get('change_currency')

        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            periods[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.user.company_id.id
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, user_company)
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND ''' + report_date_query + '''
                AND l.company_id = %s
                AND l.invoice_id is not NULL
                AND (SELECT state FROM account_invoice WHERE id = l.invoice_id) = 'open'
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], []

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        rate_dict = {}
        currency_dict = {}
        if target_domain:
            query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (SELECT currency_id FROM account_invoice WHERE id = l.invoice_id) in %s
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND ''' + report_date_query + '''
                AND l.company_id = %s
                AND l.invoice_id is not NULL
                AND (SELECT state FROM account_invoice WHERE id = l.invoice_id) = 'open'
                '''
            cr.execute(query, (tuple(move_state),tuple(target_domain), tuple(account_type), date_from, tuple(partner_ids), date_from, user_company))
        else:
            query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND ''' + report_date_query + '''
                AND l.company_id = %s
                AND l.invoice_id is not NULL
                AND (SELECT state FROM account_invoice WHERE id = l.invoice_id) = 'open'
                '''
            cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, user_company))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        aml_ids = self.env['account.move.line'].search([('id', 'in', aml_ids)], order='date')
        for line in aml_ids:
            change_currency_id = ''
            if context_change_currency_id:
                change_currency_id = self.env.context.get('change_currency').with_context(date=line.date)
                UsedCurrency = self.env.user.company_id.currency_id.with_context(date=line.date)
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = change_currency_id and UsedCurrency.compute(line.balance, change_currency_id) or line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount += change_currency_id and UsedCurrency.compute(partial_line.amount, change_currency_id) or partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount -= change_currency_id and UsedCurrency.compute(partial_line.amount, change_currency_id) or partial_line.amount
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                if line.move_id:
                    currency = self.env['account.invoice'].search([('number','=',line.move_id.name)],limit=1).currency_id
                    currency_dict[partner_id] = change_currency_id and change_currency_id.name or currency.name
                if context_change_currency_id:
                    amount_currency = UsedCurrency.compute(line.amount_currency, change_currency_id)
                    amount_residual = UsedCurrency.compute(line.amount_residual, change_currency_id)
                else:
                    amount_currency = line.amount_currency
                    amount_residual = line.amount_residual
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 5,
                    'main_period': 0,
                    'amount_currency': abs(amount_currency) or line_amount,
                    'amount_residual': abs(amount_residual) or line_amount,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, user_company)
            if target_domain:
                query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND ''' + report_date_query + '''
                    AND l.company_id = %s
                    AND (SELECT currency_id FROM account_invoice WHERE id = l.invoice_id) in %s
                    AND l.invoice_id is not NULL
                    AND (SELECT state FROM account_invoice WHERE id = l.invoice_id) = 'open'
                    '''
                args_list += (tuple(target_domain),)
            else:
                query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND ''' + report_date_query + '''
                    AND l.company_id = %s
                    AND l.invoice_id is not NULL
                    AND (SELECT state FROM account_invoice WHERE id = l.invoice_id) = 'open'
                    '''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            # Ordering records based on date
            aml_ids = self.env['account.move.line'].search([('id','in',aml_ids)], order='date')
            for line in aml_ids:
                change_currency_id = ''
                if context_change_currency_id:
                    change_currency_id = self.env.context.get('change_currency').with_context(date=line.date)
                    UsedCurrency = self.env.user.company_id.currency_id.with_context(date=line.date)
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = change_currency_id and UsedCurrency.compute(line.balance, change_currency_id) or line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount += change_currency_id and UsedCurrency.compute(partial_line.amount, change_currency_id) or partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount -= change_currency_id and UsedCurrency.compute(partial_line.amount, change_currency_id) or partial_line.amount

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    if self.env.context.get('change_currency'):
                        amount_currency = UsedCurrency.compute(line.amount_currency, change_currency_id)
                        amount_residual = UsedCurrency.compute(line.amount_residual, change_currency_id)
                    else:
                        amount_currency = line.amount_currency
                        amount_residual = line.amount_residual

                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i,
                        'amount_currency': abs(amount_currency) or line_amount,
                        'amount_residual': abs(amount_residual) or line_amount,
                    })
            history.append(partners_amount)
        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]
            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt

            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
            if at_least_one_amount:
                res.append(values)
        return res, total, lines

class report_account_aged_partner(models.AbstractModel):
    _inherit = "account.aged.partner"

    def _format(self, value):
        if self.env.context.get('no_format'):
            return value
        currency_id = self.env.user.company_id.currency_id
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
    def _lines(self, context, line_id=None):
        sign = 1.0
        lines = []
        multi_currency = False
        context_change_currency_id = self.env.context.get('change_currency')
        report_type = self.env.context.get('account_type')
        currency_ids = self._context.get('currency_ids',[])
        results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines2([self._context['account_type']], self._context['date_to'], 'posted', 30, currency_ids)
        config_setting = self.env['account.config.settings'].search([],order='id desc', limit=1)
        if config_setting and config_setting.group_multi_currency:
            multi_currency = True

        # Calculate invoice currency amount total
        partner_total_amount = {}
        partner_due_amount = {}

        partner_ids = []
        for line in results:
            partner_ids.append(line.get('partner_id'))
        partner_ids = list(set(partner_ids))
        for partner_id in amls:
            if partner_id in partner_ids:
                for line in amls.get(partner_id):

                    aml = line['line']
                    invoice = self.env['account.invoice'].search([('number', '=', aml.move_id.name)], limit=1)
                    invoice_sign = 1.0
                    change_currency_id = ''

                    amount_currency = aml.amount_currency
                    credit = aml.credit
                    debit = aml.debit
                    amount_residual = aml.amount_residual
                    amount_residual_currency = aml.amount_residual_currency

                    if context_change_currency_id:
                        change_currency_id = self.env.context.get('change_currency').with_context(date=aml.date)
                        UsedCurrency = self.env.user.company_id.currency_id.with_context(date=aml.date)

                        amount_currency = aml.amount_currency and  UsedCurrency.compute(aml.amount_currency, change_currency_id) or 0.0
                        credit = aml.debit and UsedCurrency.compute(aml.debit, change_currency_id) or 0.0
                        debit = aml.debit and UsedCurrency.compute(aml.debit, change_currency_id) or 0.0
                        amount_residual = aml.amount_residual and UsedCurrency.compute(aml.amount_residual, change_currency_id) or 0.0
                        amount_residual_currency = aml.amount_residual_currency and UsedCurrency.compute(aml.amount_residual_currency, change_currency_id) or 0.0

                    if invoice.type in ('out_refund', 'in_refund'):
                        invoice_sign = -1.0
                    # Currency Total
                    if self.env.context.get('filter_original_currency'):
                        if partner_id not in partner_total_amount:
                            partner_total_amount.update(
                                {partner_id: (invoice_sign * (amount_currency or debit or credit))})
                        else:
                            partner_total_amount.update({partner_id: partner_total_amount.get(partner_id) + round(
                                invoice_sign * (amount_currency or debit or credit), 2)})
                    else:
                        if partner_id not in partner_due_amount:
                            partner_total_amount.update({partner_id: (invoice_sign * (debit or credit))})
                        else:
                            partner_total_amount.update({partner_id: partner_total_amount.get(partner_id) + (
                                invoice_sign * (debit or credit))})

                    # Residual Total
                    if self.env.context.get('filter_original_currency'):
                        if partner_id not in partner_due_amount:
                            partner_due_amount.update({partner_id: (invoice_sign * (amount_residual_currency or amount_residual))})
                        else:
                            partner_due_amount.update({partner_id: partner_due_amount.get(partner_id) + (invoice_sign * (amount_residual_currency or amount_residual))})
                    else:
                        if partner_id not in partner_due_amount:
                            partner_due_amount.update({partner_id: (invoice_sign * (amount_residual))})
                        else:
                            partner_due_amount.update({partner_id: partner_due_amount.get(partner_id) + (invoice_sign * (amount_residual))})
        # Not due invoices
        partner_not_due_dict = {}
        partner_totals = {}
        partner_totals_final = {0: 0.00, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00}
        if self.env.context.get('forecast_report') == 'on':
            partner_totals_final = {-3: 0.00, -2: 0.00, -1: 0.00, 0: 0.00, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00}
        if self.env.context.get('forecast_report') == 'summary':
            partner_totals_final = {'summary': 0.00, 0: 0.00, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00}
        current_date = datetime.strptime(self._context['date_to'], "%Y-%m-%d")
        for values in results:
            # Not due invoices
            domain = [('partner_id','=',values['partner_id']),('date_due','>',self.env.context.get('date_to')),('date_invoice','<=',self.env.context.get('date_to')),('state','=','open')]
            domain.append(('company_id','in',self.env.context['context_id'].company_ids.ids))
            invoice_ids = self.env['account.invoice'].search(domain)
            partner_not_due_dict.update({values['partner_id']: 0.00})
            for invoice in invoice_ids:
                residual_signed = invoice.residual_signed

                if self.env.context.get('change_currency'):
                    change_currency_id = self.env.context.get('change_currency').with_context(date=aml.date)
                    UsedCurrency =  self.env.user.company_id.currency_id.with_context(date= invoice.date_invoice and invoice.date_invoice or invoice.create_date)
                    residual_signed = UsedCurrency.compute(invoice.residual_signed, change_currency_id) or 0.0
                partner_not_due_dict.update({values['partner_id']: partner_not_due_dict.get(values['partner_id']) + (residual_signed and residual_signed or invoice.residual_signed)})

            # Total per period
            partner_totals.update({values['partner_id']: {0: 0.00, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00}})
            if self.env.context.get('forecast_report') == 'on':
                partner_totals.update({values['partner_id']: {-3: 0.00, -2: 0.00, -1: 0.00, 0: 0.00, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00}})
            if self.env.context.get('forecast_report') == 'summary':
                partner_totals.update({values['partner_id']: {'summary': 0.00, 0: 0.00, 1: 0.00, 2: 0.00, 3: 0.00, 4: 0.00}})
            for line in amls[values['partner_id']]:
                aml = line['line']
                invoice = self.env['account.invoice'].search([('number', '=', aml.move_id.name)], limit=1)
                currency_id = invoice.currency_id or self.env.user.company_id.currency_id
                if self.env.context.get('chanage_currency'):
                    currency_id = self.env.context.get('change_currency')
                invoice_sign = 1.0
                if invoice.type in ('out_refund', 'in_refund'):
                    invoice_sign = -1.0
                if invoice:
                    currency_rate = invoice.with_context(date=invoice.date_invoice).currency_id.rate
                else:
                    currency_rate = currency_id.rate
                age = current_date - current_date
                if self.env.context.get('aging_due_filter_cmp'):
                    if invoice.date_due:
                        age = current_date - datetime.strptime(invoice.date_due, "%Y-%m-%d")
                elif invoice.date_invoice:
                    age = current_date - datetime.strptime(invoice.date_invoice, "%Y-%m-%d")

                amount_residual = aml.amount_residual
                amount_residual_currency = aml.amount_residual_currency

                if self.env.context.get('change_currency') and aml.currency_id != self.env.context.get('change_currency'):
                    change_currency_id = self.env.context.get('change_currency').with_context(date=aml.date)
                    UsedCurrency = self.env.user.company_id.currency_id.with_context(date=aml.date)
                    amount_residual = aml.amount_residual and UsedCurrency.compute(aml.amount_residual, change_currency_id) or 0.0
                    amount_residual_currency = aml.amount_residual_currency and UsedCurrency.compute(aml.amount_residual_currency, change_currency_id) or 0.0

                if self.env.context.get('forecast_report') == 'on':
                    # -120 days
                    if age.days < -60:
                        amount = partner_totals.get(values['partner_id']).get(-3)
                        if self.env.context.get('filter_original_currency'):
                            partner_totals.get(values['partner_id']).update({-3: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                            partner_totals_final.update({-3: partner_totals_final.get(-3) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        else:
                            partner_totals.get(values['partner_id']).update({-3: amount + (invoice_sign * abs(amount_residual))})
                            partner_totals_final.update({-3: partner_totals_final.get(-3) + (invoice_sign * abs(amount_residual))})
                    # -60 days
                    if age.days < -30 and age.days >= -60:
                        amount = partner_totals.get(values['partner_id']).get(-2)
                        if self.env.context.get('filter_original_currency'):
                            partner_totals.get(values['partner_id']).update({-2: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                            partner_totals_final.update({-2: partner_totals_final.get(-2) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        else:
                            partner_totals.get(values['partner_id']).update({-2: amount + (invoice_sign * abs(amount_residual))})
                            partner_totals_final.update({-2: partner_totals_final.get(-2) + (invoice_sign * abs(amount_residual))})
                    # -30 days
                    if age.days < 0 and age.days >= -30:
                        amount = partner_totals.get(values['partner_id']).get(-1)
                        if self.env.context.get('filter_original_currency'):
                            partner_totals.get(values['partner_id']).update({-1: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                            partner_totals_final.update({-1: partner_totals_final.get(-1) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        else:
                            partner_totals.get(values['partner_id']).update({-1: amount + (invoice_sign * abs(amount_residual))})
                            partner_totals_final.update({-1: partner_totals_final.get(-1) + (invoice_sign * abs(amount_residual))})
                # Summary Report Value calculation
                if self.env.context.get('forecast_report') == 'summary':
                    if age.days < 0:
                        amount = partner_totals.get(values['partner_id']).get('summary')
                        if self.env.context.get('filter_original_currency'):
                            partner_totals.get(values['partner_id']).update({'summary': amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                            partner_totals_final.update({'summary': partner_totals_final.get('summary') + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        else:
                            partner_totals.get(values['partner_id']).update({'summary': amount + (invoice_sign * abs(amount_residual))})
                            partner_totals_final.update({'summary': partner_totals_final.get('summary') + (invoice_sign * abs(amount_residual))})
                # 0-30 days
                if age.days >= 0 and age.days <= 30:
                    amount = partner_totals.get(values['partner_id']).get(0)
                    if self.env.context.get('filter_original_currency'):
                        partner_totals.get(values['partner_id']).update({0: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        partner_totals_final.update({0: partner_totals_final.get(0) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                    else:
                        partner_totals.get(values['partner_id']).update({0: amount + (invoice_sign * abs(amount_residual))})
                        partner_totals_final.update({0: partner_totals_final.get(0) + (invoice_sign * abs(amount_residual))})
                # 30-60 days
                if age.days >= 31 and age.days <= 60:
                    amount = partner_totals.get(values['partner_id']).get(1)
                    if self.env.context.get('filter_original_currency'):
                        partner_totals.get(values['partner_id']).update({1: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        partner_totals_final.update({1: partner_totals_final.get(1) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                    else:
                        partner_totals.get(values['partner_id']).update({1: amount + (invoice_sign * abs(amount_residual))})
                        partner_totals_final.update({1: partner_totals_final.get(1) + (invoice_sign * abs(amount_residual))})
                # 60-90 days
                if age.days >= 61 and age.days <= 90:
                    amount = partner_totals.get(values['partner_id']).get(2)
                    if self.env.context.get('filter_original_currency'):
                        partner_totals.get(values['partner_id']).update({2: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        partner_totals_final.update({2: partner_totals_final.get(2) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                    else:
                        partner_totals.get(values['partner_id']).update({2: amount + (invoice_sign * abs(amount_residual))})
                        partner_totals_final.update({2: partner_totals_final.get(2) + (invoice_sign * abs(amount_residual))})
                # 90-120 days
                if age.days >= 91 and age.days <= 120:
                    amount = partner_totals.get(values['partner_id']).get(3)
                    if self.env.context.get('filter_original_currency'):
                        partner_totals.get(values['partner_id']).update({3: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        partner_totals_final.update({3: partner_totals_final.get(3) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                    else:
                        partner_totals.get(values['partner_id']).update({3: amount + (invoice_sign * abs(amount_residual))})
                        partner_totals_final.update({3: partner_totals_final.get(3) + (invoice_sign * abs(amount_residual))})
                # >120 days
                if age.days > 120:
                    amount = partner_totals.get(values['partner_id']).get(4)
                    if self.env.context.get('filter_original_currency'):
                        partner_totals.get(values['partner_id']).update({4: amount + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                        partner_totals_final.update({4: partner_totals_final.get(4) + (invoice_sign * abs(amount_residual_currency or amount_residual))})
                    else:
                        partner_totals.get(values['partner_id']).update({4: amount + (invoice_sign * abs(amount_residual))})
                        partner_totals_final.update({4: partner_totals_final.get(4) + (invoice_sign * abs(amount_residual))})

        for values in results:
            if not partner_due_amount.get(values['partner_id']):
                continue
            partner_total_line = partner_totals.get(values['partner_id'])
            columns = [partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
            if self.env.context.get('forecast_report') == 'on':
                columns = [partner_total_line[-3], partner_total_line[-2], partner_total_line[-1], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
            if self.env.context.get('forecast_report') == 'summary':
                columns = [partner_total_line['summary'], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
            if self.env.context.get('aging_due_filter_cmp'):
                # columns = [partner_not_due_dict.get(values['partner_id']), partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3] + partner_total_line[4]]
                columns = [partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                if self.env.context.get('forecast_report') == 'on':
                    columns = [partner_total_line[-3], partner_total_line[-2], partner_total_line[-1], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                if self.env.context.get('forecast_report') == 'summary':
                    columns = [partner_total_line['summary'], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
            if line_id and values['partner_id'] != line_id:
                continue
            if context.show_all == False:
                unfold_value = False
            else:
                unfold_value = values['partner_id'] and (values['partner_id'] in context.unfolded_partners.ids) or context.show_all or False
            vals = {
                'id': values['partner_id'] and values['partner_id'] or -1,
                'name': values['name'],
                'level': 0 if values['partner_id'] else 2,
                'type': values['partner_id'] and 'partner_id' or 'line',
                'footnotes': context._get_footnotes('partner_id', values['partner_id']),
                'columns': columns,
                'multi_currency': multi_currency,
                'trust': values['trust'],
                'unfoldable': values['partner_id'] and True or False,
                'unfolded': unfold_value,
            }
            vals['columns'] = [''] + [self._format(t) for t in vals['columns']]
            if self.env.context.get('filter_original_currency'):
                vals['columns'].extend([self._format(partner_due_amount.get(values['partner_id']))])
                vals['columns'].extend([self._format(sign * partner_total_amount.get(values['partner_id'])), ''])
            else:
                vals['columns'].extend([self._format(partner_due_amount.get(values['partner_id']))])
                vals['columns'].extend([self._format(sign * partner_total_amount.get(values['partner_id'])), ''])
            if self.env.context.get('filter_local_currency') or self.env.context.get('filter_original_currency'):
                vals['columns'].extend(['', ''])
            lines.append(vals)

            if self.env.context.get('show_all') != False and (values['partner_id'] in context.unfolded_partners.ids or context.show_all):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    credit = aml.credit
                    debit = aml.debit
                    amount_residual = aml.amount_residual
                    amount_residual_currency = aml.amount_residual_currency

                    if self.env.context.get('change_currency') and aml.currency_id != self.env.context.get('change_currency'):
                        change_currency_id = self.env.context.get('change_currency').with_context(date=aml.date)
                        UsedCurrency = self.env.user.company_id.currency_id.with_context(date=aml.date)
                        credit = aml.credit and UsedCurrency.compute(aml.credit, change_currency_id) or 0.0
                        debit = aml.debit and UsedCurrency.compute(aml.debit, change_currency_id) or 0.0
                        amount_residual = aml.amount_residual and UsedCurrency.compute(aml.amount_residual, change_currency_id) or 0.0
                        amount_residual_currency = aml.amount_residual_currency and UsedCurrency.compute(aml.amount_residual_currency, change_currency_id) or 0.0

                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'move_id': aml.move_id.id,
                        'partnerid':values['partner_id'],
                        'action': aml.get_model_id_and_name(),
                        'multi_currency':multi_currency,
                        'level': 1,
                        'type': 'move_line_id',
                        'footnotes': context._get_footnotes('move_line_id', aml.id),
                    }

                    invoice = self.env['account.invoice'].search([('number','=',aml.move_id.name)],limit=1)
                    currency_id = invoice.currency_id or self.env.user.company_id.currency_id
                    print 'Invoice : ', invoice
                    if invoice:
                        currency_rate = change_currency_id and change_currency_id.rate or invoice.with_context(date=invoice.date_invoice).currency_id.rate
                    else:
                        currency_rate = change_currency_id and change_currency_id.rate or currency_id.rate
                    print 'Currency Rate : ', currency_rate
                    invoice_sign = 1.0
                    if invoice.type in ('out_refund', 'in_refund'):
                        invoice_sign = -1.0
                    age = current_date - current_date
                    if self.env.context.get('aging_due_filter_cmp'):
                        if invoice.date_due:
                            age = current_date - datetime.strptime(invoice.date_due, "%Y-%m-%d")
                    elif invoice.date_invoice:
                        age = current_date - datetime.strptime(invoice.date_invoice, "%Y-%m-%d")

                    # Calculating period based amount
                    if self.env.context.get('aging_due_filter_cmp'):
                        if invoice.date_due:
                            # cmp_date_due = datetime.strptime(invoice.date_due, "%Y-%m-%d")
                            final_columns = []
                            # if cmp_date_due <= current_date:
                            # due_date = current_date
                            # report_date = datetime.strptime(self.env.context.get('date_to'), "%Y-%m-%d")
                            # if invoice.date_due:
                            #     due_date = datetime.strptime(invoice.date_due, "%Y-%m-%d")
                            if self.env.context.get('forecast_report') == 'on':
                                # -120 days
                                if age.days < -60:
                                    if self.env.context.get('filter_original_currency'):
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                    else:
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                                else:
                                    final_columns.append('')
                                # -60 days
                                if (age.days < -30 and age.days >= -60):
                                    if self.env.context.get('filter_original_currency'):
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                    else:
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                                else:
                                    final_columns.append('')
                                # -30 days
                                if (age.days < 0 and age.days >= -30):
                                    if self.env.context.get('filter_original_currency'):
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                    else:
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                                else:
                                    final_columns.append('')
                            # Summary report value calculation
                            if self.env.context.get('forecast_report') == 'summary':
                                if age.days < 0:
                                    if self.env.context.get('filter_original_currency'):
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                    else:
                                        final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                                else:
                                    final_columns.append('')
                            # 0-30 days
                            if (age.days >= 0 and age.days <= 30):
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')

                            # 30-60 days
                            if age.days >= 31 and age.days <= 60:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')
                            # 60-90 days
                            if age.days >= 61 and age.days <= 90:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')

                            if age.days >= 91 and age.days <= 120:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(
                                        invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')
                            # >120 days
                            if age.days > 120:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(
                                        invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')
                    else:
                        final_columns = []
                        if self.env.context.get('forecast_report') == 'on':
                            # -120 days
                            if age.days < -60:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')
                            # -60 days
                            if age.days < -30 and age.days >= -60:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')
                            # -30 days
                            if age.days < 0 and age.days >= -30:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')
                        # Summary Calculation value changes
                        if self.env.context.get('forecast_report') == 'summary':
                            if age.days < 0:
                                if self.env.context.get('filter_original_currency'):
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                                else:
                                    final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                            else:
                                final_columns.append('')
                        # 0-30 days
                        if age.days >= 0 and age.days <= 30:
                            if self.env.context.get('filter_original_currency'):
                                final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                            else:
                                final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                        else:
                            final_columns.append('')
                        # 30-60 days
                        if age.days >= 31 and age.days <= 60:
                            if self.env.context.get('filter_original_currency'):
                                final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                            else:
                                final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                        else:
                            final_columns.append('')
                        # 60-90 days
                        if age.days >= 61 and age.days <= 90:
                            if self.env.context.get('filter_original_currency'):
                                final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                            else:
                                final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                        else:
                            final_columns.append('')
                        # 90-120 days
                        if age.days >= 91 and age.days <= 120:
                            if self.env.context.get('filter_original_currency'):
                                final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                            else:
                                final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                        else:
                            final_columns.append('')
                        # >120 days
                        if age.days > 120:
                            if self.env.context.get('filter_original_currency'):
                                final_columns.append(self._format(invoice_sign * abs(amount_residual_currency or amount_residual)))
                            else:
                                final_columns.append(self._format(invoice_sign * abs(amount_residual)))
                        else:
                            final_columns.append('')
                    # Update total
                    invoice_date = invoice.date_invoice and datetime.strptime(invoice.date_invoice, '%Y-%m-%d').strftime('%d-%m-%Y')
                    due_date = invoice.date_due and datetime.strptime(invoice.date_due, '%Y-%m-%d').strftime('%d-%m-%Y')
                    if due_date:
                        cmp_date_due = datetime.strptime(invoice.date_due, "%Y-%m-%d")

                    # if (not self.env.context.get('aging_due_filter_cmp')) or (due_date and (cmp_date_due <= current_date)):
                    # vals['columns'] = [invoice_date, due_date]
                    account_name = invoice.account_id.name_get()[0][1] or ''
                    vals['columns'] = [invoice_date, due_date, account_name]
                    vals['columns'].extend(final_columns)
                    # Changes for adding Filter
                    # if self.env.context.get('aging_due_filter_cmp'):
                    #     vals['columns'].extend([''])
                    if self.env.context.get('filter_original_currency'):
                        vals['columns'].extend([self._format(invoice_sign * abs(amount_residual_currency or amount_residual)) or ''])
                        vals['columns'].extend([self._format(invoice_sign * abs(amount_currency or debit or credit)) or ''])
                    else:
                        vals['columns'].extend([self._format(invoice_sign * abs(amount_residual)) or ''])
                        vals['columns'].extend([self._format(invoice_sign * abs(amount_currency or debit or credit)) or ''])
                    vals['columns'].extend([(age.days)])
                    if self.env.context.get('filter_local_currency') or self.env.context.get('filter_original_currency'):
                        currency_id = change_currency_id and change_currency_id or invoice.currency_id
                        vals['columns'].extend([currency_id.name or '', currency_rate or 0.0])
                    lines.append(vals)

                partner_total_line = partner_totals.get(values['partner_id'])
                columns = [partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                if self.env.context.get('forecast_report') == 'on':
                    columns = [partner_total_line[-3], partner_total_line[-2], partner_total_line[-1], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                if self.env.context.get('forecast_report') == 'summary':
                    columns = [partner_total_line['summary'], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                if self.env.context.get('aging_due_filter_cmp'):
                    columns = [partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                    if self.env.context.get('forecast_report') == 'on':
                        columns = [partner_total_line[-3], partner_total_line[-2], partner_total_line[-1], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                    if self.env.context.get('forecast_report') == 'summary':
                        columns = [partner_total_line['summary'], partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                vals1 = {
                    'id': values['partner_id'],
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total'),
                    'footnotes': self.env.context['context_id']._get_footnotes('o_account_reports_domain_total', values['partner_id']),
                    'columns': columns,
                    'level': 1,
                }
                final_columns1 = [self._format(t) for t in vals1['columns']]
                vals1['columns'] = ['', '', '']
                vals1['columns'].extend(final_columns1)

                if self.env.context.get('filter_original_currency'):
                    vals1['columns'].extend([self._format(sign * partner_due_amount.get(values['partner_id']))])
                    vals1['columns'].extend([self._format(sign * partner_total_amount.get(values['partner_id'])), ''])
                else:
                    vals1['columns'].extend([self._format(sign * partner_due_amount.get(values['partner_id']))])
                    vals1['columns'].extend([self._format(sign * partner_total_amount.get(values['partner_id'])), ''])
                if self.env.context.get('filter_local_currency') or self.env.context.get('filter_original_currency'):
                    vals1['columns'].extend(['', '', ''])
                lines.append(vals1)

        if total and not line_id:
            currency_total = sum(partner_total_amount.values())
            columns = [partner_totals_final[0], partner_totals_final[1], partner_totals_final[2], partner_totals_final[3], partner_totals_final[4]]
            if self.env.context.get('forecast_report') == 'on':
                columns = [partner_totals_final[-3], partner_totals_final[-2], partner_totals_final[-1], partner_totals_final[0], partner_totals_final[1], partner_totals_final[2], partner_totals_final[3], partner_totals_final[4]]
            if self.env.context.get('forecast_report') == 'summary':
                columns = [partner_totals_final['summary'], partner_totals_final[0], partner_totals_final[1], partner_totals_final[2], partner_totals_final[3], partner_totals_final[4]]
            if self.env.context.get('aging_due_filter_cmp'):
                # columns = [partner_not_due_dict.get(values['partner_id']), partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3] + partner_total_line[4]]
                columns = [partner_total_line[0], partner_total_line[1], partner_total_line[2], partner_total_line[3], partner_total_line[4]]
                if self.env.context.get('forecast_report') == 'on':
                    columns = [partner_totals_final[-3], partner_totals_final[-2], partner_totals_final[-1], partner_totals_final[0], partner_totals_final[1], partner_totals_final[2], partner_totals_final[3], partner_totals_final[4]]
                if self.env.context.get('forecast_report') == 'summary':
                    columns = [partner_totals_final['summary'], partner_totals_final[0], partner_totals_final[1], partner_totals_final[2], partner_totals_final[3], partner_totals_final[4]]
            total_line = {
                'id': 0,
                'name': _('Total'),
                'level': 0,
                'multi_currency':multi_currency,
                'type': 'o_account_reports_domain_total',
                'footnotes': context._get_footnotes('o_account_reports_domain_total', 0),
                'columns': columns,
            }
            final_columns = [self._format(t) for t in total_line['columns']]
            total_line['columns'] = ['', '', '']
            total_line['columns'].extend(final_columns)
            if self.env.context.get('filter_original_currency'):
                total_line['columns'].extend([self._format(sign * sum([float(x) for x in partner_due_amount.values()]))])
                total_line['columns'].extend([self._format(sign * currency_total), ''])
            else:
                total_line['columns'].extend([self._format(sign * sum([float(x) for x in partner_due_amount.values()]))])
                total_line['columns'].extend([self._format(sign * currency_total), ''])
            if self.env.context.get('filter_local_currency') or self.env.context.get('filter_original_currency'):
                total_line['columns'].extend(['', '', ''])
            lines.append(total_line)
        return lines

class report_account_aged_receivable(models.AbstractModel):
    _inherit = "account.aged.receivable"

    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.aged.receivable'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_to': context_id.date_to,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'currency_ids': context_id.currency_ids.ids,
            'account_type': 'receivable',
            'forecast_report': context_id.forecast_report if context_id.forecast_report else 'off',
            'change_currency': context_id.change_currency_id,
        })
        return self.with_context(new_context)._lines(context_id, line_id)

    @api.model
    def get_title(self):
        context = self.env.context.get('context') or {}
        if context and context.get('aging_filter_cmp'):
            return _("Aged Receivable - Aging Report")
        if context and context.get('aging_due_filter_cmp'):
            return _("Aged Receivable - Due Aging Report")
        return _("Aged Receivable")


class report_account_aged_payable(models.AbstractModel):
    _inherit = "account.aged.payable"


    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.aged.payable'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_to': context_id.date_to,
            'aged_balance': True,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'currency_ids': context_id.currency_ids.ids,
            'account_type': 'payable',
            'change_currency': context_id.change_currency_id
        })
        return self.with_context(new_context)._lines(context_id, line_id)

