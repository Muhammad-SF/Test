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
import datetime

from odoo import fields, models, exceptions, api
from odoo.tools.translate import _

class account_analytic_profit(models.TransientModel):
    _name = 'hr.timesheet.analytic.profit'
    _description = 'Print Timesheet Profit'

    date_from     = fields.Date('From', required=True)
    date_to       = fields.Date('To', required=True)
    # journal_ids = fields.Many2many('account.analytic.journal', 'analytic_profit_journal_rel', 'analytic_id', 'journal_id', 'Journal', required=True)
    employee_ids  = fields.Many2many('res.users', 'analytic_profit_emp_rel', 'analytic_id', 'emp_id', 'User', required=True)

    def _date_from(*a):
        return datetime.date.today().replace(day=1).strftime('%Y-%m-%d')

    def _date_to(*a):
        return datetime.date.today().strftime('%Y-%m-%d')

    _defaults = {
        'date_from' : _date_from,
        'date_to'   : _date_to
    }

    @api.multi
    def print_report(self):
        line_obj     = self.env['account.analytic.line']
        data         = {}
        data['form'] = self.read()[0]
        lines        = line_obj.search([
            ('date', '>=', data['form']['date_from']),
            ('date', '<=', data['form']['date_to']),
            # ('journal_id', 'in', data['form']['journal_ids']),
            ('user_id', 'in', data['form']['employee_ids']),
        ])
        # if not lines:
        #     raise exceptions.Warning(_('No record(s) found for this report.'))

        # data['form']['journal_ids'] = [(6, 0, data['form']['journal_ids'])] # Improve me => Change the rml/sxw so that it can support withou [0][2]
        data['form']['employee_ids'] = [(6, 0, data['form']['employee_ids'])]
        datas = {
            'ids'   : [],
            'model' : 'account.analytic.line',
            'form'  : data['form']
        }
        return self.env['report'].get_action([], 'stable_hr_timesheet_invoice.report_analyticprofit', data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
