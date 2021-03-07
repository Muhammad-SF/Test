# -*- coding: utf-8 -*-
# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    treasury_planning = fields.Boolean(string="Treasury Planning")

    @api.multi
    def compute_bank_balance(self, date_str):
        """Computes bank saldo of this journal at the given date"""
        self.ensure_one()
        msg = ''
        # get correct bank statement
        date = datetime.strptime(date_str, DEFAULT_SERVER_DATE_FORMAT).date()
        statement = self.env['account.bank.statement'].search([
            ('journal_id', '=', self.id),
            ('initial_date', '<=', date),
            ('final_date', '>=', date),
        ])
        if len(statement) != 1:
            msg = "{}: None or too many bank statements \
                found for this date!".format(self.name)
            return statement, 0, msg

        # adding to the initial balance all the bank moves to that date
        bank_balance = statement.balance_start
        lines_filtered = statement.line_ids.filtered(
            lambda r: r.date <= date_str)
        for line in lines_filtered:
            bank_balance += line.amount

        return statement, bank_balance, msg

    @api.model
    def create(self, vals):
        """at creation of a treasury planning journal, the accounts automatically
           created by default are deleted"""
        res = super(AccountJournal, self).create(vals)
        account = res.default_credit_account_id

        if res.treasury_planning:
            account.unlink()

        return res
