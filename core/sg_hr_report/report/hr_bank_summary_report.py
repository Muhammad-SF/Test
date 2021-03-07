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
from odoo import api, models


class ppd_bank_summary_receipt(models.AbstractModel):
    _name = 'report.sg_hr_report.hr_bank_summary_report_tmp'
    
    @api.model
    def get_info(self, data):
        payslip_obj = self.env['hr.payslip']
        employee_obj = self.env['hr.employee']
        bank_obj = self.env['hr.bank.details']
        result = {}
        payslip_data= {}
        department_info = {}
        final_result = {}
        date_from = data.get('start_date') or False
        date_to = data.get('end_date') or False
        employee_ids = employee_obj.search([('bank_account_id','!=',False), 
                                            ('id', 'in', data.get('employee_ids')), 
                                            ('department_id', '!=', False)])


        department_total_amount = 0.0
        new_employee_ids = []
        new_employee_rec = []

        if employee_ids and employee_ids.ids:
            bank_rec = bank_obj.search([('bank_emp_id', 'in', employee_ids.ids)], order="bank_name, bank_code, branch_code")

            for bank in bank_rec:
                if bank.bank_emp_id.id not in new_employee_ids:
                    new_employee_ids.append(bank.bank_emp_id.id)

            new_employee_rec += list(set(employee_ids.ids).difference(set(new_employee_ids)))
            if not new_employee_rec:
                new_employee_rec = new_employee_ids

        for employee in employee_obj.browse(new_employee_rec):
            payslip_ids = payslip_obj.search([('date_from', '>=', date_from),
                                              ('date_from','<=',date_to),
                                              ('employee_id', '=' , employee.id),
                                              ('pay_by_cheque','=',False),
                                              ('state', 'in', ['draft', 'done', 'verify'])])

            net = 0.0
            for payslip in payslip_ids:

                print ">>>>>>>>>> payslip.employee_id.department_id.id>>>>>>>>>>>>>>\n\n",payslip.employee_id.department_id.id

                # if not payslip.employee_id.department_id.id:
                if payslip.employee_id.department_id.id:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total
            payslip_data = {
                            'bank_name':employee.bank_account_id and employee.bank_account_id.bank_name or '',
                            'bank_id':employee.bank_account_id and employee.bank_account_id.bank_bic or '',
                            'branch_id':employee.bank_account_id and employee.bank_account_id.branch_id or '',
                            'employee_id':employee and employee.user_id and employee.user_id.login or ' ',
                            'employee_name':employee.name,
                            'account_number':employee.bank_account_id and employee.bank_account_id.acc_number or '',
                            'amount':net}
            department_total_amount += net
            if 'Undefined' in result:
                result.get('Undefined').append(payslip_data)
            else:
                result.update({'Undefined': [payslip_data]})

            print "result >>>>>>>> \n\n\n",result

        department_total = {'total': float(department_total_amount), 'department_name': 'Total Undefined'}
        if 'Undefined' in department_info:
            department_info.get('Undefined').append(department_total)
        else:
            department_info.update({'Undefined': [department_total]})
        
        for hr_department_rec in self.env['hr.department'].search([]):
            employee_ids = employee_obj.search([('bank_account_id', '!=', False), 
                                                ('id', 'in', data.get('employee_ids')), 
                                                ('department_id', '=', hr_department_rec.id)])
            department_total_amount = 0.0
            new_employee_ids = []
            new_employee_rec = []
            if employee_ids and employee_ids.ids:
                bank_rec = bank_obj.search([('bank_emp_id', 'in', employee_ids.ids)], order="bank_name, bank_code, branch_code")
                for bank in bank_rec:
                    if bank.bank_emp_id.id not in new_employee_ids:
                        new_employee_ids.append(bank.bank_emp_id.id)
                new_employee_rec += list(set(employee_ids.ids).difference(set(new_employee_ids)))
            for employee in employee_obj.browse(new_employee_rec):
                payslip_ids = payslip_obj.search([('date_from', '>=', date_from), 
                                                  ('date_from','<=',date_to),
                                                  ('employee_id', '=' , employee.id), 
                                                  ('pay_by_cheque','=',False), 
                                                  ('state', 'in', ['draft', 'done', 'verify'])])
                net = 0.0
                if not payslip_ids:
                    continue
                for payslip in payslip_ids:
                    for line in payslip.line_ids:
                        if line.code == 'NET':
                            net += line.total
                payslip_data = {
                            'bank_name':employee.bank_account_id and employee.bank_account_id.bank_name or '',
                            'bank_id':employee.bank_account_id and employee.bank_account_id.acc_number or '',
                            'branch_id':employee.bank_account_id and employee.bank_account_id.branch_id or '',
                            'employee_id':employee and employee.user_id and employee.user_id.login or ' ',
                            'employee_name':employee.name or '',
                            'account_number':employee.bank_account_id and employee.bank_account_id.acc_number or '',
                            'amount':net or 0.0}



                department_total_amount += net
                if hr_department_rec.id in result:
                    result.get(hr_department_rec.id).append(payslip_data)
                else:
                    result.update({hr_department_rec.id: [payslip_data]})
            department_total = {'total': float(department_total_amount), 'department_name': "Total " + hr_department_rec.name}
            if hr_department_rec.id in department_info:
                department_info.get(hr_department_rec.id).append(department_total)
            else:
                department_info.update({hr_department_rec.id: [department_total]})

        for key, val in result.items():
            final_result[key] = {'lines': val, 'departmane_total': department_info[key] }

        print "final_result >>>>>>>> \n\n\n",final_result

        return final_result.values()
    
    @api.model
    def get_total(self, data):
        date_from = data.get('start_date') or False
        date_to = data.get('end_date') or False
        employee_ids = self.env['hr.employee'].search([('bank_account_id','!=',False), 
                                                       ('id', 'in', data.get('employee_ids'))])
        total_ammount = 0.0
        payslip_ids = self.env['hr.payslip'].search([('date_from', '>=', date_from),
                                                     ('date_from','<=',date_to),
                                                     ('pay_by_cheque','=',False),
                                                     ('employee_id', 'in' , employee_ids.ids), 
                                                     ('state', 'in', ['draft', 'done', 'verify'])])
        if payslip_ids:
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code == 'NET':
                        total_ammount += line.total
        return total_ammount
    
    @api.model
    def get_totalrecord(self, data):
        date_from = data.get('start_date') or False
        date_to = data.get('end_date') or False
        emp_list = []
        employee_ids = self.env['hr.employee'].search([('bank_account_id','!=',False),
                                                       ('id', 'in', data.get('employee_ids'))])
        for employee in employee_ids:
            payslip_ids = self.env['hr.payslip'].search([('date_from', '>=', date_from), 
                                                         ('date_from','<=',date_to),
                                                         ('employee_id', '=' , employee.name), 
                                                         ('pay_by_cheque','=',False), 
                                                         ('state', 'in', ['draft', 'done', 'verify'])])
            if payslip_ids:
                emp_list.append(employee.id)
        return len(emp_list)

    @api.multi
    def render_html(self, docids,data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        data = docs.read([])[0]

        # print "!data >>>>> \n\n\n", data

        report_lines = self.get_info(data)

        # print "!report_lines >>>>> \n\n\n",report_lines

        total_employees = self.get_totalrecord(data)
        total = self.get_total(data)
        docargs = {'doc_ids' : self.ids,
                   'doc_model' : self.model,
                   'data' : data,
                   'docs' : docs,
                   'time' : time,
                   'get_info' : report_lines,
                   'get_totalrecord' : total_employees,
                   'get_total' : total}
        return self.env['report'].render('sg_hr_report.hr_bank_summary_report_tmp', docargs)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: