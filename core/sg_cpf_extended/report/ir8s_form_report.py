# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
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
import datetime
from odoo import tools
from time import strftime
from odoo import api, models, _
from odoo.tools.misc import formatLang
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ir8s_form(models.AbstractModel):
    _name = "report.sg_income_tax_report.ir8s_incometax_form_report"

    @api.multi
    def get_data(self, form):
        vals = []
        user_obj = self.env['res.users']
        start_date = form.get('start_date', False) or False
        end_date = form.get('end_date', False) or False
        wiz_start_date = form.get('start_date', False) or False
        wiz_end_date = form.get('end_date', False) or False
        if start_date and end_date:
            year = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).year
            start_year = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).year - 1
            end_year = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT).year - 1
            start_date = '%s-01-01' % tools.ustr(int(start_year))
            end_date = '%s-12-31' % tools.ustr(int(end_year))
#            wiz_start_date = '%s-01-01' % tools.ustr(int(start_year))
#            wiz_end_date = '%s-12-31' % tools.ustr(int(end_year))
            start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
            previous_year = start_year
        contract_rec = self.env['hr.contract'].search([('employee_id', 'in', form.get('employee_ids'))])
        for contract in contract_rec:
            income_tax_rec = self.env['hr.contract.income.tax'].search([ ('contract_id', '=', contract.id),
                                                                        ('start_date', '>=', wiz_start_date),
                                                                        ('end_date', '<=', wiz_end_date)])
            for contract_income_tax in income_tax_rec:
                res = {}
                birthday = cessation_date = ''
                if contract.employee_id.birthday:
                    birthday = datetime.datetime.strptime(contract.employee_id.birthday, DEFAULT_SERVER_DATE_FORMAT)
                    birthday = birthday.strftime('%d/%m/%Y')
                if contract.employee_id.cessation_date:
                    cessation_date = datetime.datetime.strptime(contract.employee_id.cessation_date, DEFAULT_SERVER_DATE_FORMAT)
                    cessation_date = cessation_date.strftime('%d/%m/%Y')
                employee_rec = self.env['hr.employee'].search([('user_id', '=', int(form.get('payroll_user')))])
                emp_designation = ''
                payroll_admin_user_name = user_obj.browse(int(form.get('payroll_user'))).name
                signature = user_obj.browse(int(form.get('payroll_user'))).signature
                for emp in employee_rec:
                    emp_designation = emp.job_id.name
                res['emp_designation'] = emp_designation
                res['signature'] = signature
                res['payroll_admin_user_name'] = payroll_admin_user_name
                cpf_data = {}
                for income_tax_rec in contract_income_tax:
                    months = [1,2,3,4,5,6,7,8,9,10,11,12]
                    payslip_rec = self.env['hr.payslip'].search([('date_from', '>=', start_date),
                                                                 ('date_from', '<=', end_date),
                                                                 ('employee_id', '=', contract.employee_id.id),
                                                                 ('state', 'in', ['draft', 'done', 'verify'])])
                    for payslip in payslip_rec:
                        payslip_month = ''
                        payslip_dt = datetime.datetime.strptime(payslip.date_from, DEFAULT_SERVER_DATE_FORMAT)
                        payslip_month = payslip_dt.strftime('%m')
#                         added new features
                        ow_wages = aw_wages = ow_empyr_amt = ow_emp_amt = temp_aw = temp_ow = aw_empyr_amt = aw_emp_amt = 0
                        obj_rule = self.env['hr.salary.rule']
                        ow_ids = obj_rule.search([('is_cpf', '=', 'ow')])
                        aw_ids = obj_rule.search([('is_cpf', '=', 'aw')])
                        for line in payslip.line_ids:
                            if line.salary_rule_id.is_cpf == 'ow':
                                ow_wages += line.total
                            if line.salary_rule_id.is_cpf == 'aw':
                                aw_wages += line.total
                            if line.code == 'CPFEE_SPR_SIN_OW':
                                temp_ow = line.total
                            if line.code == 'CPFEE_SPR_SIN_AW':
                                temp_aw = line.total
                            if line.code == 'CPFEE_SPR_SIN_OW_EMP':
                                ow_emp_amt = line.total
                                ow_empyr_amt = temp_ow - line.total
                            if line.code == 'CPFEE_SPR_SIN_AW_EMP':
                                aw_emp_amt = line.total
                                aw_empyr_amt = temp_aw - line.total
                        cpf_data.update({payslip_dt.month : [ow_wages, ow_empyr_amt,
                                                             ow_emp_amt, aw_wages,
                                                             aw_empyr_amt, aw_emp_amt]})
                        if payslip_dt.month in months:
                            months.remove(payslip_dt.month)
                    for rest_mnth in months:
                        cpf_data.update({rest_mnth : [0.0, 0.0,
                                                      0.0, 0.0,
                                                      0.0, 0.0]})
                    res['cpf_data'] = cpf_data
                    res['emp_name'] = contract.employee_id.name
                    res['identification_id'] = contract.employee_id.identification_id
                    res['work_phone'] = contract.employee_id.work_phone
                    res['birthday'] = birthday
                    res['cessation_date'] = cessation_date
                    res['eyer_contibution'] = formatLang(self.env, income_tax_rec.eyer_contibution)
                    res['eyee_contibution'] = formatLang(self.env, income_tax_rec.eyee_contibution)
                    res['additional_wage'] = formatLang(self.env, income_tax_rec.additional_wage)
                    res['add_wage_pay_date'] = income_tax_rec.add_wage_pay_date
                    res['refund_eyers_contribution'] = formatLang(self.env, income_tax_rec.refund_eyers_contribution)
                    res['refund_eyees_contribution'] = formatLang(self.env, income_tax_rec.refund_eyees_contribution)
                    res['refund_eyers_date'] = income_tax_rec.refund_eyers_date
                    res['refund_eyees_date'] = income_tax_rec.refund_eyees_date
                    res['refund_eyers_interest_contribution'] = formatLang(self.env, income_tax_rec.refund_eyers_interest_contribution)
                    res['refund_eyees_interest_contribution'] = formatLang(self.env, income_tax_rec.refund_eyees_interest_contribution)
                    res['date_today'] = datetime.date.today()
                    res['previous_year'] = previous_year
                    res['year'] = year
                vals.append(res)
        return vals

    @api.multi
    def render_html(self,docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        datas = docs.read([])[0]
        report_lines = self.get_data(datas)
        docargs = {'doc_ids': self.ids,
                   'doc_model': self.model,
                   'data': datas,
                   'docs': docs,
                   'time': time,
                   'get_data' : report_lines}
        return self.env['report'].render('sg_income_tax_report.ir8s_incometax_form_report', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: