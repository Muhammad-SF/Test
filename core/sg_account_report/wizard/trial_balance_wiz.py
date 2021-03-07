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

import xlwt
import time
import base64
from cStringIO import StringIO
from odoo import fields, models, api, _
from odoo.addons.sg_account_report.report.trial_balance_report import account_trail_balance


class excel_export_trial(models.TransientModel):
    _name = "excel.export.trial"


    file = fields.Binary("Click On Download Link To Download Xls File", readonly=True)
    name = fields.Char("Name" , size=32, default='Export_Trial.xls')

class AccountBalanceReport(models.TransientModel):
    _inherit = 'account.balance.report'
    _description = 'Trial Balance Report'

    @api.multi
    def _print_report(self, data):
        account_data = self.pre_print_report(data)
        account_blnc_data = self.read([])
        balance_dict = {}
        if account_blnc_data:
            balance_dict = account_blnc_data[0]
        account_data['form'].update(balance_dict)
        return self.env['report'].get_action(self, 'sg_account_report.account_trial_balance_temp', data=account_data)

    @api.multi
    def get_trial_data(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        context = dict(context)
        acc_data = self.read([])
        if acc_data:
            acc_data = acc_data[0]
        start_dt = acc_data and acc_data.get('date_from',False) or False
        end_dt = acc_data and acc_data.get('date_to',False) or False
        account_obj = self.env['account.account']
        account_data = account_obj.browse(acc_data.get('chart_account_id',[]))
        fiscalyear_data = account_obj.browse(acc_data.get('fiscalyear_id',[]))
        context.update({'form':acc_data, 'company_name':account_data.company_id.name, 'date_from': start_dt,'date_to': end_dt})
        context = dict(context)
        period_name = context.get('period_id')
        start_date = context.get('date_from',False) or False
        end_date = context.get('date_to',False) or False
        date = 'Start Date %s To End Date %s' %(start_date,end_date)
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        font = xlwt.Font()
        font.bold = True
        header = xlwt.easyxf('font: bold 1, height 280')
        header1 = xlwt.easyxf('pattern: pattern solid, fore_colour white; borders: top double, bottom double, bottom_color black; font: bold on, height 180, color black; align: wrap off')
        style = xlwt.easyxf('font: height 180')
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 5000
        worksheet.col(2).width = 5000
        worksheet.row(0).height = 500
        worksheet.row(1).height = 500
        worksheet.row(2).height = 500
        company_name = self.env['res.users'].browse(uid).company_id.name
        worksheet.write(0, 1, company_name , header)
        worksheet.write(1, 1, date , header)
        worksheet.write(2, 1, "Trial Balance Report" , header)
        worksheet.write(4, 0, "Account" , header1)
        worksheet.write(4, 1, "" , header1)
        worksheet.write(4, 2, "Debit" , header1)
        worksheet.write(4, 3, "Credit" , header1)
        worksheet.write(4, 4, "YTD Debit" , header1)
        worksheet.write(4, 5, "YTD Credit" , header1)
        row = 5

        account_balance_inherit_obj = self.env['report.sg_account_report.account_trial_balance_temp']
        display_account = context['form'].get('display_account')
        accounts = self.env['account.account'].search([])
        account_data = account_balance_inherit_obj.with_context(context)._get_accounts(accounts, display_account)

        tot_deb = tot_cre = tot_ytd_deb = tot_ytd_cre = 0.00
        for acc in account_data:
            worksheet.write(row, 0, acc['name'] , style)
            worksheet.write(row, 2, round(acc['debit'] or 0.00, 2) , style)
            worksheet.write(row, 3, round(acc['credit'] or 0.00, 2) , style)
            worksheet.write(row, 4, round(acc['ytd_debit'] or 0.00, 2) , style)
            worksheet.write(row, 5, round(acc['ytd_credit'] or 0.00, 2) , style)
            tot_deb += acc['debit']
            tot_cre += acc['credit']
            tot_ytd_deb += acc['ytd_debit']
            tot_ytd_cre += acc['ytd_credit']
            row += 1
        row += 2
        worksheet.write(row, 0, 'Total' , header1)
        worksheet.write(row, 1, "" , header1)
        worksheet.write(row, 2, round(tot_deb or 0.00, 2) , header1)
        worksheet.write(row, 3, round(tot_cre or 0.00, 2) , header1)
        worksheet.write(row, 4, round(tot_ytd_deb or 0.00, 2) , header1)
        worksheet.write(row, 5, round(tot_ytd_cre or 0.00, 2) , header1)
        row += 2
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        res = base64.b64encode(data)
        module_rec = self.env['excel.export.trial'].create({'file':res, 'name':'Export_Trial.xls'})

        return {
          'name': 'Trial Balance Report',
          'res_id' : module_rec.id,
          'view_type': 'form',
          'view_mode': 'form',
          'res_model': 'excel.export.trial',
          'type': 'ir.actions.act_window',
          'target': 'new',
          'context': context,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: