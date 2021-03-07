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

from odoo import api, models
import time
import datetime


class ppd_hr_cheque_summary_report(models.AbstractModel):
    _name = 'report.sg_hr_report.cheque_summary_report_tmp'
    
    @api.model
    def get_info(self, data):
        payslip_obj = self.env['hr.payslip']
        employee_obj = self.env['hr.employee']
        hr_department_brw =  self.env['hr.department'].search([])
        result = {}
        payslip_data= {}
        department_info = {}
        final_result = {}
        date_from = data.get('date_start') or False
        date_to = data.get('date_stop') or False

        employee_ids = employee_obj.search([('id', 'in', data.get('employee_ids')), 
                                            ('department_id', '=', False)])
        department_total_amount = 0.0
        for employee in employee_ids:
            payslip_ids = []
            if employee.bank_account_id:
                payslip_id = payslip_obj.search([('date_from', '>=', date_from), 
                                                 ('date_from','<=',date_to),
                                                 ('employee_id', '=' , employee.id), 
                                                 ('pay_by_cheque', '=', True), 
                                                 ('state', 'in', ['draft', 'done', 'verify'])])
                if payslip_id:
                    payslip_ids.append(payslip_id)
                net = 0.0
                cheque_number = ''
                for payslip in payslip_ids:
                    for payslip_rec in payslip:
                        linetot = 0.0
                        cheque_number = payslip_rec.cheque_number or ''
                        for line in payslip_rec.line_ids:
                            if line.code == 'NET':
                                linetot += line.total
                        if cheque_number:
                            payslip_data = {'employee_id': employee.user_id and employee.user_id.login or ' ',
                                            'employee_name': employee.name or ' ',
                                            'cheque_number': cheque_number,
                                            'amount': linetot}
                            net += linetot
                        if 'Undefined' in result:
                            result.get('Undefined').append(payslip_data)
                        else:
                            result.update({'Undefined': [payslip_data]})
            department_total_amount += net
        department_total = {'total': department_total_amount, 'department_name': "Total Undefined"}
        if 'Undefined' in department_info:
            department_info.get('Undefined').append(department_total)
        else:
            department_info.update({'Undefined': [department_total]})
        for hr_department in hr_department_brw:
            employee_ids = employee_obj.search([('id', 'in', data.get('employee_ids')), 
                                                ('department_id', '=', hr_department.id)])
            department_total_amount = 0.0
            for employee in employee_ids:
                payslip_ids = []
                if employee.bank_account_id:
                    payslip_id = payslip_obj.search([('date_from', '>=', date_from), 
                                                     ('date_from','<=',date_to),
                                                     ('employee_id', '=' , employee.id), 
                                                     ('pay_by_cheque', '=', True), 
                                                     ('state', 'in', ['draft', 'done', 'verify'])])
                    if payslip_id:
                        payslip_ids.append(payslip_id)
                net = 0.0
                cheque_number = ''
                for payslip in payslip_ids:
                    for payslip_rec in payslip:
                        linetot = 0.0
                        cheque_number = payslip_rec.cheque_number or ''
                        for line in payslip_rec.line_ids:
                            if line.code == 'NET':
                                linetot += line.total
                        if cheque_number:
                            payslip_data = {'employee_id': employee.user_id and employee.user_id.login or ' ',
                                            'employee_name': employee.name or ' ',
                                            'cheque_number': cheque_number,
                                            'amount': linetot}
                            net += linetot
                            if hr_department.id in result:
                                result.get(hr_department.id).append(payslip_data)
                            else:
                                result.update({hr_department.id: [payslip_data]})
                    department_total_amount += net
            department_total = {'total': department_total_amount, 'department_name': "Total "+hr_department.name}
            if hr_department.id in department_info:
                department_info.get(hr_department.id).append(department_total)
            else:
                department_info.update({hr_department.id: [department_total]})
        for key, val in result.items():
            final_result[key] = {'lines': val, 'departmane_total': department_info[key] }
        return final_result.values()
    
    @api.model
    def get_total(self, data):
        date_from = data.get('date_start') or False
        date_to = data.get('date_stop') or False
        employee_rec = self.env['hr.employee'].search([('id', 'in', data.get('employee_ids'))])
        total_ammount = 0
        payslip_ids = []
        for employee in employee_rec:
            if employee.bank_account_id:
                payslip_id = self.env['hr.payslip'].search([('date_from', '>=', date_from),
                                                            ('date_from','<=',date_to),
                                                            ('employee_id', '=' , employee.id),
                                                            ('pay_by_cheque', '=', True), 
                                                            ('state', 'in', ['draft', 'done', 'verify'])])
                if payslip_id:
                    payslip_ids.append(payslip_id)
        for payslip in payslip_ids:
            for payslip_rec in payslip:
                for line in payslip_rec.line_ids:
                    if line.code == 'NET':
                        total_ammount+=line.total
        return total_ammount
    
    @api.model
    def get_totalrecord(self, data):
        date_from = data.get('date_start') or False
        date_to = data.get('date_stop') or False
        employee_rec = self.env['hr.employee'].search([('id', 'in', data.get('employee_ids'))])
        payslip_list = []
        for employee in employee_rec:
            payslip_rec = self.env['hr.payslip'].search([('date_from', '>=', date_from),
                                                         ('date_from','<=',date_to),
                                                         ('pay_by_cheque', '=', True),
                                                         ('employee_id', '=' , employee.id),
                                                         ('state', 'in', ['draft', 'done', 'verify'])])
            if payslip_rec and payslip_rec.ids:
                payslip_list.append(payslip_rec.ids)
        return len(payslip_list)
    
    @api.multi
    def render_html(self, docids,data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        data = docs.read([])[0]
        report_lines = self.get_info(data)
        total = self.get_total(data)
        total_employees = self.get_totalrecord(data)
        docargs = {'doc_ids' : self.ids,
                   'doc_model' : self.model,
                   'data' : data,
                   'docs' : docs,
                   'time' : time,
                   'get_info' : report_lines,
                   'get_total' : total,
                   'get_totalrecord' : total_employees,}
        return self.env['report'].render('sg_hr_report.cheque_summary_report_tmp', docargs)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: