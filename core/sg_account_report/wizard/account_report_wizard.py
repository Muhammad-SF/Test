# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
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

from odoo import fields, models, api, _
import time
from datetime import datetime
from dateutil import relativedelta
import base64
import xlwt
from cStringIO import StringIO
from odoo.addons.sg_account_report.report.financial_report import account_balance_inherit
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import except_orm, Warning


class wizard_report(models.TransientModel):
    _name = "account.wizard.report"
    _inherit = 'account.common.report'

    @api.multi
    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        '''Returns a dictionary with key=the ID of a record and value = the level of this  
           record in the tree structure.'''
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level

    def _get_children_by_order(self):
        '''returns a recordset of all the children computed recursively, and sorted by sequence. Ready for the printing'''
        res = self
        children = self.search([('parent_id', 'in', self.ids)], order='sequence ASC')
        if children:
            res += children._get_children_by_order()
        return res

    parent_id = fields.Many2one('account.financial.report', 'Parent')
    children_ids = fields.One2many('account.financial.report', 'parent_id', 'Account Report')
    sequence = fields.Integer('Sequence')
    level = fields.Integer(compute='_get_level', string='Level', store=True)
    account_report_id = fields.Many2one('account.financial.report', string='Account Reports', required=True)
    afr_id = fields.Many2one('afr', 'Report Template')
    company_id = fields.Many2one('res.company', 'Company', required = True, default = lambda self: self.env['res.company']._company_default_get('account.invoice'))
    currency_id = fields.Many2one('res.currency', 'Currency', help = "This will be the currency in which the report will be stated in. If no currency is selected, the default currency of the company will be selected.")
    inf_type = fields.Selection([('BS', 'Balance Sheet'), ('IS', 'Profit & Loss'), ('TB', 'Trial Balance'), ('GL', 'General Ledger')],
                                'Type', default = 'BS')
    columns = fields.Selection([('one', 'End. Balance'), ('two', 'Debit | Credit'), ('four', 'Initial | Debit | Credit | YTD'),
                                ('five', 'Initial | Debit | Credit | Period | YTD'), ('qtr', "4 QTR's | YTD"),
                                ('thirteen', '12 Months | YTD')], 'Columns', required = True, default = 'five')
    display_account = fields.Selection([('all', 'All Accounts'), ('bal', 'With Balance'), ('mov', 'With movements'),
                                        ('bal_mov', 'With Balance / Movements')], 'Display Accounts', default = 'all')
    display_account_level = fields.Integer('Up To Level', help = 'Display accounts up to this level (0 to show all)')
    start_date = fields.Date('Start Date', required = True, default = lambda *a: time.strftime('%Y-01-01'))
    end_date = fields.Date('End Date', required = True, default = lambda *a: time.strftime('%Y-12-31'))
    analytic_ledger = fields.Boolean('Analytic Ledger', help = """You can generate a "Transactions by GL Account" report if you click this check box. Make sure to select "Balance Sheet" and "Initial | Debit | Credit | YTD" in their respective fields.""")
    tot_check = fields.Boolean('Ending Total for Financial Statements?', help = 'Please check this box if you would like to get an accumulated amount for each column (Period, Quarter, or Year) at the bottom of this report.')
    lab_str = fields.Char('Description for Ending Total', help = """E.g. - Net Income (Loss)""", size = 128)
    target_move = fields.Selection([('posted', 'All Posted Entries'),('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')


    @api.onchange('columns')
    def onchange_columns(self):
        if self.columns != 'four':
            self.analytic_ledger = False
        if self.columns == 'thirteen' and self.start_date:
            en_date1 = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT)
            en_date = en_date1 + relativedelta.relativedelta(years = 1)
            self.end_date = en_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if self.columns == 'qtr' and self.start_date:
            en_qtr_date2 = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT)
            en_qtr_date = en_qtr_date2 + relativedelta.relativedelta(months = 3)
            self.end_date = en_qtr_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.columns not in ('qtr','thirteen'):
            self.end_date = time.strftime('%Y-12-31')

    @api.onchange('analytic_ledger')
    def onchange_analytic_ledger(self):
        context = self.env.context
        company_id = self.company_id and self.company_id.id or False
        if context is None:
            context = {}
        context = dict(context)
        context.update({'company_id' : company_id})
        cur_id = self.env['res.company'].with_context(context = context).browse(company_id).currency_id.id
        self.currency_id = cur_id or False

    @api.onchange('company_id')
    def onchange_company_id(self):
        context = self.env.context
        company_id = self.company_id and self.company_id.id or False
        if context is None:
            context = {}
        context = dict(context)
        context.update({'company_id' : company_id})
        if company_id:
            cur_id = self.env['res.company'].with_context(context = context).browse(company_id).currency_id.id
            self.currency_id = cur_id or False
            self.afr_id = False
            self.account_list = []

    @api.onchange('afr_id')
    def onchange_afr_id(self):
        afr_rec = self.afr_id or False
        if afr_rec:
            self.currency_id = afr_rec.currency_id and afr_rec.currency_id.id or afr_rec.company_id.currency_id.id
            self.inf_type = afr_rec.inf_type or 'BS'
            self.columns = afr_rec.columns or 'five'
            self.display_account = afr_rec.display_account or 'bal_mov'
            self.display_account_level = afr_rec.display_account_level or 0
            self.analytic_ledger = afr_rec.analytic_ledger or False
            self.tot_check = afr_rec.tot_check or False
            self.lab_str = afr_rec.lab_str or ''
            self.target_move = afr_rec.target_move or 'all'

    @api.multi
    def _get_defaults(self, data):
        cr, uid, context = self.env.args
        user = self.pool.get('res.users').browse(cr, uid, uid, context = context)
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        data['form']['company_id'] = company_id
        data['form']['context'] = context
        return data['form']

    def _build_contexts(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def _print_report(self, data):
        context = self.env.context
        if context is None:
            context = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        selfdata = self.read([])[0]
        data['form'].update(selfdata)
        data['form']['date_from'] = selfdata.get('start_date',False)
        data['form']['date_to'] = selfdata.get('end_date',False)
        data['form']['used_context']['date_from'] = selfdata.get('start_date',False)
        data['form']['used_context']['date_to'] = selfdata.get('end_date',False)
        if data['form']['columns'] == 'qtr':
            acc_mon = 0
            if selfdata['start_date'] and selfdata['end_date']:
                st_date = datetime.strptime(selfdata['start_date'], DEFAULT_SERVER_DATE_FORMAT).date()
                en_date = datetime.strptime(selfdata['end_date'], DEFAULT_SERVER_DATE_FORMAT).date()
                diff = relativedelta.relativedelta(en_date, st_date)
                if st_date == en_date or st_date > en_date:
                    raise Warning(_('Selected dates are not according to quater format'))
                if diff and diff.days and diff.days > 0:
                    raise Warning(_('Selected dates are not according to quater format'))
                if diff and diff.months and diff.months > 0 or diff.years>0:
                    acc_mon = diff.months
                    if diff.years:
                        acc_mon = acc_mon + (diff.years*12)
                if acc_mon!= 0 and (acc_mon%3) != 0:
                    raise Warning(_('Selected dates are not according to quater format\n Please select end date as quater date'))
                quat_num = acc_mon/3
                qtr_dates = {}
                sta_date = st_date
                for quat in range(quat_num):
                    en_date = sta_date + relativedelta.relativedelta(months = 3,days=-1)
                    qtr_dates.update({'qtr' + str(quat + 1):{'date_from':sta_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                              'date_to':en_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                              }
                                      })
                    sta_date = en_date + relativedelta.relativedelta(days = 1)
                data['form'].update({'qtr_dates':qtr_dates,'quat_num':quat_num})
                
        if data['form']['columns'] == 'thirteen':
            acc_mon = 0
            if selfdata['start_date'] and selfdata['end_date']:
                st_date = datetime.strptime(selfdata['start_date'], DEFAULT_SERVER_DATE_FORMAT).date()
                en_date = datetime.strptime(selfdata['end_date'], DEFAULT_SERVER_DATE_FORMAT).date()
                diff = relativedelta.relativedelta(en_date, st_date)
                if st_date == en_date or st_date > en_date:
                    raise Warning(_('Selected dates are not according to 12 month format'))
                if diff and diff.days and diff.days > 0:
                    raise Warning(_('Selected dates are not according to 12 month format'))
                if diff and diff.months and diff.months > 0:
                    raise Warning(_('Selected dates are not according to 12 month format'))
                if diff and diff.year and diff.year > 0:
                    acc_mon = diff.year
                quat_num = 12
                qtr_dates = {}
                sta_date = st_date
                for quat in range(quat_num):
                    en_date = sta_date + relativedelta.relativedelta(months = 1,days = -1)
                    qtr_dates.update({'qtr' + str(quat + 1):{'date_from':sta_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                              'date_to':en_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                              }
                                      })
                    sta_date = en_date + relativedelta.relativedelta(days = 1)
                data['form'].update({'qtr_dates':qtr_dates,'quat_num':quat_num})
        if context and context.get('xls_report'):
            data['form']['xls_report'] = context.get('xls_report')
            return self.print_report_xls(data=data)
#        account_list = self.account_list
        if data['form']['columns'] == 'one':
            name = 'sg_account_report.financial_report_balance_full_temp'
        if data['form']['columns'] == 'two':
            name = 'sg_account_report.financial_report_balance_full_temp'
        if data['form']['columns'] == 'four':
            name = 'sg_account_report.financial_report_balance_full_temp'
        if data['form']['columns'] == 'five':
            name = 'sg_account_report.financial_report_balance_full_temp'
        if data['form']['columns'] == 'qtr':
            name = 'sg_account_report.account_full_qtr_balance_cols'
        if data['form']['columns'] == 'thirteen':
            name = 'sg_account_report.account_full_13_balance_cols'
        return self.env['report'].get_action(self, name, data = data)

    @api.multi
    def print_report_xls(self,data):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        borders = xlwt.Borders()
        borders.top = xlwt.Borders.MEDIUM
        borders.bottom = xlwt.Borders.MEDIUM
        borders.left = xlwt.Borders.MEDIUM
        borders.right = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle() # Create Style
        border_style.borders = borders
        font = xlwt.Font()
        font.bold = True 
        bold = xlwt.easyxf("font: bold on; align: wrap on;")
        bold1 = xlwt.easyxf("font: bold on; align: wrap on, horiz right;")
        bold2 = xlwt.easyxf("align: wrap on, horiz right;")
        header1 = xlwt.easyxf('font: bold on, height 220, color black;align: wrap on , horiz left;')
        header2 = xlwt.easyxf('font: bold on, height 220, color black;align: wrap on , horiz right;')
#        header1 = xlwt.easyxf('pattern: pattern solid, fore_colour white; borders: top double, bottom double, bottom_color black; font: bold on, height 180, color black; align: wrap off')
        style = xlwt.easyxf('align: wrap yes')
        worksheet.col(0).width = 15000
        worksheet.col(1).width = 4000
        worksheet.col(2).width = 4000
        worksheet.col(3).width = 4000
        worksheet.col(4).width = 4000
        worksheet.col(5).width = 4000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 4000
        worksheet.row(0).height = 500
        worksheet.row(1).height = 500
        worksheet.row(2).height = 500
        company_name = self.env['res.users'].browse(uid).company_id.name
        account_balance_inherit_obj = self.env['report.sg_account_report.financial_report_balance_full_temp']
        if data['form']['columns'] in ('one','four','five','two'):
            acc_data = account_balance_inherit_obj.get_account_lines(data['form'])
            worksheet.write(4, 0, "Account Name" , header1)
            if data['form']['columns'] in ('one','four','five'):
                worksheet.write(4, 1, "Balance" , header2)
            if data['form']['columns'] in ('two','four','five'):
                worksheet.write(4, 2, "Debit" , header2)
                worksheet.write(4, 3, "Credit" , bold1)
            if data['form']['columns'] in ('four','five'):
                worksheet.write(4, 4, "YTD" , header2)
            if data['form']['columns'] in ('five'):
                worksheet.write(4, 5, "period" , header2)
            row = 6
            if data['form']['account_report_id'][1] == 'Balance Sheet':
                worksheet.write(0, 1, company_name , header1)
                worksheet.write(1, 1, 'Balance Sheet' , header1)
            elif data['form']['account_report_id'][1] == 'Profit and Loss':
                worksheet.write(0, 1, company_name , header1)
                worksheet.write(1, 1, 'Profit Loss' , header1)
            if acc_data:
                for acc in acc_data:
                    if data['form']['account_report_id'][1] == 'Balance Sheet':
                        if acc['level'] != 0:
                            if acc['level'] <= 3:
                                    worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],bold)
                                    if data['form']['columns'] in ('one','four','five'):
                                        if acc['balance'] != 0:
                                            worksheet.write(row, 1, round(acc['balance'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] in ('two','four','five'):
                                        if acc['debit'] != 0:
                                            worksheet.write(row, 2, round(acc['debit'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                        if acc['credit'] != 0:
                                            worksheet.write(row, 3, round(acc['credit'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] in ('four','five'):
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 4, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] in ('five'):
                                        if acc['period'] != 0:
                                            worksheet.write(row, 5, round(acc['period'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                            else:
                                worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],style)
                                if data['form']['columns'] in ('one','four','five'):
                                    if acc['balance'] != 0:
                                        worksheet.write(row, 1, round(acc['balance'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 1, '0.00',bold2)
                                if data['form']['columns'] in ('two','four','five'):
                                    if acc['debit'] != 0:
                                        worksheet.write(row, 2, round(acc['debit'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 2, '0.00',bold2)
                                    if acc['credit'] != 0:
                                        worksheet.write(row, 3, round(acc['credit'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 3, '0.00',bold2)
                                if data['form']['columns'] in ('four','five'):
                                    if acc['ytd'] != 0:
                                        worksheet.write(row, 4, round(acc['ytd'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 4, '0.00',bold2)
                                if data['form']['columns'] in ('five'):
                                    if acc['period'] != 0:
                                        worksheet.write(row, 5, round(acc['period'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 5, '0.00',bold2)
                            row += 1
                    if data['form']['account_report_id'][1] == 'Profit and Loss':
                        if acc['level'] != 0:
                            if acc['level'] <= 3:
                                    worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],bold)
                                    if data['form']['columns'] in ('one','four','five'):
                                        if acc['balance'] != 0:
                                            worksheet.write(row, 1, round(acc['balance'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] in ('two','four','five'):
                                        if acc['debit'] != 0:
                                            worksheet.write(row, 2, round(acc['debit'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                        if acc['credit'] != 0:
                                            worksheet.write(row, 3, round(acc['credit'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] in ('four','five'):
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 4, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] in ('five'):
                                        if acc['period'] != 0:
                                            worksheet.write(row, 5, round(acc['period'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                            else:
                                worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],style)
                                if data['form']['columns'] in ('one','four','five'):
                                    if acc['balance'] != 0:
                                        worksheet.write(row, 1, round(acc['balance'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 1, '0.00',bold2)
                                if data['form']['columns'] in ('two','four','five'):
                                    if acc['debit'] != 0:
                                        worksheet.write(row, 2, round(acc['debit'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 2, '0.00',bold2)
                                    if acc['credit'] != 0:
                                        worksheet.write(row, 3, round(acc['credit'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 3, '0.00',bold2)
                                if data['form']['columns'] in ('four','five'):
                                    if acc['ytd'] != 0:
                                        worksheet.write(row, 4, round(acc['ytd'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 4, '0.00',bold2)
                                if data['form']['columns'] in ('five'):
                                    if acc['period'] != 0:
                                        worksheet.write(row, 5, round(acc['period'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 5, '0.00',bold2)
                            row += 1
        if data['form']['columns'] == 'qtr':
            account_balance_qtr_obj = self.env['report.sg_account_report.account_full_qtr_balance_cols']
            acc_data = account_balance_qtr_obj.get_account_lines_qtr(data['form'])
            worksheet.write(4, 0, "Account Name" , header1)
            worksheet.write(4, 1, "Q1" , header2)
            worksheet.write(4, 2, "Q2" , header2)
            worksheet.write(4, 3, "Q3" , bold1)
            worksheet.write(4, 4, "Q4" , header2)
            worksheet.write(4, 5, "YTD" , header2)
            if data['form']['account_report_id'][1] == 'Balance Sheet':
                worksheet.write(0, 1, company_name , header1)
                worksheet.write(1, 1, 'Balance Sheet' , header1)
            elif data['form']['account_report_id'][1] == 'Profit and Loss':
                worksheet.write(0, 1, company_name , header1)
                worksheet.write(1, 1, 'Profit Loss' , header1)
            row = 6
            if acc_data:
                for acc in acc_data:
                    if data['form']['account_report_id'][1] == 'Balance Sheet':
                        if acc['level'] != 0:
                            if acc['level'] <= 3:
                                    worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],bold)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance1'] != 0:
                                            worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance2'] != 0:
                                            worksheet.write(row, 2, round(acc['balance2'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance3'] != 0:
                                            worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance4'] != 0:
                                            worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 5, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                            else:
                                worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],style)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance1'] != 0:
                                        worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 1, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance2'] != 0:
                                        worksheet.write(row, 2, round(acc['balance2'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 2, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance3'] != 0:
                                        worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 3, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance4'] != 0:
                                        worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 4, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['ytd'] != 0:
                                        worksheet.write(row, 5, round(acc['ytd'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 5, '0.00',bold2)
                            row += 1
                    if data['form']['account_report_id'][1] == 'Profit and Loss':
                        if acc['level'] != 0:
                            if acc['level'] <= 3:
                                    worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],bold)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance1'] != 0:
                                            worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance2'] != 0:
                                            worksheet.write(row, 2, round(acc['balance2'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance3'] != 0:
                                            worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['balance4'] != 0:
                                            worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] == 'qtr':
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 5, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                            else:
                                worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],style)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance1'] != 0:
                                        worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 1, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance2'] != 0:
                                        worksheet.write(row, 2, round(acc['balance2'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 2, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance3'] != 0:
                                        worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 3, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['balance4'] != 0:
                                        worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 4, '0.00',bold2)
                                if data['form']['columns'] == 'qtr':
                                    if acc['ytd'] != 0:
                                        worksheet.write(row, 5, round(acc['ytd'] or 0.00 , 2),style)
                                    else:
                                        worksheet.write(row, 5, '0.00',bold2)
                            row += 1
        if data['form']['columns'] == 'thirteen':
            account_balance_twlv_obj = self.env['report.sg_account_report.account_full_13_balance_cols']
            acc_data = account_balance_twlv_obj.get_account_lines_twelve_month(data['form'])
            worksheet.write(4, 0, "Account Name" , header1)
            worksheet.write(4, 1, "01" , header2)
            worksheet.write(4, 2, "02" , header2)
            worksheet.write(4, 3, "03" , bold1)
            worksheet.write(4, 4, "04" , header2)
            worksheet.write(4, 5, "05" , header2)
            worksheet.write(4, 6, "06" , header2)
            worksheet.write(4, 7, "07" , header2)
            worksheet.write(4, 8, "08" , header2)
            worksheet.write(4, 9, "09" , header2)
            worksheet.write(4, 10, "10" , header2)
            worksheet.write(4, 11, "11" , header2)
            worksheet.write(4, 12, "12" , header2)
            worksheet.write(4, 13, "YTD" , header2)
            if data['form']['account_report_id'][1] == 'Balance Sheet':
                worksheet.write(0, 1, company_name , header1)
                worksheet.write(1, 1, 'Balance Sheet' , header1)
            elif data['form']['account_report_id'][1] == 'Profit and Loss':
                worksheet.write(0, 1, company_name , header1)
                worksheet.write(1, 1, 'Profit Loss' , header1)
            row = 6
            if acc_data:
                for acc in acc_data:
                    if data['form']['account_report_id'][1] == 'Balance Sheet':
                        if acc['level'] != 0:
                            if acc['level'] <= 3:
                                    worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],bold)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance1'] != 0:
                                            worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance2'] != 0:
                                            worksheet.write(row, 2, round(acc['balance2'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance3'] != 0:
                                            worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance4'] != 0:
                                            worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance5'] != 0:
                                            worksheet.write(row, 5, round(acc['balance5'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance6'] != 0:
                                            worksheet.write(row, 6, round(acc['balance6'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 6, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance7'] != 0:
                                            worksheet.write(row, 7, round(acc['balance7'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 7, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance8'] != 0:
                                            worksheet.write(row, 8, round(acc['balance8'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 8, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance9'] != 0:
                                            worksheet.write(row, 9, round(acc['balance9'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 9, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance10'] != 0:
                                            worksheet.write(row, 10, round(acc['balance10'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 10, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance11'] != 0:
                                            worksheet.write(row, 11, round(acc['balance11'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 11, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance12'] != 0:
                                            worksheet.write(row, 12, round(acc['balance12'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 12, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 13, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 13, '0.00',bold1)
                            else:
                                worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],style)
                                if data['form']['columns'] == 'thirteen':
                                    if acc['balance1'] != 0:
                                        worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),bold)
                                    else:
                                        worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance2'] != 0:
                                            worksheet.write(row, 2, round(acc['balance2'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance3'] != 0:
                                            worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance4'] != 0:
                                            worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance5'] != 0:
                                            worksheet.write(row, 5, round(acc['balance5'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance6'] != 0:
                                            worksheet.write(row, 6, round(acc['balance6'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 6, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance7'] != 0:
                                            worksheet.write(row, 7, round(acc['balance7'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 7, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance8'] != 0:
                                            worksheet.write(row, 8, round(acc['balance8'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 8, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance9'] != 0:
                                            worksheet.write(row, 9, round(acc['balance9'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 9, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance10'] != 0:
                                            worksheet.write(row, 10, round(acc['balance10'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 10, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance11'] != 0:
                                            worksheet.write(row, 11, round(acc['balance11'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 11, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance12'] != 0:
                                            worksheet.write(row, 12, round(acc['balance12'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 12, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 13, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 13, '0.00',bold1)
                            row += 1
                    if data['form']['account_report_id'][1] == 'Profit and Loss':
                        if acc['level'] != 0:
                            if acc['level'] <= 3:
                                    worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],bold)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance1'] != 0:
                                            worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance2'] != 0:
                                            worksheet.write(row, 2, round(acc['balance2'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance3'] != 0:
                                            worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance4'] != 0:
                                            worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance5'] != 0:
                                            worksheet.write(row, 5, round(acc['balance5'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance6'] != 0:
                                            worksheet.write(row, 6, round(acc['balance6'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 6, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance7'] != 0:
                                            worksheet.write(row, 7, round(acc['balance7'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 7, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance8'] != 0:
                                            worksheet.write(row, 8, round(acc['balance8'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 8, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance9'] != 0:
                                            worksheet.write(row, 9, round(acc['balance9'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 9, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance10'] != 0:
                                            worksheet.write(row, 10, round(acc['balance10'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 10, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance11'] != 0:
                                            worksheet.write(row, 11, round(acc['balance11'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 11, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance12'] != 0:
                                            worksheet.write(row, 12, round(acc['balance12'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 12, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 13, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 13, '0.00',bold1)
                            else:
                                worksheet.write(row, 0,'    '*(acc['level']-1) + acc['name'],style)
                                if data['form']['columns'] == 'thirteen':
                                    if acc['balance1'] != 0:
                                        worksheet.write(row, 1, round(acc['balance1'] or 0.00 , 2),bold)
                                    else:
                                        worksheet.write(row, 1, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance2'] != 0:
                                            worksheet.write(row, 2, round(acc['balance2'], 2),bold)
                                        else:
                                            worksheet.write(row, 2, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance3'] != 0:
                                            worksheet.write(row, 3, round(acc['balance3'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 3, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance4'] != 0:
                                            worksheet.write(row, 4, round(acc['balance4'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 4, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance5'] != 0:
                                            worksheet.write(row, 5, round(acc['balance5'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 5, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance6'] != 0:
                                            worksheet.write(row, 6, round(acc['balance6'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 6, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance7'] != 0:
                                            worksheet.write(row, 7, round(acc['balance7'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 7, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance8'] != 0:
                                            worksheet.write(row, 8, round(acc['balance8'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 8, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance9'] != 0:
                                            worksheet.write(row, 9, round(acc['balance9'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 9, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance10'] != 0:
                                            worksheet.write(row, 10, round(acc['balance10'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 10, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance11'] != 0:
                                            worksheet.write(row, 11, round(acc['balance11'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 11, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['balance12'] != 0:
                                            worksheet.write(row, 12, round(acc['balance12'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 12, '0.00',bold1)
                                    if data['form']['columns'] == 'thirteen':
                                        if acc['ytd'] != 0:
                                            worksheet.write(row, 13, round(acc['ytd'] or 0.00 , 2),bold)
                                        else:
                                            worksheet.write(row, 13, '0.00',bold1)
                            row += 1

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data1 = fp.read()
        fp.close()
        file_res =  base64.b64encode(data1)
        bs_pl_xls_rec = self.env['bs.pl.xls.report'].create({'file':file_res, 'name':'BS PL.xls'})
        return {
          'name': _('Financial Xls Reports'),
          'res_id': bs_pl_xls_rec.id,
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'bs.pl.xls.report',
          'type': 'ir.actions.act_window',
          'target': 'new',
          'context': context,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
