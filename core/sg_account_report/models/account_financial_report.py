# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services (<http://serpentcs.com>).
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
import time
from odoo import models, fields, api, _


class account_financial_report(models.Model):
    _name = "afr"

    name = fields.Char('Name', size= 128, help="""This will be the title that will be displayed in the header of the report. E.g. - "Balance Sheet" or "Income Statement".""", required=True)
    company_id = fields.Many2one('res.company','Company',required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', help="This will be the currency in which the report will be stated in. If no currency is selected, the default currency of the company will be selected.")
    inf_type = fields.Selection([('BS','Balance Sheet'),('IS','Income Statement'),
                                 ('TB', 'Trial Balance'),('GL', 'General Ledger')],
                                 'Type',required=True, default='BS')
    columns = fields.Selection([('one','End. Balance'),('two','Debit | Credit'), ('four','Initial | Debit | Credit | YTD'), 
                                ('five','Initial | Debit | Credit | Period | YTD'),
                                ('qtr',"4 QTR's | YTD"),('thirteen','12 Months | YTD')],
                               'Columns',required=True, default='five')
    display_account = fields.Selection([('all','All Accounts'),('bal', 'With Balance'),('mov','With movements'),
                                        ('bal_mov','With Balance / Movements')],'Display Accounts', default='all')
    display_account_level = fields.Integer('Up To Level',help='Display accounts up to this level (0 to show all)')
    start_date = fields.Datetime('Start Date', required=True, default=time.strftime('%Y-01-01'))
    end_date = fields.Datetime('End Date', required=True, default=time.strftime('%Y-12-31'))
    analytic_ledger = fields.Boolean('Analytic Ledger', help="""You can generate a "Transactions by GL Account" report if you click this check box. Make sure to select "Balance Sheet" and "Initial | Debit | Credit | YTD" in their respective fields.""")
    tot_check = fields.Boolean('Ending Total for Financial Statements ?', help='Please check this box if you would like to get an accumulated amount for each column (Period, Quarter, or Year) at the bottom of this report.')
    lab_str = fields.Char('Description for Ending Total', help="""E.g. - Net Income (Loss)""", size= 128)
    user_id = fields.Many2one("res.users","Current Logged in user")
    target_move = fields.Selection([('posted', 'All Posted Entries'),('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')

    @api.multi
    def copy(self, defaults):
        res_afr = super(account_financial_report,self).copy(defaults)
        for afr_rec in self:
            new_name = _('Copy of %s')%afr_rec.name
            afr_recs = self.search([('name','like',new_name)])
            if afr_recs.ids:
                new_name = '%s (%s)' % (new_name, len(afr_recs.ids)+1)
            afr_rec.name = new_name
        return res_afr

    @api.onchange('inf_type')
    def onchange_inf_type(self):
        if self.inf_type != 'BS':
            self.analytic_ledger = False

    @api.onchange('columns')
    def onchange_columns(self):
        if self.columns != 'four':
            self.analytic_ledger = False

    @api.onchange('analytic_ledger')
    def onchange_analytic_ledger(self):
        context = self.env.context
        company_id = self and self.company_id and self.company_id.id or False
        if context is None:
            context = {}
        ctx = context.copy()
        ctx = dict(ctx)
        ctx['company_id'] = company_id
        company_rec = self.env['res.company'].with_context(context=ctx).browse(company_id)
        self.currency_id = company_rec and company_rec.currency_id and company_rec.currency_id.id or False

    @api.onchange('company_id')
    def onchange_company_id(self):
        context = self.env.context
        company_id = self and self.company_id and self.company_id.id or False
        if context is None:
            context = {}
        ctx = context.copy()
        ctx = dict(ctx)
        ctx['company_id'] = company_id
        if company_id:
            company_rec = self.env['res.company'].with_context(context=ctx).browse(company_id)
            self.currency_id = company_rec and company_rec.currency_id and company_rec.currency_id.id or False
            self.account_ids = []

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: