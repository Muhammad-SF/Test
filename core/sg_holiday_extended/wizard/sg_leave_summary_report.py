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
import os
import xlwt 
from xlwt import Workbook,easyxf, Pattern
import base64
import time
import math
from datetime import datetime
from cStringIO import StringIO
from odoo import models,fields,api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID
from odoo.report import report_sxw


class sg_leave_export_summary(models.TransientModel):
    
    _name = "excel.sg.leave.summary.report"

    file = fields.Binary("Click On Download Link To Download Xls File", readonly = True)
    name = fields.Char("Name", default = 'generic summary.xls')

sg_leave_export_summary()

class sg_leave_summary_wizard(models.TransientModel):
    _name = 'sg.leave.summary.report.wizard'
    
    @api.multi
    def _curr_employee(self):
        cr, uid, context = self.env.args
        emp_id = context.get('default_employee_id', False)
        if emp_id:
            return emp_id
        ids = self.env['hr.employee'].search([('user_id', '=', uid)])
        if ids:
            return ids[0]
        return False
    
    to_date= fields.Date('Date To')
    from_date= fields.Date('Date From')
    leave_type_id=fields.Many2one('hr.holidays.status', 'Leave Type')
    employee_id=fields.Many2one('hr.employee', 'Name of Employee', default=_curr_employee)
    all_employee=fields.Boolean("All Employee")
    all_leave=fields.Boolean("All Leave")
    
    @api.onchange('all_employee')
    def onchange_all_employee(self):
        vals={}
        if self.all_employee == True:
            vals.update({'employee_id': False})
        return {'value' : vals}
    
    @api.onchange('employee_id')
    def onchange_sg_employee(self):
        """
            When you change employee, this method will change
            value of leave types accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        @param context: A standard dictionary for contextual values
        @return: Dictionary of values.
        """
#        if uid != SUPERUSER_ID and (res_user.has_group(cr, uid, 'base.group_user'):
        result = {}
        result.update({'value': {'leave_type_id':False}})
        employee = self.employee_id
        if employee:
            if employee.leave_config_id and employee.leave_config_id.holiday_group_config_line_ids and employee.leave_config_id.holiday_group_config_line_ids.ids:
                emp_leave_ids=[]
                for leave_type in employee.leave_config_id.holiday_group_config_line_ids:
                    emp_leave_ids.append(leave_type.leave_type_id.id)
                    result.update({'domain':{'leave_type_id':[('id', 'in', emp_leave_ids)]}})
                return result
        else:
            all_leave_ids = self.env['hr.holidays.status'].search([])
            result.update({'domain':{'leave_type_id':[('id', 'in', all_leave_ids.ids)]}})
            return result
        
    def _get_employee_header(self, worksheet, row, table_border):
        """
            this method display employee info header
        """
        worksheet.write(row + 2, 0, 'Department', table_border)
        worksheet.write(row + 2, 1, 'Employee ID', table_border)
        worksheet.write(row + 2, 2, 'Employee Name', table_border)
        worksheet.write(row + 2, 3, 'Date Joined', table_border)
        worksheet.write(row + 2, 4, 'Service Year', table_border)
        worksheet.write(row + 2, 5, 'Leave Structure', table_border)
        worksheet.write(row + 2, 6, 'Carry Forward Leave', table_border)
        worksheet.write(row + 2, 7, 'Current Year Entitlement', table_border)
        worksheet.write(row + 2, 8, 'Pending', table_border)
        worksheet.write(row + 2, 9, 'Taken', table_border)
        worksheet.write(row + 2, 10, 'Balance Days', table_border)
