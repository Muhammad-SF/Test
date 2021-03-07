# -*- coding: utf-8 -*-
import time
from datetime import date, datetime, timedelta
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.modules import get_module_resource
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import except_orm, Warning as UserError
from openerp.exceptions import ValidationError
from dateutil import relativedelta


class StudentPayslipLine(models.Model):
    '''Student Fees Structure Line'''
    _inherit = 'student.payslip.line'
    
    code = fields.Char('Code', required=0)
    '''type = fields.Selection([('month', 'Monthly'),
                             ('year', 'Yearly'),
                             ('range', 'Range'),
                             ('enrollment_fee', 'Enrollment Fee'),
                             ('application_fee', 'Application Fee'),
                             ('others', 'Others')],
                            'Duration', required=True)'''

class StudentFeesStructureLine(models.Model):
    '''Student Fees Structure Line'''
    _inherit = 'student.fees.structure.line'
    
    '''type = fields.Selection([('month', 'Monthly'),
                             ('year', 'Yearly'),
                             ('range', 'Range'),
                             ('enrollment_fee', 'Enrollment Fee'),
                             ('application_fee', 'Application Fee')],
                            'Duration', required=True)'''
    number_of_months = fields.Integer('No Of Months')
    
    
class StudentStudent(models.Model):
    _inherit = 'student.student'
    
    def get_dates(self,date_start,date_stop,number_of_months):
        date_list = [date_start.date()]
        next_date = date_start
        while next_date < date_stop:
            next_date = next_date + relativedelta.relativedelta(months=+number_of_months)
            if next_date < date_stop:
                date_list.append(next_date.date())
        return date_list
    
    @api.multi
    def cron_semester_fees_receipt(self):
        student_ids = self.search([('state','=','done')])
        #print "\n\nStudent-Ids=",student_ids
        for student in student_ids:
            #print "\n\nstudent=",student
            intake_id = student.year
            enrollment_fee_id = intake_id.enrollment_fee_id
            date_start = datetime.strptime(intake_id.date_start , '%Y-%m-%d') 
            date_stop = datetime.strptime(intake_id.date_stop , '%Y-%m-%d') 
            r = relativedelta.relativedelta(date_stop, date_start)
            month_difference = r.months + 1
            number_of_months = 0
            for enrollment_line in enrollment_fee_id.line_ids:
                if enrollment_line.type == 'month':
                    number_of_months = enrollment_line.number_of_months
            date_list = self.get_dates(date_start,date_stop,number_of_months)
            today_date = datetime.today().date()
            #print "\n\n====today_date==",today_date
            #today_date = datetime.strptime('01052017', "%d%m%Y").date() #datetime.date(2016, 5, 1)
            start_date = date_start.date()
            if today_date in date_list:
                if today_date != start_date:
		            student_payslip = self.env['student.payslip']
		            payslip_vals = {
		                'student_id': student and student.id or False,
		                'name': 'Semester Fee Receipt - ' + student.name,
		                'date': fields.Date.today(),
		                'division_id' : student.division_id and student.division_id.id or False,
		                'type': 'out_refund',
		                'company_id': student.school_id.company_id and student.school_id.company_id.id or False,
		            }
		            if student.year.enrollment_fee_id:
		                payslip_vals.update({'fees_structure_id':intake_id.enrollment_fee_id and intake_id.enrollment_fee_id.id or False,})
		            student_payslip_id = student_payslip.create(payslip_vals)
		            student_payslip_line_pool = self.env['student.payslip.line']
		            if student.year.enrollment_fee_id.line_ids:
		                for fee_structure_line in student.year.enrollment_fee_id.line_ids:
		                    if fee_structure_line.type == 'month':
		                        payslip_line_vals = {
		                            'name': fee_structure_line.name,
		                            'code': fee_structure_line.code,
		                            'type': fee_structure_line.type,
		                            'account_id' : fee_structure_line.account_id and fee_structure_line.account_id.id or False,
		                            'amount': fee_structure_line.amount or 0.00,
		                            'slip_id': student_payslip_id and student_payslip_id.id or False
		                        }
		                        student_payslip_line_pool.create(payslip_line_vals)
		                        #print "\n\nSemester Fees Receipt Created"
        return True
