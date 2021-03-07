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
import xlwt
import time
import locale
import base64
import datetime
from odoo import tools
from cStringIO import StringIO
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class excel_export_cheque_summary(models.TransientModel):
    _name = "excel.export.cheque.summary"

    file = fields.Binary("Click On Download Link To Download Xls File", readonly = True)
    name = fields.Char("Name" , size = 32, default = 'Cheque_summary.xls')


class view_cheque_summary_report_wizard(models.TransientModel):
    _name = 'view.cheque.summary.report.wizard'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_cheque_rel', 'emp_id', 'employee_id', 'Employee Name', required = False)
    export_report = fields.Selection([('pdf', 'PDF'), ('excel', 'Excel')] , "Export", default = 'pdf')
    date_start = fields.Date('Date Start', default = lambda *a: time.strftime('%Y-%m-01'))
    date_stop = fields.Date('Date Stop', default = lambda *a: str(datetime.datetime.now() + relativedelta.relativedelta(months = +1, day = 1, days = -1))[:10])

    @api.multi
    def print_cheque_summary_report(self):
        '''
            The method used to call download of wizard action called or
            Cheque Summery Report of Template called If selected PDF or Excel
            Type of Report.
            @self : Record Set
            @api.multi : The decorator of multi
            @return : The return wizard of action in dictionary
            ---------------------------------------------------------------- 
        '''
        cheque_data = self.read([])[0]
        cr, uid, context = self.env.args
        context = dict(context)
        data = {}
        payslip_ids = []
        if cheque_data:
            data = cheque_data
        start_date = data.get('date_start', False)
        end_date = data.get('date_stop', False)
        emp_ids = data.get('employee_ids', False)
        employee_obj = self.env['hr.employee']
        payslip_obj = self.env['hr.payslip']
        if start_date >= end_date:
            raise ValidationError(_("You must be enter start date less than end date !"))
        for employee in employee_obj.browse(emp_ids):
            domain = []
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
            domain.append(('date_from', '>=', start_date))
            domain.append(('date_from', '<=', end_date))
            domain.append(('employee_id', '=' , employee.id))
            domain.append(('state', 'in', ['draft', 'done', 'verify']))
            if employee.bank_account_id:
                domain.append(('pay_by_cheque', '=', True))
            payslip_rec = payslip_obj.search(domain)
            if payslip_rec and payslip_rec.ids:
                payslip_ids.append(payslip_rec.ids)
        if not payslip_ids:
            raise ValidationError(_('There is no cheque number of payslip available between selected date %s and %s!' % (start_date, end_date)))
        if data.get("export_report") == "pdf":
            res_user = self.env["res.users"].browse(uid)
            data.update({'currency': " " + tools.ustr(res_user.company_id.currency_id.symbol), 'company': res_user.company_id.name})
            datas = {
                'ids': [],
                'form': data,
                'model':'hr.payslip',
                'date_from':start_date,
                'date_to':end_date
            }
            return self.env['report'].get_action(self, 'sg_hr_report.cheque_summary_report_tmp', data = datas)
        else:
            employee_lst_ids = data['employee_ids'] or False
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('Sheet 1')
            font = xlwt.Font()
            font.bold = True
            header = xlwt.easyxf('font: bold 1, height 240;')
            res_user = self.env['res.users'].browse(uid)
            start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            start_date_formate = start_date.strftime('%d/%m/%Y')
            end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
            end_date_formate = end_date.strftime('%d/%m/%Y')
            start_date_to_end_date = tools.ustr(start_date_formate) + ' to ' + tools.ustr(end_date_formate)
            borders = xlwt.Borders()
            borders.top = xlwt.Borders.MEDIUM
            borders.bottom = xlwt.Borders.MEDIUM
            alignment = xlwt.Alignment()
            alignment.horz = xlwt.Alignment.HORZ_CENTER  # May be: HORZ_GENERAL, HORZ_LEFT, HORZ_CENTER, HORZ_RIGHT, HORZ_FILLED, HORZ_JUSTIFIED, HORZ_CENTER_ACROSS_SEL, HORZ_DISTRIBUTED
            alignment.vert = xlwt.Alignment.VERT_CENTER
            border_style = xlwt.XFStyle()  # Create Style
            border_style.alignment = alignment
            border_style.borders = borders
            alignment_style = xlwt.XFStyle()  # Create Style
            alignment_style.alignment = alignment
            flag = False
    
            style = xlwt.easyxf('align: wrap yes')
            header_brdr = xlwt.easyxf('font: bold on;align: wrap off , vert center, horiz left; borders : bottom_color black, top_color black,top medium, bottom medium')
            brdr_center = xlwt.easyxf('font: bold on;align: wrap off , vert center, horiz center; borders : bottom_color black, top_color black,top medium, bottom medium')
            right = xlwt.easyxf('font: bold on;align: wrap off , vert center, horiz right;')
            brder_right = xlwt.easyxf('font: bold on;align: wrap off , vert center, horiz right;borders : bottom_color black, top_color black,top medium, bottom medium')
            
            worksheet.col(0).width = 7000
            worksheet.col(1).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(5).width = 5000
            worksheet.col(7).width = 5000
            worksheet.row(0).height = 500
            worksheet.row(1).height = 500
            worksheet.write(0, 0, "Company Name" , header)
            worksheet.write(0, 1, res_user.company_id.name, header)
            worksheet.write(0, 7, "By Cheque", header)
            worksheet.write(1, 0, "Period", header)
            worksheet.write(1, 1, start_date_to_end_date, header)
            hr_department_brw = self.env['hr.department'].search([])
            result = {}
            payslip_data = {}
            department_info = {}
            employee_ids = employee_obj.search([('id', 'in', employee_lst_ids),
                                                ('department_id', '=', False)])
            row = 2
#            here employee record browse and search employee of payslip on payslip object 
            if employee_ids and employee_ids.ids:
                for emp in employee_ids:
                    if emp.bank_account_id:
                        payslip_id = payslip_obj.search([('date_from', '>=', start_date),
                                                          ('date_from', '<=', end_date),
                                                          ('employee_id', '=' , emp.id),
                                                          ('pay_by_cheque', '=', True),
                                                          ('state', 'in', ['draft', 'done', 'verify'])])
#                Here name of column written in the excel file
                if payslip_id:
                    worksheet.write(2, 0, "", border_style)
                    worksheet.write(2, 1, "Employee Name" , border_style)
                    worksheet.write(2, 2, "", border_style)
                    worksheet.write(2, 3, "Employee Login", border_style)
                    worksheet.write(2, 4, "", border_style)
                    worksheet.write(2, 5, "Amount", border_style)
                    worksheet.write(2, 6, "", border_style)
                    worksheet.write(2, 7, "Cheque Number", border_style)
                    row += 1
            department_total_amount = 0.0
            for employee in employee_ids:
                if employee.bank_account_id:
                    payslip_id = payslip_obj.search([('date_from', '>=', start_date),
                                                     ('date_from', '<=', end_date),
                                                     ('employee_id', '=' , employee.id),
                                                     ('pay_by_cheque', '=', True),
                                                     ('state', 'in', ['draft', 'done', 'verify'])])
                net = 0.0
                flag = False
                cheque_number = ''
                for payslip in payslip_id:
                    line_net = 0.0
                    cheque_number = payslip.cheque_number
                    if not payslip.employee_id.department_id.id:
                        flag = True
                        for line in payslip.line_ids:
                            if line.code == 'NET':
                                line_net += line.total
#                   here search data written of employee in xls file
                    worksheet.write(row, 0, "")
                    worksheet.write(row, 1, employee.name or '', alignment_style)
                    worksheet.write(row, 2, "")
                    worksheet.write(row, 3, employee.user_id and employee.user_id.login or '', alignment_style)
                    worksheet.write(row, 4, "")
                    net_total = '%.2f' % line_net
                    worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(net_total), grouping = True)), right)
                    worksheet.write(row, 6, "")
                    worksheet.write(row, 7, cheque_number or '', alignment_style)
                    row += 1
                    department_total_amount += line_net
                    if 'Undefined' in result:
                        result.get('Undefined').append(payslip_data)
                    else:
                        result.update({'Undefined': [payslip_data]})
            if flag:
                worksheet.write(row, 0, 'Total Undefined', header_brdr)
                worksheet.write(row, 1, '', border_style)
                worksheet.write(row, 2, '', border_style)
                worksheet.write(row, 3, '', border_style)
                worksheet.write(row, 4, '', border_style)
                new_department_total_amount = '%.2f' % department_total_amount
                worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_department_total_amount), grouping = True)), brder_right)
                worksheet.write(row, 6, '', border_style)
                worksheet.write(row, 7, '', border_style)
                row += 1
            new_department_total_amount1 = '%.2f' % department_total_amount
            department_total = {'total': new_department_total_amount1, 'department_name': "Total Undefined"}
            if 'Undefined' in department_info:
                department_info.get('Undefined').append(department_total)
            else:
                department_info.update({'Undefined': [department_total]})
            for hr_department in hr_department_brw:
                employee_ids = employee_obj.search([('id', 'in', employee_lst_ids),
                                                    ('department_id', '=', hr_department.id)])
                department_total_amount = 0.0
                flag = False
                print_header = True
                for employee in employee_ids:
                    payslip_ids = []
                    if employee.bank_account_id:
                        payslip_id = payslip_obj.search([('date_from', '>=', start_date),
                                                         ('date_from', '<=', end_date),
                                                         ('employee_id', '=' , employee.id),
                                                         ('pay_by_cheque', '=', True),
                                                         ('state', 'in', ['draft', 'done', 'verify'])])
                    net = 0.0
                    cheque_number = ""
                    for payslip in payslip_id:
                        net_total = 0.0
                        cheque_number = payslip.cheque_number
                        flag = True
                        for line in payslip.line_ids:
                            if line.code == 'NET':
                                net_total += line.total
                        if print_header:
                            row += 2
                            print_header = False
                            worksheet.write(row, 0, "", border_style)
                            worksheet.write(row, 1, "Employee Name", border_style)
                            worksheet.write(row, 2, "", border_style)
                            worksheet.write(row, 3, "Employee Login", border_style)
                            worksheet.write(row, 4, "", border_style)
                            worksheet.write(row, 5, "Amount", border_style)
                            worksheet.write(row, 6, "", border_style)
                            worksheet.write(row, 7, "Cheque Number", border_style)
                            row += 1
                        worksheet.write(row, 0, "")
                        worksheet.write(row, 1, employee.name or ' ' , alignment_style)
                        worksheet.write(row, 2, "")
                        worksheet.write(row, 3, employee.user_id and employee.user_id.login or '', alignment_style)
                        worksheet.write(row, 4, "")
                        new_net = '%.2f' % net_total
                        worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_net), grouping = True)), right)
                        worksheet.write(row, 6, "")
                        worksheet.write(row, 7, cheque_number or '', alignment_style)
                        row += 1
                        department_total_amount += net_total
                        if hr_department.id in result:
                            result.get(hr_department.id).append(payslip_data)
                        else:
                            result.update({hr_department.id: [payslip_data]})
                if flag:
                    worksheet.write(row, 0, tools.ustr('Total ' + hr_department.name), header_brdr)
                    worksheet.write(row, 1, '', border_style)
                    worksheet.write(row, 2, '', border_style)
                    worksheet.write(row, 3, '', border_style)
                    worksheet.write(row, 4, '', border_style)
                    new_department_total_amount = '%.2f' % department_total_amount
                    worksheet.write(row, 5, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_department_total_amount), grouping = True)), brder_right)
                    worksheet.write(row, 6, '', border_style)
                    worksheet.write(row, 7, '', border_style)
                    row += 1
                new_department_total_amount1 = '%.2f' % department_total_amount
                department_total = {'total': new_department_total_amount1, 'department_name': "Total " + hr_department.name}
                if hr_department.id in department_info:
                    department_info.get(hr_department.id).append(department_total)
                else:
                    department_info.update({hr_department.id: [department_total]})
            row += 1
            worksheet.write_merge(row, row, 0, 2, "Overall Total", brdr_center)
            row += 2
            for key, val in result.items():
                worksheet.write(row, 0, department_info[key][0].get("department_name"), header_brdr)
                worksheet.write(row, 2, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(department_info[key][0].get("total")), grouping = True)), right)
                row += 1
            row += 1
            final = 0.0
            employee_ids = employee_obj.search([('id', 'in', employee_lst_ids)])
            for employee in employee_ids:
                if employee.bank_account_id:
                    payslip_id = payslip_obj.search([('date_from', '>=', start_date),
                                                      ('date_from', '<=', end_date),
                                                      ('employee_id', '=' , employee.id),
                                                      ('pay_by_cheque', '=', True),
                                                      ('state', 'in', ['draft', 'done', 'verify'])])
                for payslip in payslip_id:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            final += line.total
            new_total_ammount = '%.2f' % final
            worksheet.write(row, 0, "All", header_brdr)
            worksheet.write(row, 1, "", border_style)
            worksheet.write(row, 2, res_user.company_id.currency_id.symbol + ' ' + tools.ustr(locale.format("%.2f", float(new_total_ammount), grouping = True)), brder_right)
            fp = StringIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            res = base64.b64encode(data)
            module_rec = self.env['excel.export.cheque.summary'].create({'name': 'Cheque_summary.xls', 'file' : res})
            return {'name': _('Cheque Summary Report'),
                    'res_id' : module_rec.id,
                    'view_type': 'form',
                    "view_mode": 'form',
                    'res_model': 'excel.export.cheque.summary',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': context}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
