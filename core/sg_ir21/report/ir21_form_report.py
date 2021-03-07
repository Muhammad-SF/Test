# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-2012 Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
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
from odoo import models, fields, api
from odoo import tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import datetime
import time
# from boto.mws.connection import dependent

class ir21_form(models.AbstractModel):
    _name = 'report.sg_ir21.report_form_ir21'
    
    def format_date(self, convert_date):
        if convert_date:
            return datetime.datetime.strftime(datetime.datetime.strptime(convert_date, DEFAULT_SERVER_DATE_FORMAT), '%d-%m-%Y')
        return ''
    
    @api.multi
    def get_data(self, form):
        employee_obj = self.env['hr.employee']
        payslip_obj = self.env['hr.payslip']
        contract_income_tax_obj = self.env['hr.contract.income.tax']
        from_date = to_date = start_date = end_date = prev_yr_start_date = prev_yr_end_date = False
        if form.get('start_date', False) and form.get('end_date', False):
            from_date = datetime.datetime.strptime(form.get('start_date', False), DEFAULT_SERVER_DATE_FORMAT)
            to_date = datetime.datetime.strptime(form.get('end_date', False), DEFAULT_SERVER_DATE_FORMAT)
            fiscal_start = from_date.year - 1
            fiscal_end = to_date.year - 1
            start_date = '%s-01-01' % tools.ustr(int(fiscal_start))
            end_date = '%s-12-31' % tools.ustr(int(fiscal_end))
            start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
            prev_yr_start = from_date.year - 1
            prev_yr_end = to_date.year - 1
            prev_yr_start_date = '%s-01-01' % tools.ustr(int(prev_yr_start))
            prev_yr_end_date = '%s-12-31' % tools.ustr(int(prev_yr_end))
            prev_yr_start_date = datetime.datetime.strptime(prev_yr_start_date, DEFAULT_SERVER_DATE_FORMAT)
            prev_yr_end_date = datetime.datetime.strptime(prev_yr_end_date, DEFAULT_SERVER_DATE_FORMAT)
            
        vals = []
        emp_ids = employee_obj.search([('id', 'in', form.get('employee_ids'))])
        for employee in emp_ids:
            res = {}
            depend = []
            child = {'child_name':'', 'child_gender':'', 'birth_date':''}
            contract_ids = self.env['hr.contract'].search([
                                               ('employee_id', '=', employee.id),
                                              ])
            
            payslip_id = self.env['hr.payslip'].search([
                                               ('employee_id', '=', employee.id),
                                               ('date_from', '>=', from_date),
                                               ('date_to', '<=', to_date),
                                               ('state', 'in', ['done'])], order='create_date desc', limit=1)
            if payslip_id:
                res['date_last_salary'] = payslip_id.date
                res['salary_period'] = payslip_id.date_from + ' To ' + payslip_id.date_to
                for line_ids in payslip_id.line_ids:
                    if line_ids.code == 'GROSS':
                        res['last_salary'] = line_ids.amount
            
                    
            res['name'] = employee.name or  ''
            res['nationality'] = employee.country_id and employee.country_id.name or ''
            res['birthday'] = self.format_date(employee.birthday)
            res['gender'] = employee.gender or ''
            res['nric_no'] = employee.nric_no or ''
            res['fin_no'] = employee.fin_no or ''
            res['country_id'] = employee.country_id or ''
            res['marital'] = employee.marital or ''
            res['mobile_phone'] = employee.mobile_phone or ''
            res['work_email'] = employee.work_email or ''
            res['app_date'] = self.format_date(employee.app_date)
            res['join_date'] = self.format_date(employee.join_date)
            res['cessation_date'] = self.format_date(employee.cessation_date)
            res['last_date'] = self.format_date(employee.last_date)
            res['comp_house_no'] = employee.company_id.house_no or ''
            res['comp_unit_no'] = employee.company_id.unit_no or ''
