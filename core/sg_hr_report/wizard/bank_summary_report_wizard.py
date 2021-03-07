# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
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
import xlwt
import locale
import base64
import datetime
from odoo import tools
from cStringIO import StringIO
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class excel_export_summary(models.TransientModel):
    _name = "excel.export.summary"

    file = fields.Binary("Click On Download Link To Download Xls File", readonly = True)
    name = fields.Char("Name",default = 'Bank_summary.xls')


class view_bank_summary_report_wizard(models.TransientModel):
    _name = 'view.bank.summary.report.wizard'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_bank_rel_tbl', 'rel_bank_id', 'rel_employee_id', 'Employee Name')
    start_date = fields.Date('Start Date', default = lambda *a: time.strftime('%Y-%m-01'))
    end_date = fields.Date('End Date', default = lambda *a: str(datetime.datetime.now() + relativedelta.relativedelta(months = +1, day = 1, days = -1))[:10])
    export_report = fields.Selection([('pdf', 'PDF'), ('excel', 'Excel')] , "Export", default = 'pdf')

    @api.multi
    def print_bank_summary_report(self):
        '''
            The method used to call download of wizard action called or
            Bank Summery Report of Template called If selected PDF or Excel
            Type of Report.
            @self : Record Set
            @api.multi : The decorator of multi
            @return : The return wizard of action in dictionary
            ---------------------------------------------------------------- 
        '''
        bank_emp_rec = self.read([])
        employee_obj = self.env['hr.employee']
        cr, uid, context = self.env.args
        bank_obj = self.env['hr.bank.details']
        payslip_obj = self.env['hr.payslip']
        context = dict(context)
        data = {}
        if bank_emp_rec:
            data = bank_emp_rec[0]
        start_date = data.get('start_date', False)
        end_date = data.get('end_date', False)
        emp_ids = data.get('employee_ids', False) or []
        if start_date >= end_date:
            raise ValidationError(_("You must be enter start date less than end date !"))
        for employee in employee_obj.browse(emp_ids):
            if not employee.bank_account_id:
                raise ValidationError(_('There is no Bank Account define for %s employee.' % (employee.name)))
#            if not employee.gender:
#                raise ValidationError(_('There is no gender define for %s employee.' % (employee.name)))
#            if not employee.birthday:
#                raise ValidationError(_('There is no birth date define for %s employee.' % (employee.name)))
#            if not employee.identification_id:
#                raise ValidationError(_('There is no identification no define for %s employee.' % (employee.name)))
#            if not employee.work_phone or not employee.work_email:
#                raise ValidationError(_('You must be configure Contact no or email for %s employee.' % (employee.name)))
        payslip_ids = self.env['hr.payslip'].search([('employee_id', 'in', emp_ids),
                                                     ('date_from', '>=', start_date),
                                                     ('date_from', '<=', end_date),
                                                     ('pay_by_cheque', '=', False),
                                                     ('state', 'in', ['draft', 'done', 'verify'])])

        if not payslip_ids.ids:
            raise ValidationError(_('There is no payslip details available for bank between selected date %s and %s') % (start_date, end_date))
        res_user = self.env['res.users'].browse(uid)
        if data.get("export_report", False) == "pdf":
            data.update({'currency': " " + tools.ustr(res_user.company_id.currency_id.symbol), 'company': res_user.company_id.name})
            for employee in employee_obj.browse(data.get('employee_ids')):
                if not employee.bank_account_id:
                    raise Warning(_('There is no Bank Account Number define for %s.' % (employee.name)))

            datas = {
                'ids': [],
                'form': data,
                'model':'hr.payslip',
                'date_from':start_date,
                'date_to':end_date
            }
            return self.env['report'].get_action(self, 'sg_hr_report.hr_bank_summary_report_tmp', data = datas)
        else:
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('Sheet 1')
            font = xlwt.Font()
            font.bold = True
            header = xlwt.easyxf('font: bold 1, height 280')
            start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            start_date_formate = start_date.strftime('%d/%m/%Y')
            end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
            end_date_formate = end_date.strftime('%d/%m/%Y')
            start_date_to_end_date = tools.ustr(start_date_formate) + ' To ' + tools.ustr(end_date_formate)
            style = xlwt.easyxf('align: wrap yes')
            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.row(0).height = 500
            worksheet.row(1).height = 500
            worksheet.write(0, 0, "Company Name" , header)
            worksheet.write(0, 1, res_user.company_id.name, header)
            worksheet.write(0, 7, "By Bank", header)
            worksheet.write(1, 0, "Period", header)
            worksheet.write(1, 1, start_date_to_end_date, header)
            worksheet.col(9).width = 5000
            worksheet.col(11).width = 5000
            borders = xlwt.Borders()
            borders.top = xlwt.Borders.MEDIUM
            borders.bottom = xlwt.Borders.MEDIUM
            alignment = xlwt.Alignment()
            alignment.horz = xlwt.Alignment.HORZ_CENTER  # May be: HORZ_GENERAL, HORZ_LEFT, HORZ_CENTER, HORZ_RIGHT, HORZ_FILLED, HORZ_JUSTIFIED, HORZ_CENTER_ACROSS_SEL, HORZ_DISTRIBUTED
            alignment.vert = xlwt.Alignment.VERT_CENTER
            border_style = xlwt.XFStyle()  # Create Style
            border_style.alignment = alignment
            border_style.borders = borders
            row = 2
            employee_ids = employee_obj.search([('bank_account_id', '!=', False),
                                                ('id', 'in', emp_ids),
                                                ('department_id', '!=', False)])
            new_employee_ids = []
            new_emp_rec = []
            style = xlwt.easyxf('align: wrap yes')
            if employee_ids and employee_ids.ids:
                payslip_ids = payslip_obj.search([('date_from', '>=', start_date),
                                                  ('date_from', '<=', end_date),
                                                  ('employee_id', 'in' , employee_ids.ids),
                                                  ('pay_by_cheque', '=', False),
                                                  ('state', 'in', ['draft', 'done', 'verify'])])
                if payslip_ids and payslip_ids.ids:
                    bank_ids = bank_obj.search([('bank_emp_id', 'in', employee_ids.ids)], order = "bank_name, bank_code, branch_code")
                    for bank in bank_ids:
                        if bank.bank_emp_id.id not in new_employee_ids:
                            new_employee_ids.append(bank.bank_emp_id.id)

                    new_emp_rec += list(set(employee_ids.ids).difference(set(new_employee_ids)))
                    if new_emp_rec:
                        new_emp_rec = new_employee_ids

                    row = 4
                    worksheet.write(4, 0, "", border_style)
                    worksheet.write(4, 1, "Employee Name" , border_style)
                    worksheet.write(4, 2, "", border_style)
                    worksheet.write(4, 3, "Employee Login"  , border_style)
                    worksheet.write(4, 4, "", border_style)
                    worksheet.write(4, 5, "Amount" , border_style)
                    worksheet.write(4, 6, "", border_style)
                    worksheet.write(4, 7, "Name Of Bank", border_style)
                    worksheet.write(4, 8, "", border_style)
                    worksheet.write(4, 9, "Bank Code", border_style)
                    worksheet.write(4, 10, "", border_style)
                    worksheet.write(4, 11, "Account Number", border_style)
                    worksheet.write(4, 12, "", border_style)
                    worksheet.write(4, 13, "Branch Code", border_style)
                    row += 1
            hr_department_brw = self.env['hr.department'].search([])
            result = {}
            payslip_data = {}
            department_total_amount = 0.0
            for employee in employee_obj.browse(new_emp_rec):
                payslip_ids = payslip_obj.search([('date_from', '>=', start_date),
                                                  ('date_from', '<=', end_date),
                                                  ('employee_id', '=' , employee.id),
                                                  ('pay_by_cheque', '=', False),
                                                  ('state', 'in', ['draft', 'done', 'verify'])])
                net = 0.00
                for payslip in payslip_ids:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total



                net_total = '%.2f' % net
                worksheet.write(row, 1, employee.name)
                worksheet.write(row, 2, "")
                worksheet.write(row, 3, employee and employee.user_id and employee.user_id.login or '')
                worksheet.write(row, 4, "")
                worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(net_total), grouping = True)))
                worksheet.write(row, 6, "")
                worksheet.write(row, 7, employee.bank_account_id and employee.bank_account_id.bank_name or '')
                worksheet.write(row, 8, "")
                worksheet.write(row, 9, employee.bank_account_id and employee.bank_account_id.bank_id and employee.bank_account_id.bank_id.bic or '')
                worksheet.write(row, 10, "")
                worksheet.write(row, 11, employee.bank_account_id and employee.bank_account_id.acc_number or '')
                worksheet.write(row, 12, "")
                worksheet.write(row, 13, employee.bank_account_id and employee.bank_account_id.branch_id or '')
    #            worksheet.write(row, 13, res_user.company_id.currency_id.symbol + ' '+ tools.ustr(net_total))
                row += 1
                department_total_amount += net
                if 'Undefined' in result:
                    result.get('Undefined').append(payslip_data)
                else:
                    result.update({'Undefined': [payslip_data]})
            if department_total_amount:
                worksheet.write(row, 0, 'Total Undefined', border_style)
                worksheet.write(row, 1, '', border_style)
                worksheet.write(row, 2, '', border_style)
                worksheet.write(row, 3, '', border_style)
                worksheet.write(row, 4, '', border_style)
                new_department_total_amount = '%.2f' % department_total_amount
                worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_department_total_amount), grouping = True)) , border_style)
                worksheet.write(row, 6, '', border_style)
                worksheet.write(row, 7, '', border_style)
                worksheet.write(row, 8, '', border_style)
                worksheet.write(row, 9, '', border_style)
                worksheet.write(row, 10, '', border_style)
                worksheet.write(row, 11, '', border_style)
                worksheet.write(row, 12, '', border_style)
                worksheet.write(row, 13, '', border_style)
                row += 1
            new_department_total_amount1 = '%.2f' % department_total_amount
            department_total = {'total': new_department_total_amount1, 'department_name': 'Total Undefined'}
            department_info = {'Undefined': [department_total]}

            for hr_department in hr_department_brw:
                employee_ids = employee_obj.search([('bank_account_id', '!=', False),
                                                    ('id', 'in', emp_ids),
                                                    ('department_id', '=', hr_department.id)])
                new_employee_ids = []
                new_employee_rec = []
                employee_ids = employee_ids.ids
                bank_ids = bank_obj.search([('bank_emp_id', 'in', employee_ids)], order = "bank_name, bank_code, branch_code")
                for bank in bank_ids:
                    if bank.bank_emp_id.id not in new_employee_ids:
                        new_employee_ids.append(bank.bank_emp_id.id)
                new_employee_rec += list(set(employee_ids).difference(set(new_employee_ids)))
                department_total_amount = 0.0
                flag = False
                print_header = True
                for employee in employee_obj.browse(new_employee_rec):
                    payslip_ids = payslip_obj.search([('date_from', '>=', start_date),
                                                      ('date_from', '<=', end_date),
                                                      ('employee_id', '=' , employee.id),
                                                      ('pay_by_cheque', '=', False),
                                                      ('state', 'in', ['draft', 'done', 'verify'])])
                    net = 0.0
                    for payslip in payslip_ids:
                        flag = True
                        for line in payslip.line_ids:
                            if line.code == 'NET':
                                net += line.total
                    if print_header and payslip_ids:
                        row += 2
                        print_header = False
                        worksheet.write(row, 0, "", border_style)
                        worksheet.write(row, 1, "Employee Name" , border_style)
                        worksheet.write(row, 2, "", border_style)
                        worksheet.write(row, 3, "Employee Login"  , border_style)
                        worksheet.write(row, 4, "", border_style)
                        worksheet.write(row, 5, "Amount" , border_style)
                        worksheet.write(row, 6, "", border_style)
                        worksheet.write(row, 7, "Name Of Bank", border_style)
                        worksheet.write(row, 8, "", border_style)
                        worksheet.write(row, 9, "Bank Code", border_style)
                        worksheet.write(row, 10, "", border_style)
                        worksheet.write(row, 11, "Account Number", border_style)
                        worksheet.write(row, 12, "", border_style)
                        worksheet.write(row, 13, "Branch Code", border_style)
                        row += 1
                    new_net = '%.2f' % net
                    worksheet.write(row, 1, employee.name or '')
                    worksheet.write(row, 2, "")
                    worksheet.write(row, 3, employee and employee.user_id and employee.user_id.login or '')
                    worksheet.write(row, 4, "")
                    worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_net), grouping = True)))
                    worksheet.write(row, 6, "")
                    worksheet.write(row, 7, employee.bank_account_id and employee.bank_account_id.bank_name or '')
                    worksheet.write(row, 8, "")
                    worksheet.write(row, 9, employee.bank_account_id and employee.bank_account_id.bank_id and employee.bank_account_id.bank_id.bic or '')
                    worksheet.write(row, 10, "")
                    worksheet.write(row, 11, employee.bank_account_id and employee.bank_account_id.acc_number or '')
                    worksheet.write(row, 12, "")
                    worksheet.write(row, 13, employee.bank_account_id and employee.bank_account_id.branch_id or '')
                    row += 1
                    department_total_amount += net
                    if hr_department.id in result:
                        result.get(hr_department.id).append(payslip_data)
                    else:
                        result.update({hr_department.id: [payslip_data]})
                if flag:
                    worksheet.write(row, 0, tools.ustr('Total ' + hr_department.name), border_style)
                    worksheet.write(row, 1, '', border_style)
                    worksheet.write(row, 2, '', border_style)
                    worksheet.write(row, 3, '', border_style)
                    worksheet.write(row, 4, '', border_style)
                    new_department_total_amount = '%.2f' % department_total_amount
                    worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_department_total_amount), grouping = True)), border_style)
                    worksheet.write(row, 6, '', border_style)
                    worksheet.write(row, 7, '', border_style)
                    worksheet.write(row, 8, '', border_style)
                    worksheet.write(row, 9, '', border_style)
                    worksheet.write(row, 10, '', border_style)
                    worksheet.write(row, 11, '', border_style)
                    worksheet.write(row, 12, '', border_style)
                    worksheet.write(row, 13, '', border_style)
                    row += 1
                new_department_total_amount1 = '%.2f' % department_total_amount
                department_total = {'total': new_department_total_amount1, 'department_name': "Total " + hr_department.name}
                if hr_department.id in department_info:
                    department_info.get(hr_department.id).append(department_total)
                else:
                    department_info.update({hr_department.id: [department_total]})

            row += 1
            worksheet.write(row, 0, "Overall Total", border_style)
            worksheet.write(row, 1, '', border_style)
            worksheet.write(row, 2, '', border_style)
            row += 2
            for key, val in result.items():
                worksheet.write(row, 0, department_info[key][0].get("department_name"))
                worksheet.write(row, 2, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(department_info[key][0].get("total")), grouping = True)))
                row += 1
            row += 1
            total_ammount = 0
            total_employee_ids = employee_obj.search([('bank_account_id', '!=', False),
                                                      ('id', 'in', emp_ids)])
            payslip_ids = payslip_obj.search([('date_from', '>=', start_date),
                                              ('date_from', '<=', end_date),
                                              ('employee_id', 'in' , total_employee_ids.ids),
                                              ('pay_by_cheque', '=', False),
                                              ('state', 'in', ['draft', 'done', 'verify'])])
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code == 'NET':
                        total_ammount += line.total
            new_total_ammount = '%.2f' % total_ammount
            worksheet.write(row, 0, "All")
            worksheet.write(row, 2, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_total_ammount), grouping = True)))
            fp = StringIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            res = base64.b64encode(data)
            module_rec = self.env['excel.export.summary'].create({'name':'Bank_summary.xls', 'file' : res})
            return {
              'name': _('Bank Summary Report'),
              'res_id' : module_rec.id,
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'excel.export.summary',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': context,
              }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