#         worksheet.write(row + 2, 11, 'Balance MTD', table_border)

    def _get_company_info(self, worksheet, row, header2):
        """
            this method display company info
        """
        cr, uid, context = self.env.args
        ids = self.env['hr.employee'].search([('user_id', '=', uid)])
        today = datetime.now()
        today_date = str(today.strftime('%d')) + '-' + str(today.strftime('%m')) + '-' + str(today.strftime('%Y'))
        worksheet.write(row + 0, 0, 'Title', header2)
        worksheet.write(row + 0, 1, 'Leave Balance Report', header2)
        worksheet.write(row + 1, 0, 'Company Name', header2)
        worksheet.write_merge(3, 3, 1, 3, ids[0].company_id.name, header2)
        worksheet.write(row + 2, 0, 'Date', header2)
        worksheet.write(row + 2, 1, today_date, header2)
    
    @api.multi
    def _get_pending_leave(self , emp_id, leave_id, from_date_str, from_to_str):
        cr, uid, context = self.env.args
        cr.execute("""
            SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d 
            and type='remove' and state='confirm' and date_from >= '%s' and date_to <= '%s' """ 
                % (emp_id, leave_id, from_date_str, from_to_str))
        pending_leave = cr.fetchone()
        return pending_leave
    
    @api.multi
    def _get_taken_leave(self, emp_id, leave_id, from_date_str, from_to_str):
        cr, uid, context = self.env.args
        cr.execute("""
            SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d 
            and type='remove' and state='validate' and date_from >= '%s' and date_to <= '%s' """ 
                % (emp_id, leave_id, from_date_str, from_to_str))
        taken_leave = cr.fetchone()
        return taken_leave
    
    @api.multi
    def _get_total_leave(self, emp_id, leave_id, fiscalyear_id):
        cr, uid, context = self.env.args
        cr.execute("""
            SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d and 
            type='add' and state='validate' and hr_year_id =%d""" 
                % (emp_id, leave_id, fiscalyear_id))
        total_leave = cr.fetchone()
        if total_leave:
            total_leave = total_leave[0] if total_leave[0] != None else 0
        else:
            total_leave = 0
        return total_leave
    
    @api.multi
    def _get_carry_leave(self, emp_id, leave_id, fiscalyear_id):
        cr, uid, context = self.env.args
        cr.execute("""
                SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d and 
                    type='add' and state='validate' and hr_year_id =%d and carry_forward ='TRUE'""" 
                    % (emp_id, leave_id, fiscalyear_id))
        carry_leave = cr.fetchone()
        return carry_leave
    
#     @api.multi
#     def _get_earn_leave(self, emp_id, leave_id, from_date_str, from_to_str, fiscalyear_id):
#         cr, uid, context = self.env.args
#         earn_leaves = 0
#         holiday_obj=self.env['hr.holidays.status']
#         emp_brw  = self.env['hr.employee'].browse(emp_id)
#         user_id = emp_brw.user_id and emp_brw.user_id.id or uid
#         for holiday_earn_record in holiday_obj.browse(leave_id):
#             if holiday_earn_record.earned_leave == True:
#                 date_from1 = datetime.strptime(from_date_str, DEFAULT_SERVER_DATE_FORMAT)
#                 date_to1 = datetime.strptime(from_to_str, DEFAULT_SERVER_DATE_FORMAT)
#                 default_allocation = holiday_earn_record.default_leave_allocation
#                 working_months = relativedelta(date_to1, date_from1)
#                 total_month = 1
#                 if working_months and working_months.months:
#                     total_month = working_months.months
#                 if default_allocation:
#                     default_leave = (float(default_allocation) / 12) * total_month
#                     earn_leaves = round(default_leave)
#         return earn_leaves

    @api.multi
    def print_sg_leave_summary_report_wizard(self):
        rml_obj = report_sxw.rml_parse(self._cr, self._uid, self.env['res.users']._name, self.env.context)
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        context = dict(context)
        user_obj=self.env['res.users'].search([])
        ids = self.env['hr.employee'].search([('user_id', '=', uid)])
        data = self.read()[0]
        if 'all_employee' or 'all_leave'in data:
            context.update({'all_employee':data['all_employee'], 'all_leave':data['all_leave']})
        context.update({
                        'from_date': data['from_date'],
                        'to_date':data['to_date'],
                        'leave_type_id':data['leave_type_id'],
                        'employee_id':data['employee_id']
        })
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        borders = xlwt.Borders()
        border_style = xlwt.XFStyle()  # Create Style
        font = xlwt.Font()
        font.bold = True
        table_border = xlwt.easyxf('font: bold 1, height 200; align: wrap on;')
        table_border.num_format_str = '@'
        table_border1 = xlwt.easyxf('font: height 200; align: wrap on;')
        table_border1.num_format_str = '@'
        table_border_center = xlwt.easyxf("font: bold 0; align: wrap on, horiz centre;")
        table_border_center.num_format_str = '@'
        table_border1_center = xlwt.easyxf("align: wrap on, horiz centre;")
        table_border1_center.num_format_str = '@'
        borders.top = xlwt.Borders.MEDIUM
        borders.bottom = xlwt.Borders.MEDIUM
        borders.left = xlwt.Borders.MEDIUM
        borders.right = xlwt.Borders.MEDIUM
        table_border.borders = borders
        table_border1.borders = borders
        table_border_center.borders = borders
        table_border1_center.borders = borders
        header = xlwt.easyxf('font: bold 1, height 300', 'align: horiz center')
        header.num_format_str = '@'
        header2 = xlwt.easyxf('font: bold 1, height 200', 'align: horiz left')
        header2.num_format_str = '@'
        header3 = xlwt.easyxf('font: bold 1 , height 250', 'align: horiz left')
        header3.num_format_str = '@'
        header1 = xlwt.easyxf("align: wrap on;")
        header1.num_format_str = '@'
        borders.top = xlwt.Borders.MEDIUM
        borders.bottom = xlwt.Borders.MEDIUM
        borders.left = xlwt.Borders.MEDIUM
        borders.right = xlwt.Borders.MEDIUM
        header1.borders = borders

        worksheet.col(0).width = 7000
        worksheet.col(1).width = 7000
        worksheet.col(2).width = 7000
        worksheet.col(3).width = 7000
        worksheet.col(4).width = 7000
        worksheet.col(5).width = 6000
        worksheet.col(6).width = 6000
        worksheet.col(7).width = 6000
        worksheet.col(8).width = 6000
        worksheet.col(9).width = 7000
        worksheet.row(0).height = 600
        worksheet.row(1).height = 300
        worksheet.row(2).height = 400
        worksheet.row(3).height = 300
        worksheet.row(4).height = 300
        worksheet.row(5).height = 400
        worksheet.row(6).height = 300
        worksheet.row(7).height = 300
        worksheet.row(8).height = 400
        worksheet.row(9).height = 300

