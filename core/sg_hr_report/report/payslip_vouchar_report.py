# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
#    Copyright (C) 2012 OpenERP SA (<http://www.serpentcs.com>)
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

class payslip_report(models.AbstractModel):
    _name = 'report.sg_hr_report.report_payslip_sample'
    
    @api.model
    def get_category(self, curr_id, code):
        res = {}
        self.tot_a = 0.0
        basic_pay = overtime_hour = overtime_pay = total = 0.0
        pay_slip_line_ids = self.env['hr.payslip.line'].search([('slip_id', '=', curr_id.id)])
        for rec in pay_slip_line_ids:
            if rec.code == 'SC100':
                basic_pay = rec.total
            if rec.code == 'BASIC':
                basic_pay = rec.total
            if rec.code == 'SC102':
                input_code = []
                hr_sal_rule_rec = self.env['hr.salary.rule'].search([('code', '=', code)])
                input_ids_code = [inp_ids.code for inp_ids in hr_sal_rule_rec.input_ids]
                set_input_code = (list(set(input_ids_code)))
                input_code = [list_rec.encode('UTF8') for list_rec in set_input_code]
                payslip_input_ids = self.env['hr.payslip.input'].search([('payslip_id', '=', curr_id.id),
                                                                         ('code', 'in', input_code)])
                tot_amount_list = [payslip_input_rec.amount for payslip_input_rec in payslip_input_ids]
                overtime_hour = sum(tot_amount_list)
            if rec.code == 'SC102':
                overtime_pay = rec.total
        res.update({'basic_pay':basic_pay,
                    'overtime_hour':curr_id.overtime_hours,
                    'overtime_pay':overtime_pay, })
        self.tot_a = basic_pay
        return res


    @api.model
    def category_total_employr(self, curr_ids, CAT_CPF_EMPLOYER, CATCPFAGENCYSERVICESER):
        total = 0.0
        if CAT_CPF_EMPLOYER:
            total += self.category_line(curr_ids, CAT_CPF_EMPLOYER, None, 'Total')
        if CATCPFAGENCYSERVICESER:
            total += self.category_line(curr_ids, CATCPFAGENCYSERVICESER, None, 'Total')
        return total

    @api.model
    def category_total(self, curr_ids, DED, CAT_CPF_EMPLOYEE, CATCPFAGENCYSERVICESEE, DED_INCL_CPF):
        total = 0.0
        if DED:
            total += self.category_line(curr_ids, DED, None, 'Total')
        if CAT_CPF_EMPLOYEE:
            total += self.category_line(curr_ids, CAT_CPF_EMPLOYEE, None, 'Total')
        if CATCPFAGENCYSERVICESEE:
            total += self.category_line(curr_ids, CATCPFAGENCYSERVICESEE, None, 'Total')
        if DED_INCL_CPF:
            total += self.category_line(curr_ids, DED_INCL_CPF, None, 'Total')
        return total

    @api.model
    def category_line(self, curr_ids, code, overtime_code, code_tittle):
        res = []
        line_dict = {}
        total_allowances = total_deduction = 0.0
        hr_sal_rule_categ_ids = self.env['hr.salary.rule.category'].search([('code', '=', code)])
        hr_sal_rule_ids = self.env['hr.salary.rule'].search([('category_id', 'in', hr_sal_rule_categ_ids.ids)])
        if hr_sal_rule_ids:
            sal_rule_code = [sal_rule_rec.code for sal_rule_rec in hr_sal_rule_ids if sal_rule_rec.code != overtime_code and sal_rule_rec.code != False]
            sal_rule_code_list = [code_rec.encode('UTF8') for code_rec in sal_rule_code]
            if sal_rule_code_list:
                payslip_line_rec = self.env['hr.payslip.line'].search([('slip_id', '=', curr_ids.id),
                                                                    ('code', 'in', sal_rule_code_list)])
                for line_rec in payslip_line_rec:
                    line_dict = ({'name':line_rec.name,
                                 'total':line_rec.total,
                                 'code':line_rec.code})
                    res.append(line_dict)
                    total_allowances += line_rec.total
        if code_tittle == 'Total':
            rec = self.total_allowances(total_allowances)
            return rec
        return res
    
    @api.model
    def total_allowances(self, total_amount):
        return total_amount
    
    @api.model
    def blank_line(self, line_key):
        line_list = []
        if line_key == 'deduction_line':
            for line in range(1, 3):
                line_list.append(line)
        return line_list
    
    @api.model
    def blank_fix_line(self, len_fetch_line):
        fix_line_list = []
        remain_line = 4 - len_fetch_line
        for line_rec in range(1, remain_line + 1):
            fix_line_list.append(line_rec)
        return fix_line_list
    
    @api.model
    def additional_blank_fix_line(self, add_line, len_fetch_line):
        fix_line_list = []
        remain_line = len_fetch_line - 2 - add_line - 3
        for line_rec in range(1, remain_line):
            fix_line_list.append(line_rec)
        return fix_line_list
    
    @api.multi
    def get_worked_hour(self,data):
        amt = 0.0
        if data.input_line_ids:
            for line in data.input_line_ids:
                if line.code =="SC100I":
                    amt = line.amount
        return amt
    
    @api.multi
    def render_html(self,docids, data=None):
        self.model=self.env.context.get('active_model')
        docs = self.env['hr.payslip'].browse(docids)
        datas=docs.read(docs)
        docargs = {'doc_ids': self.ids,
                   'doc_model': self.model,
                   'docs': docs,
                   'time' : time,
                   'get_category' : self.get_category,
                   'category_line' : self.category_line,
                   'category_total' : self.category_total,
                   'category_total_employr':self.category_total_employr,
                   'total_allowances' : self.total_allowances,
                   'blank_line' : self.blank_line,
                   'blank_fix_line' : self.blank_fix_line,
                   'get_worked_hour':self.get_worked_hour,
                   'additional_blank_fix_line' : self.additional_blank_fix_line
                   }
        return self.env['report'].render('sg_hr_report.report_payslip_sample', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: