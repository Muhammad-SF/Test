# -*- coding: utf-8 -*-
##############################################################################
#
#        MISSING OPEN POINTS IN TESTS
#        - MISSING FINAL BALANCE FINANCIAL FORECASTS!!
#        - SUDO () FOR USER in SETUP
#
##############################################################################

from datetime import date, timedelta
from odoo.addons.account.tests.account_test_users import AccountTestUsers

import logging
_logger = logging.getLogger(__name__)


class TestTreasuryForecast(AccountTestUsers):

    def setUp(self):
        super(TestTreasuryForecast, self).setUp()

        # setup accounting data
        self.today = date.today().strftime('%Y-%m-%d')
        self.account_model = self.env['account.account']
        self.move_model = self.env['account.move']
        self.move_line_model = self.env['account.move.line']
        self.journal_model = self.env['account.journal']
        self.bank_stat_model = self.env['account.bank.statement']
        self.forecast_model = self.env['treasury.forecast']
        self.template_model = self.env['treasury.forecast.template']
        self.company = self.env.ref('base.main_company')

        self.miscellaneous_journal = self.env['account.journal'].search(
            [('type', '=', 'general')])[0]
        self.miscellaneous_journal.update_posted = True  # ???

        # creating unique treasury planning account
        account_user_type = self.env.ref('account.data_account_type_receivable')

        self.credit_account = self.account_model.create({
            'code': '1234567',
            'name': 'Testing treasury management',
            'treasury_planning': True,
            'reconcile': True,
            'user_type_id': account_user_type.id,
        })

        # creating treasury managemnt journal and bank statement
        self.journal = self.journal_model.create({
            'name': 'Treasury planning journal',
            'type': 'bank',
            'code': 'FINPL',
            'treasury_planning': True,
        })

        self.bank_stat = self.bank_stat_model.create({
            'name': 'Virtual bank',
            'journal_id': self.journal.id,
            'date': self.today,
            'balance_start': 1000,
        })

        # create treasury forecast
        self.forecast = self.forecast_model.create({
            'name': 'Periodic test forecast',
            'date_start': (date.today() - timedelta(days=5)).strftime('%Y-%m-%d'),
            'date_end': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'initial_balance': 2000,
            'company_id': self.company.id,
        })

    def test_account_move_treasury(self):
        # create account move
        self.move = self.move_model.create({
            'journal_id': self.miscellaneous_journal.id,
            'date': self.today,
            'ref': 'Test treasury account move',
            })

        # create credit move line
        receivables_line_1 = self.move_line_model.with_context(
            check_move_validity=False).create({
                'move_id': self.move.id,
                'account_id': self.credit_account.id,
                'name': 'Test credit line',
                'debit': 150,
                'date_maturity': self.today,
            })

        receivables_line_2 = self.move_line_model.with_context(
            check_move_validity=False).create({
                'move_id': self.move.id,
                'account_id': self.credit_account.id,
                'name': 'Test credit line',
                'debit': 50,
                'date_maturity': (date.today() + timedelta(days=15)).strftime('%Y-%m-%d'),
            })

        # create credit move line
        payables_line = self.move_line_model.create({
            'move_id': self.move.id,
            'account_id': self.credit_account.id,
            'name': 'Test debit line',
            'credit': 200,
            'date_maturity': self.today,
            })

        self.move.post()
        self.assertEqual(self.forecast.receivables, 150)
        self.assertEqual(self.forecast.payables, -200)
        self.assertEqual(self.forecast.periodic_saldo, -50)
        self.assertEqual(self.forecast.final_balance, 1950)