#        path = os.path.abspath(os.path.dirname(__file__))
#        path += '/../static/img/abced.bmp'
#        worksheet.insert_bitmap(path,0,2,1)

        worksheet.write_merge(0, 0, 3, 5, ids[0].company_id.name, header)

        emp_obj = self.env['hr.employee']
        if context["employee_id"]:
            emp_record = self.env['hr.employee'].browse(context["employee_id"][0])
            department = emp_record.department_id and emp_record.department_id.name or ''
            emp_no = emp_record.identification_id or ''
            emp_title = emp_record.job_id and emp_record.job_id.name or ''
            joined_year = emp_record.joined_year or ''
            leave_structure = emp_record.leave_config_id and emp_record.leave_config_id.name or ''
        else:
            employee_res = self.env['hr.employee'].search([])
        leave_obj = self.env['hr.holidays.status']
        holiday_obj = self.env['hr.holidays']
        if context['all_leave'] == True:
            leave_ids = leave_obj.search([])

        args = [('date_start', '<=' , context.get('from_date')), ('date_stop', '>=', context.get('to_date'))]
        fiscalyear_id = self.env['hr.year'].search(args)
        if fiscalyear_id:
            fiscalyear_id = fiscalyear_id[0]
        else:
            raise ValidationError(_('You can search only single year records'))

        from_date_date = datetime.strptime(context["from_date"] + " 00:00:00", DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(hours=8)
        from_date_str = from_date_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        from_to_date = datetime.strptime(context["to_date"] + " 23:59:59", DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(hours=8)
        from_to_str = from_to_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

#       WHEN BOTH CHECKBOX IS TRUE
        if context['all_employee'] == True and context['all_leave'] == True:
            row = 2
            col = 0
            self._get_company_info(worksheet, row, header2)
            row = row + 4
            worksheet.row(row + 4).height = 300
            leave_name = ''
            leave_ids=leave_obj.search([])
            for leave in leave_ids:
                row = row + 1
                worksheet.row(row).height = 300
                worksheet.row(row + 2).height = 600
                leave_name = leave.name2 if leave.name2 else leave.name
                worksheet.write_merge(row, row , col, 2, leave_name, header3)
                self._get_employee_header(worksheet, row, table_border)
                row = row + 3
                col = 0
                for emp_record in employee_res:
                    emp_id = emp_record.id
                    leave_id = leave.id
#                   DEPARTMENT
                    if emp_record.department_id and emp_record.department_id.name:
                        worksheet.write(row, col + 0, emp_record.department_id.name , table_border1)
                    else:
                        worksheet.write(row, col + 0, '' , table_border1)
#                   IDENTIFICATION NUMBER
                    if emp_record.identification_id:
                        worksheet.write(row, col + 1, emp_record.identification_id , table_border1)
                    else:
                        worksheet.write(row, col + 1, '' , table_border1)
#                   EMPLOYEE NAME
                    if emp_record.name:
                        worksheet.write(row, col + 2, emp_record.name, table_border1)
                    else:
                        worksheet.write(row, col + 2, '', table_border1)
#                   DATE JOINED
                    if emp_record.join_date:
                        emp_j_date = datetime.strptime(emp_record.join_date, DEFAULT_SERVER_DATE_FORMAT)
                        emp_join_dt = str(emp_j_date.strftime('%d')) + '-' + str(emp_j_date.strftime('%m')) + '-' + str(emp_j_date.strftime('%Y'))
                        worksheet.write(row, col + 3, emp_join_dt , table_border1)
                    else:
                        worksheet.write(row, col + 3, '' , table_border1)
#                   SERVICE YEARS
                    if emp_record.joined_year:
                        worksheet.write(row, col + 4, emp_record.joined_year, table_border1)
                    else:
                        worksheet.write(row, col + 4, '', table_border1)
#                   LEAVE STRUCTURE
                    if emp_record.leave_config_id and emp_record.leave_config_id.name:
                        worksheet.write(row, col + 5, emp_record.leave_config_id.name, table_border1)
                    else:
                        worksheet.write(row, col + 5, '', table_border1)
#                   CARRY FORWARD
                    carry_leave = self._get_carry_leave(emp_id, leave_id, fiscalyear_id)
                    if carry_leave and carry_leave[0] and carry_leave[0] != None:
                        worksheet.write(row, col + 6, int(carry_leave[0]), table_border1_center)
                    else:
                        worksheet.write(row, col + 6, 0, table_border1_center)
#                   CURRENT YEAR
                    total_leave = self._get_total_leave(emp_id, leave_id, fiscalyear_id)
                    if total_leave != 0:
                        worksheet.write(row, col + 7, rml_obj.formatLang(total_leave) , table_border1_center)
                    else:
                        worksheet.write(row, col + 7, 0 , table_border1_center)
#                   PENDING
                    pending_leave = self._get_pending_leave(emp_id, leave_id, from_date_str, from_to_str)
                    if pending_leave and pending_leave[0] and pending_leave[0] != None:
                        worksheet.write(row, col + 8, pending_leave[0], table_border1_center)
                    else:
                        worksheet.write(row, col + 8, 0, table_border1_center)
#                   TAKEN
                    taken_leave = self._get_taken_leave(emp_id, leave_id, from_date_str, from_to_str)
                    if taken_leave and taken_leave[0] and taken_leave[0] != None:
                        worksheet.write(row, col + 9, taken_leave[0], table_border1_center)
                    else:
                        worksheet.write(row, col + 9, 0, table_border1_center)
#                   BALANCE YTD
                    if total_leave  != 0:
                        if taken_leave and taken_leave[0] and taken_leave[0] != None:
                            after_blc = total_leave - taken_leave[0]
                            worksheet.write(row, col + 10, rml_obj.formatLang(after_blc) or 0, table_border1_center)
                        else:
                            worksheet.write(row, col + 10, rml_obj.formatLang(total_leave) , table_border1_center)
                    else:
                        worksheet.write(row, col + 10, 0 , table_border1_center)
#                   BALANCE MTD
#                     earn_leaves = self._get_earn_leave(emp_id, leave_id, context["from_date"], context["to_date"], fiscalyear_id)
#                     if earn_leaves != 0:
#                         if taken_leave and taken_leave[0] and taken_leave[0] != None:
#                             earn_leaves = earn_leaves - taken_leave[0]
#                             worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#                         else:
#                             worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#                     else:
#                         worksheet.write(row, col + 11, 0 , table_border1_center)
                    row = row + 1
            row = row + 1

#       WHEN EMPLOYEE CHECKBOX TRUE
        elif context['all_employee'] == True and context['all_leave'] == False:
            row = 2
            col = 0
            self._get_company_info(worksheet, row, header2)
            row = row + 4
            leave_type = str(context["leave_type_id"][1]).upper() + ' LEAVE RECORD'
            worksheet.row(row).height=400
            worksheet.write_merge(row, row , col, 2, leave_type, header3)
            worksheet.row(row + 2).height = 500
            self._get_employee_header(worksheet, row, table_border)
            row = row + 3
            col = 0
            for emp_record in employee_res:
                emp_id = emp_record.id
                leave_id = context["leave_type_id"][0]
                pending_leave = self._get_pending_leave(emp_id, leave_id, from_date_str, from_to_str)
                taken_leave = self._get_taken_leave(emp_id, leave_id, from_date_str, from_to_str)
                total_leave = self._get_total_leave(emp_id, leave_id, fiscalyear_id)
                carry_leave = self._get_carry_leave(emp_id, leave_id, fiscalyear_id)
#                 earn_leaves = self._get_earn_leave(emp_id, leave_id, context["from_date"], context["to_date"], fiscalyear_id)
#               DEPARTMENT
                if emp_record.department_id and emp_record.department_id.name:
                    worksheet.write(row, col + 0, emp_record.department_id.name , table_border1)
                else:
                    worksheet.write(row, col + 0, '' , table_border1)
#               IDENTIFICATION NUMBER
                if emp_record.identification_id:
                    worksheet.write(row, col + 1, emp_record.identification_id , table_border1)
                else:
                    worksheet.write(row, col + 1, '' , table_border1)
#               EMPLOYEE NAME
                if emp_record.name:
                    worksheet.write(row, col + 2, emp_record.name, table_border1)
                else:
                    worksheet.write(row, col + 2, emp_record.name, table_border1)
#               JOIN DATE
                if emp_record.join_date:
                    emp_j_date = datetime.strptime(emp_record.join_date, DEFAULT_SERVER_DATE_FORMAT)
                    emp_join_dt = str(emp_j_date.strftime('%d')) + '-' + str(emp_j_date.strftime('%m')) + '-' + str(emp_j_date.strftime('%Y'))
                    worksheet.write(row, col + 3, emp_join_dt , table_border1)
                else:
                    worksheet.write(row, col + 3, '' , table_border1)
#               SERVICE YEARS
                if emp_record.joined_year:
                    worksheet.write(row, col + 4, emp_record.joined_year, table_border1)
                else:
                    worksheet.write(row, col + 4, '', table_border1)
#               LEAVE STRUCTURE
                if emp_record.leave_config_id and emp_record.leave_config_id.name:
                    worksheet.write(row, col + 5, emp_record.leave_config_id.name, table_border1)
                else:
                    worksheet.write(row, col + 5, '', table_border1)
#               CARRY FORWARD
                if carry_leave and carry_leave[0] and carry_leave[0] != None:
                    worksheet.write(row, col + 6, int(carry_leave[0]), table_border1_center)
                else:
                    worksheet.write(row, col + 6, 0, table_border1_center)
#               CURRENT YEAR TOTAL LEAVE
                if total_leave != 0:
                    worksheet.write(row, col + 7, rml_obj.formatLang(total_leave) , table_border1_center)
                else:
                    worksheet.write(row, col + 7, 0 , table_border1_center)
#               PENDING
                if pending_leave and pending_leave[0] and pending_leave[0] != None:
                    worksheet.write(row, col + 8, pending_leave[0], table_border1_center)
                else:
                    worksheet.write(row, col + 8, 0, table_border1_center)
#               TAKEN
                if taken_leave and taken_leave[0] and taken_leave[0] != None:
                    worksheet.write(row, col + 9, taken_leave[0], table_border1_center)
                else:
                    worksheet.write(row, col + 9, 0, table_border1_center)
#               BALANCE YTD
                if total_leave  != 0:
                    if taken_leave and taken_leave[0] and taken_leave[0] != None:
                        after_blc = total_leave - taken_leave[0]
                        worksheet.write(row, col + 10, rml_obj.formatLang(after_blc) or 0, table_border1_center)
                    else:
                        worksheet.write(row, col + 10, rml_obj.formatLang(total_leave) , table_border1_center)
                else:
                    worksheet.write(row, col + 10, 0 , table_border1_center)
#               BALANCE MTD
#                 if earn_leaves != 0:
#                     if taken_leave and taken_leave[0] and taken_leave[0] != None:
#                         earn_leaves = earn_leaves - taken_leave[0]
#                         worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#                     else:
#                         worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#                 else:
#                     worksheet.write(row, col + 11, 0 , table_border1_center)
                row += 1
            row = row + 1

#         WHEN LEAVE CHECK BOX IS TRUE
        elif context['all_leave'] == True and context['all_employee'] == False:
            row = 2
            col = 0
            self._get_company_info(worksheet, row, header2)
            row = row + 4
#            worksheet.row(row + 4).height = 500
            leave_name = ''
            if emp_record.leave_config_id and emp_record.leave_config_id.holiday_group_config_line_ids and emp_record.leave_config_id.holiday_group_config_line_ids.ids:
                leave_ids = []
                for leave_config_type in emp_record.leave_config_id.holiday_group_config_line_ids:
                    leave_ids.append(leave_config_type.leave_type_id.id)
                for leave in leave_obj.browse(leave_ids):
                    row = row + 1
                    worksheet.row(row).height = 300
                    worksheet.row(row + 2).height = 500
                    leave_name = leave.name2 if leave.name2 else leave.name
                    worksheet.write_merge(row, row , col, 2, leave_name, header3)
                    self._get_employee_header(worksheet, row, table_border)
                    row = row + 3
                    col = 0
                    emp_id = emp_record.id
                    leave_id = leave.id
                    pending_leave = self._get_pending_leave(emp_id, leave_id, from_date_str, from_to_str)
                    taken_leave = self._get_taken_leave(emp_id, leave_id, from_date_str, from_to_str)
                    total_leave = self._get_total_leave(emp_id, leave_id, fiscalyear_id)
                    carry_leave = self._get_carry_leave(emp_id, leave_id, fiscalyear_id)
#                     earn_leaves = self._get_earn_leave(emp_id, leave_id, context["from_date"], context["to_date"], fiscalyear_id)
    #                   DEPARTMENT
                    if emp_record.department_id and emp_record.department_id.name:
                        worksheet.write(row, col + 0, emp_record.department_id.name , table_border1)
                    else:
                        worksheet.write(row, col + 0, '' , table_border1)
    #                   IDENTIFICATION NUMBER
                    if emp_record.identification_id:
                        worksheet.write(row, col + 1, emp_record.identification_id , table_border1)
                    else:
                        worksheet.write(row, col + 1, '' , table_border1)
    
                    if emp_record.name:
                        worksheet.write(row, col + 2, emp_record.name, table_border1)
                    else:
                        worksheet.write(row, col + 2, emp_record.name, table_border1)
    
                    if emp_record.join_date:
                        emp_j_date = datetime.strptime(emp_record.join_date, DEFAULT_SERVER_DATE_FORMAT)
                        emp_join_dt = str(emp_j_date.strftime('%d')) + '-' + str(emp_j_date.strftime('%m')) + '-' + str(emp_j_date.strftime('%Y'))
                        worksheet.write(row, col + 3, emp_join_dt , table_border1)
                    else:
                        worksheet.write(row, col + 3, '' , table_border1)
    
                    if emp_record.joined_year:
                        worksheet.write(row, col + 4, emp_record.joined_year, table_border1)
                    else:
                        worksheet.write(row, col + 4, '', table_border1)
    
                    if emp_record.leave_config_id and emp_record.leave_config_id.name:
                        worksheet.write(row, col + 5, emp_record.leave_config_id.name, table_border1)
                    else:
                        worksheet.write(row, col + 5, '', table_border1)
    
    #                       CARRY FORWARD
                    if carry_leave and carry_leave[0] and carry_leave[0] != None:
                        worksheet.write(row, col + 6, int(carry_leave[0]), table_border1_center)
                    else:
                        worksheet.write(row, col + 6, 0, table_border1_center)
    #                       CURRENT YEAR TOTAL LEAVE
                    if total_leave != 0:
                        worksheet.write(row, col + 7, rml_obj.formatLang(total_leave) , table_border1_center)
                    else:
                        worksheet.write(row, col + 7, 0 , table_border1_center)
    #                       PENDING
                    if pending_leave and pending_leave[0] and pending_leave[0] != None:
                        worksheet.write(row, col + 8, pending_leave[0], table_border1_center)
                    else:
                        worksheet.write(row, col + 8, 0, table_border1_center)
    #                       TAKEN
                    if taken_leave and taken_leave[0] and taken_leave[0] != None:
                        worksheet.write(row, col + 9, taken_leave[0], table_border1_center)
                    else:
                        worksheet.write(row, col + 9, 0, table_border1_center)
    #                    BALANCE YTD
                    if total_leave  != 0:
                        if taken_leave and taken_leave[0] and taken_leave[0] != None:
                            after_blc = total_leave - taken_leave[0]
                            worksheet.write(row, col + 10, rml_obj.formatLang(after_blc) or 0, table_border1_center)
                        else:
                            worksheet.write(row, col + 10, rml_obj.formatLang(total_leave) , table_border1_center)
                    else:
                        worksheet.write(row, col + 10, 0 , table_border1_center)
    #                   BALANCE MTD
#                     if earn_leaves != 0:
#                         if taken_leave and taken_leave[0] and taken_leave[0] != None:
#                             earn_leaves = earn_leaves - taken_leave[0]
#                             worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#                         else:
#                             worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#                     else:
#                         worksheet.write(row, col + 11, 0 , table_border1_center)
                    row += 1
                row = row + 1

#         WHEN BOTH CHECKBOX IS FALSE
        else:
            row = 2
            col = 0
            self._get_company_info(worksheet, row, header2)
            row = row + 5
            worksheet.row(row).height = 340
            worksheet.write_merge(row, row , col, 2, context["leave_type_id"][1], header3)
            worksheet.row(row + 2).height = 500
            self._get_employee_header(worksheet, row, table_border)
            row = row + 3
            col = 0
            emp_id = emp_record.id
            leave_id = context["leave_type_id"][0]
            pending_leave = self._get_pending_leave(emp_id, leave_id, from_date_str, from_to_str)
            taken_leave = self._get_taken_leave(emp_id, leave_id, from_date_str, from_to_str)
            total_leave = self._get_total_leave(emp_id, leave_id, fiscalyear_id)
            carry_leave = self._get_carry_leave(emp_id, leave_id, fiscalyear_id)
#             earn_leaves = self._get_earn_leave(emp_id, leave_id, context["from_date"], context["to_date"], fiscalyear_id)
#           DEPARTMENT
            if emp_record.department_id and emp_record.department_id.name:
                worksheet.write(row, col + 0, emp_record.department_id.name , table_border1)
            else:
                worksheet.write(row, col + 0, '' , table_border1)
#           IDENTIFICATION NUMBER
            if emp_record.identification_id:
                worksheet.write(row, col + 1, emp_record.identification_id , table_border1)
            else:
                worksheet.write(row, col + 1, '' , table_border1)
#           EMPLOYEE NAME
            if emp_record.name:
                worksheet.write(row, col + 2, emp_record.name, table_border1)
            else:
                worksheet.write(row, col + 2, emp_record.name, table_border1)
#           DATE JOINED
            if emp_record.join_date:
                emp_j_date = datetime.strptime(emp_record.join_date, DEFAULT_SERVER_DATE_FORMAT)
                emp_join_dt = str(emp_j_date.strftime('%d')) + '-' + str(emp_j_date.strftime('%m')) + '-' + str(emp_j_date.strftime('%Y'))
                worksheet.write(row, col + 3, emp_join_dt , table_border1)
            else:
                worksheet.write(row, col + 3, '' , table_border1)
#           SERVICE YEARS
            if emp_record.joined_year:
                worksheet.write(row, col + 4, emp_record.joined_year, table_border1)
            else:
                worksheet.write(row, col + 4, '', table_border1)
#           LEAVE STRUCTURE
            if emp_record.leave_config_id and emp_record.leave_config_id.name:
                worksheet.write(row, col + 5, emp_record.leave_config_id.name, table_border1)
            else:
                worksheet.write(row, col + 5, '', table_border1)
#           CARRY FORWARD
            if carry_leave and carry_leave[0] and carry_leave[0] != None:
                worksheet.write(row, col + 6, int(carry_leave[0]), table_border1_center)
            else:
                worksheet.write(row, col + 6, 0, table_border1_center)
#           CURRENT YEAR
            if total_leave != 0:
                worksheet.write(row, col + 7, rml_obj.formatLang(total_leave) , table_border1_center)
            else:
                worksheet.write(row, col + 7, 0 , table_border1_center)
#           PENDING
            if pending_leave and pending_leave[0] and pending_leave[0] != None:
                worksheet.write(row, col + 8, pending_leave[0], table_border1_center)
            else:
                worksheet.write(row, col + 8, 0, table_border1_center)
#           TAKEN
            if taken_leave and taken_leave[0] and taken_leave[0] != None:
                worksheet.write(row, col + 9, taken_leave[0], table_border1_center)
            else:
                worksheet.write(row, col + 9, 0, table_border1_center)
#           BALANCE YTD
            if total_leave  != 0:
                if taken_leave and taken_leave[0] and taken_leave[0] != None:
                    after_blc = total_leave - taken_leave[0]
                    worksheet.write(row, col + 10, rml_obj.formatLang(after_blc) or 0, table_border1_center)
                else:
                    worksheet.write(row, col + 10, rml_obj.formatLang(total_leave) , table_border1_center)
            else:
                worksheet.write(row, col + 10, 0 , table_border1_center)
#           BALANCE MTD
#             if earn_leaves != 0:
#                 if taken_leave and taken_leave[0] and taken_leave[0] != None:
#                     earn_leaves = earn_leaves - taken_leave[0]
#                     worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#                 else:
#                     worksheet.write(row, col + 11, earn_leaves , table_border1_center)
#             else:
#                 worksheet.write(row, col + 11, 0 , table_border1_center)
            row += 1
        row = row + 1


        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        res = base64.encodestring(data)
        module_rec = self.env['excel.sg.leave.summary.report'].create({'name': 'Leave summary.xls', 'file' : res})
        return {
          'name': _('Leave Summary Report'),
          'res_id' : module_rec.id,
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'excel.sg.leave.summary.report',
          'type': 'ir.actions.act_window',
          'target': 'new',
          'context': context,
          }
#        return base64.encodestring(data)