#             res['spouse_name'] = employee.spouse_name or ''
#             res['spouse_dob'] = employee.spouse_dob or ''
#             res['spouse_ident'] = employee.spouse_ident_no or ''
#             res['spouse_nationality'] = employee.spouse_nationality.name or ''
            res['marriage_date'] = self.format_date(employee.marriage_date)
            res['bank_name'] = employee.bank_account_id.bank_id.name or ''
            res['house_no'] = employee.address_home_id.house_no or ''
            res['street'] = employee.address_home_id.street or ''
            res['street2'] = employee.address_home_id.street2 or ''
            res['designation'] = employee.job_id.name or ''
            res['company_name'] = employee.company_id.name or ''
            res['company_tax'] = employee.company_id.vat or ''
            res['cmp_street'] = employee.address_id.street or ''
            res['cmp_street2'] = employee.address_id.street2 or ''
            res['sin_postal_code'] = employee.empnationality_id.name or ''
            child_list = []
            spouse_name = ''
            spouse_dob = ''
            spouse_nationality = ''
            spouse_ident = ''
            for dependent in employee.dependent_ids:
                child = {}
                if dependent.relation_ship == 'son' or dependent.relation_ship == 'daughter':
                    child['child_name'] = (dependent.first_name or '') + ' ' + (dependent.last_name or ' ')
                    child['child_gender'] = dependent.gender
                    child['birth_date'] = self.format_date(dependent.birth_date)
                if dependent.relation_ship == 'wife' or dependent.relation_ship == 'husband':
                    spouse_name = (dependent.first_name or '') + ' ' + (dependent.last_name or '')
                    spouse_dob = dependent.birth_date
                    spouse_nationality = dependent.nationality and dependent.nationality.name or ''
                    spouse_ident = dependent.identification_number or ''
                child_list.append(child)
            res['spouse_name'] = spouse_name
            res['spouse_dob'] = self.format_date(spouse_dob)
            res['spouse_ident'] = spouse_ident
            res['spouse_nationality'] = spouse_nationality
            print 'ffffffffffffffffffffffffffffffff', child_list
            res['child'] = child_list
            for history in employee.history_ids:
                res['cessation_date'] = self.format_date(history.cessation_date)
            for contract_id in contract_ids:
                income_ids = contract_income_tax_obj.search([('contract_id', '=', contract_id.id),
                                                        ('start_date', '>=', from_date),
                                                        ('end_date', '<=', to_date),
                                                ], limit=1)
                if income_ids:
                    for income in income_ids:
                        prev_income_tax_rec = income.search([('start_date', '>=', prev_yr_start_date),
                                                                    ('end_date', '<=', prev_yr_end_date)])
                        prev_allowances = prev_income_tax_rec.entertainment_allowance + prev_income_tax_rec.other_allowance + prev_income_tax_rec.pension
                        prev_sub_total = int(prev_allowances) + int(prev_income_tax_rec.gross_commission) + int(prev_income_tax_rec.gratuity_payment_amt) + \
                        int(prev_income_tax_rec.compensation_loss_office) + int(prev_income_tax_rec.retirement_benifit_up) + int(prev_income_tax_rec.contribution_employer) + \
                        int(prev_income_tax_rec.excess_voluntary_contribution_cpf_employer)
#                        prev_sub_total = int(prev_income_tax_rec.gratuity_payment_amt) + int(prev_income_tax_rec.retirement_benifit_up) + prev_income_tax_rec.contribution_employer + prev_income_tax_rec.excess_voluntary_contribution_cpf_employer
                        prev_total = int(prev_income_tax_rec.director_fee) + int(prev_income_tax_rec.payslip_net_amount) + prev_sub_total
                        res['pre_dir_fees'] = prev_income_tax_rec.director_fee
                        res['prev_allowance'] = int(prev_allowances) or 0.0
                        res['prev_gratuity_payment_amt'] = prev_income_tax_rec.gratuity_payment_amt
                        res['prev_retirement_benifit_up'] = prev_income_tax_rec.retirement_benifit_up
                        res['prev_contribution_employer'] = prev_income_tax_rec.contribution_employer
                        res['prev_compensation_loss_office'] = prev_income_tax_rec.compensation_loss_office
                        res['prev_excess_voluntary_contribution_cpf_employer'] = prev_income_tax_rec.excess_voluntary_contribution_cpf_employer
                        res['prev_donation'] = prev_income_tax_rec.donation
                        res['prev_start_date'] = self.format_date(prev_income_tax_rec.start_date)
                        res['prev_end_date'] = self.format_date(prev_income_tax_rec.end_date)
                        res['prev_gross'] = prev_income_tax_rec.payslip_net_amount or 0.0
                        res['prev_employee_income_tax'] = prev_income_tax_rec.employee_income_tax
                        res['prev_gross_commission'] = prev_income_tax_rec.gross_commission or 0.0
                        res['prev_sub_total'] = int(prev_sub_total) or 0.0
                        res['prev_total'] = int(prev_total) or 0.0
                        allowances = income.entertainment_allowance + income.other_allowance + income.pension
                        sub_total = int(allowances) + int(income.gross_commission) + int(income.gratuity_payment_amt) + int(income.compensation_loss_office) + \
                        int(income.retirement_benifit_up) + int(income.contribution_employer) + int(income.excess_voluntary_contribution_cpf_employer)
                        total = int(income.director_fee) + int(income.payslip_net_amount) + sub_total
                        res['director_fee'] = income.director_fee
                        res['allowance'] = int(allowances) or 0.0
                        res['gratuity_payment_amt'] = income.gratuity_payment_amt
                        res['compensation_loss_office'] = income.compensation_loss_office
                        res['fund_name'] = income.fund_name
                        res['retirement_benifit_up'] = income.retirement_benifit_up
                        res['retirement_benifit_from'] = income.retirement_benifit_from
                        res['contribution_employer'] = income.contribution_employer
                        res['excess_voluntary_contribution_cpf_employer'] = income.excess_voluntary_contribution_cpf_employer
                        res['donation'] = income.donation
                        res['employee_income_tax'] = income.employee_income_tax
                        res['start_date'] = self.format_date(income.start_date)
                        res['end_date'] = self.format_date(income.end_date)
                        res['sub_total'] = int(sub_total) or 0.0
                        res['total'] = int(total) or 0.0
                        res['current_gross'] = income.payslip_net_amount or 0.0
                        res['curr_gross_commission'] = income.gross_commission or 0.0
                        res['compensation'] = income.compensation or ''
            vals.append(res)
        return vals
    
    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        datas = docs.read([])
        report_lines = self.get_data(datas[0])
        docargs = {
                   'doc_ids': self.ids,
                   'doc_model': self.model,
                   'data': datas,
                   'docs': docs,
                   'get_data' : report_lines
        }
        return self.env['report'].render('sg_ir21.report_form_ir21', docargs)

