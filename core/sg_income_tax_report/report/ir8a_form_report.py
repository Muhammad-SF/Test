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
from odoo import api, models, _
import time
from odoo.tools.misc import formatLang
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import tools
import lxml.html
from odoo.exceptions import ValidationError
import datetime

class ir8a_form(models.AbstractModel):
    _name = "report.sg_income_tax_report.ir8a_incometax_form_report"

    @api.multi
    def get_data(self, form):
        employee_obj = self.env['hr.employee']
        from_date = to_date = start_date = end_date = prev_yr_start_date = prev_yr_end_date = False

        if form.get('start_date', False) and form.get('end_date', False):
            from_date = datetime.datetime.strptime(form.get('start_date', False), DEFAULT_SERVER_DATE_FORMAT)
            to_date = datetime.datetime.strptime(form.get('end_date', False), DEFAULT_SERVER_DATE_FORMAT)
            fiscal_start = from_date.year - 1
            fiscal_start_date = '%s0101' % tools.ustr(int(fiscal_start))
            fiscal_end = to_date.year - 1
            fiscal_end_date = '%s1231' % tools.ustr(int(fiscal_end))
            start_date = '%s-01-01' % tools.ustr(int(fiscal_start))
            end_date = '%s-12-31' % tools.ustr(int(fiscal_end))
            start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)

######################## UNUSED CODE #################################
#             prev_yr_start = from_date.year - 2
#             prev_yr_end = to_date.year - 2
#             prev_yr_start_date = '%s-01-01' % tools.ustr(int(prev_yr_start))
#             prev_yr_end_date = '%s-12-31' % tools.ustr(int(prev_yr_end))
#             prev_yr_start_date = datetime.datetime.strptime(prev_yr_start_date, DEFAULT_SERVER_DATE_FORMAT)
#             prev_yr_end_date = datetime.datetime.strptime(prev_yr_end_date, DEFAULT_SERVER_DATE_FORMAT)
#####################################################################
######################## UNUSED CODE #################################
#         batchdate = datetime.datetime.strptime(form.get('batch_date', False), DEFAULT_SERVER_DATE_FORMAT)
#         batchdate = batchdate.strftime('%Y%m%d')
####################################################################

        previous_year = from_date.year - 1
        total_detail_record = 0
        vals = []
        emp_ids = employee_obj.search([('id', 'in', form.get('employee_ids'))], order = 'name ASC')
        for employee in emp_ids:
            res = {}
            contract_ids = self.env['hr.contract'].search([('employee_id', '=', employee.id)])
            income_tax_rec = self.env['hr.contract.income.tax'].search([('contract_id', 'in', contract_ids.ids),
                                                                        ('start_date', '>=', from_date),
                                                                        ('end_date', '<=', to_date)], limit=1)

            if not income_tax_rec.ids:
                raise ValidationError(_('No Income Tax Record found for Selected Dates'))
            for contract_income_tax_rec in income_tax_rec:
                total_detail_record += 1
                sex = birthday = join_date = cessation_date = bonus_declare_date = approve_director_fee_date = fromdate = todate = approval_date = ''
                res['employee'] = employee.name
                if employee.gender == 'male':
                    sex = 'M'
                if employee.gender == 'female':
                    sex = 'F'
                if employee.birthday:
                    birthday = datetime.datetime.strptime(employee.birthday, DEFAULT_SERVER_DATE_FORMAT)
                    birthday = birthday.strftime('%Y-%m-%d')
                if employee.join_date:
                    join_date = datetime.datetime.strptime(employee.join_date, DEFAULT_SERVER_DATE_FORMAT)
                    join_date = join_date.strftime('%Y-%m-%d')
                if contract_income_tax_rec.contract_id.date_end:
                    cessation_date = datetime.datetime.strptime(contract_income_tax_rec.contract_id.date_end, DEFAULT_SERVER_DATE_FORMAT)
                    cessation_date = cessation_date.strftime('%Y-%m-%d')
                if contract_income_tax_rec.bonus_declaration_date:
                    bonus_declare_date = datetime.datetime.strptime(contract_income_tax_rec.bonus_declaration_date, DEFAULT_SERVER_DATE_FORMAT)
                    bonus_declare_date = bonus_declare_date.strftime('%Y-%m-%d')
                if contract_income_tax_rec.director_fee_approval_date:
                    approve_director_fee_date = datetime.datetime.strptime(contract_income_tax_rec.director_fee_approval_date, DEFAULT_SERVER_DATE_FORMAT)
                    approve_director_fee_date = approve_director_fee_date.strftime('%Y-%m-%d')
                if contract_income_tax_rec.fromdate:
                    fromdate = datetime.datetime.strptime(contract_income_tax_rec.fromdate, DEFAULT_SERVER_DATE_FORMAT)
                    fromdate = fromdate.strftime('%Y-%m-%d')
                if contract_income_tax_rec.todate:
                    todate = datetime.datetime.strptime(contract_income_tax_rec.todate, DEFAULT_SERVER_DATE_FORMAT)
                    todate = todate.strftime('%Y-%m-%d')
                if contract_income_tax_rec.approval_date:
                    approval_date = datetime.datetime.strptime(contract_income_tax_rec.approval_date, DEFAULT_SERVER_DATE_FORMAT)
                    approval_date = approval_date.strftime('%Y-%m-%d')
                transport_allowance = other_allowance = other_data = donation_amt = bonus_amt = gross_amt = gross_commission = 0

#                 salary_amt = amount_data = mbf_amt = catemp_amt = net_amt = prv_yr_gross_amt = 0
######################## UNUSED CODE #################################
#                if emp.mbf:
#                    mbf_amt += emp.mbf
#                 prev_yr_payslip_ids = payslip_obj.search([('date_from', '>=', prev_yr_start_date),
#                                                          ('date_from', '<=', prev_yr_end_date),
#                                                          ('employee_id', '=', employee.id),
#                                                          ('state', 'in', ['draft','done', 'verify'])])
#                 for payslip in prev_yr_payslip_ids:
#                     for line in payslip.line_ids:
#                         if line.code == 'GROSS':
#                             prv_yr_gross_amt += line.total
#####################################################################

                payslip_ids = self.env['hr.payslip'].search([('date_from', '>=', start_date),
                                                             ('date_from', '<=', end_date),
                                                             ('employee_id', '=', employee.id),
                                                             ('state', 'in', ['draft','done', 'verify'])])
                for payslip in payslip_ids:
                    fromdate = datetime.datetime.strptime(payslip.date_from, DEFAULT_SERVER_DATE_FORMAT)
                    todate = datetime.datetime.strptime(payslip.date_to, DEFAULT_SERVER_DATE_FORMAT)
                    fromdate = fromdate.strftime('%Y')
                    todate = todate.strftime('%Y')
                    
######################## UNUSED CODE #################################
#                     basic_flag = False
#                     for line in payslip.line_ids:
#                         if line.code == 'BASIC':
#                             basic_flag = True
#                     if basic_flag and contract_income_tax_rec.contract_id.wage:
#                         salary_amt += contract_income_tax_rec.contract_id.wage
#########################################################

                    for line in payslip.line_ids:
                        if line.code in ['CPFSINDA', 'CPFCDAC', 'CPFECF']:
                            donation_amt += line.total
                        if line.code == 'TA':
                            transport_allowance += line.total
                        if line.code == 'SC121':
                            bonus_amt += line.total
                        if line.category_id.code == 'GROSS':
#                            salary_amt += line.amount
                            gross_amt += line.total
                        if line.code in ['SC102', 'SC103']:
                            gross_amt += line.total
                        if line.code in ['SC104', 'SC105']:
#                             salary_amt -= line.total
                            gross_commission += line.total
                        if line.category_id.code == 'ALW' and line.code != 'TA':
                            other_allowance += line.total

######################## UNUSED CODE #################################

#                         if not contract_income_tax_rec.contract_id.wage and contract_income_tax_rec.contract_id.rate_per_hour and line.code == 'SC100':
#                             salary_amt += line.total
#                         if line.code == 'CPFMBMF':
#                             mbf_amt += line.total
#                         if line.category_id.code == 'CAT_CPF_EMPLOYEE':
#                             catemp_amt += line.total
#                         if line.code == 'NET':
#                             net_amt += line.total
#                             salary_amt -= line.total
#                         if line.category_id.code in ['ADD', 'ALW'] and line.code not in ['SC102', 'SC103'] and line.code not in ['TA']:
#                            other_data += line.amount
#                             salary_amt += line.total
#                         if line.code in ['SC200', 'SC206']:
#                             salary_amt -= line.total
#                 mbf_amt = mbf_amt
#                 catemp_amt = catemp_amt
#                 net_amt = net_amt

#                 gain_profit = exempt_income = 0
#                 gain_profit = contract_income_tax_rec.gain_profit
#                 exempt_income = contract_income_tax_rec.exempt_income
#                 employment_income = contract_income_tax_rec.employment_income
#                 prv_yr_gross_amt = prv_yr_gross_amt
#########################################################

                bonus_amt = bonus_amt
                insurance = director_fee = benifits_in_kinds = gains_profit_share_option = excess_voluntary_contribution_cpf_employer = contribution_employer = retirement_benifit_from = retirement_benifit_up = compensation_loss_office = gratuity_payment_amt = entertainment_allowance = pension = lum_sum_total = 0
                insurance = contract_income_tax_rec.insurance
                director_fee = contract_income_tax_rec.director_fee
                pension = contract_income_tax_rec.pension or 0.0
                entertainment_allowance = contract_income_tax_rec.entertainment_allowance
                gratuity_payment_amt = contract_income_tax_rec.gratuity_payment_amt * 1
                notice_pay_amt = contract_income_tax_rec.notice_pay * 1
                ex_gratia_amt = contract_income_tax_rec.ex_gratia * 1
                others_amt = contract_income_tax_rec.others * 1
                compensation_loss_office = contract_income_tax_rec.compensation_loss_office
                retirement_benifit_up = contract_income_tax_rec.retirement_benifit_up
                retirement_benifit_from = contract_income_tax_rec.retirement_benifit_from
                contribution_employer = contract_income_tax_rec.contribution_employer
                excess_voluntary_contribution_cpf_employer = contract_income_tax_rec.excess_voluntary_contribution_cpf_employer
                CPF_designated_pension_provident_fund = contract_income_tax_rec.CPF_designated_pension_provident_fund
                gains_profit_share_option = contract_income_tax_rec.gains_profit_share_option
                benifits_in_kinds = contract_income_tax_rec.benifits_in_kinds
                transport_allowance = entertainment_allowance = 0.00
                lum_sum_total = compensation_loss_office + gratuity_payment_amt + notice_pay_amt + ex_gratia_amt + others_amt
                total_d_2 = (transport_allowance) + (entertainment_allowance) + (other_allowance)
                other_data += total_d_2 + gross_commission + pension + lum_sum_total + retirement_benifit_from + contribution_employer + excess_voluntary_contribution_cpf_employer + gains_profit_share_option + benifits_in_kinds
######################## UNUSED CODE #################################

#                other_data = (int(gross_commission) or 0) + (int(emp.pension) or 0) + (int(transport_allowance) or 0) + \
#                                (int(entertainment_allowance) or 0) + (int(other_allowance) or 0) + \
#                                (int(emp.retirement_benifit_from) or 0) + (int(emp.contribution_employer) or 0) + \
#                                (int(emp.excess_voluntary_contribution_cpf_employer) or 0) + (int(emp.gains_profit_share_option) or 0) + \
#                                (int(emp.benifits_in_kinds) or 0)
#                 amount_data = other_data + int(net_amt) + int(contract_income_tax_rec.director_fee) + int(bonus_amt)
#                if not employee.gender:
#                    raise osv.except_osv(_('Error'), _('There is no gender define for %s employee.' % (employee.name) ))
#                if not employee.gender:
#                    raise ValidationError(_('There is no gender define for %s employee.' % (employee.name) ))
#                 payment_period_form_date = fiscal_start_date
#                 payment_period_to_date = fiscal_end_date
#                 if cessation_date:
#                     payment_period_to_date = cessation_date

#################################################################################

                resource_ids = self.env['resource.resource'].search([('user_id', '=', int(form.get('payroll_user')))])
                employee_rec = employee_obj.search([('resource_id', 'in', resource_ids.ids)])
                res['autho_user'] = ''
                res['designation'] = ''
                res['tel_no'] = ''
#                 res['employee_income_tax'] = ''
                res['partially_borne'] = res['employee_fixed_amount'] = 0.0
                res['exempt_remission'] = res['exempt_not_taxble'] = 0.0
                for emp_rec in employee_rec:
                    res['autho_user'] = emp_rec.name
                    res['designation'] = emp_rec.job_id and emp_rec.job_id.name or ''
                    res['tel_no'] = emp_rec.mobile_phone or ''
                date_today = datetime.date.today()
                res['date_today'] = date_today.strftime('%d-%m-%Y')
                res['is_income'] = 'YES'
#                if contract_income_tax_rec.employee_income_tax == 'F':
                res['partially_borne'] = contract_income_tax_rec.employee_income
#                elif contract_income_tax_rec.employee_income_tax == 'P':
                res['employee_fixed_amount'] = contract_income_tax_rec.employment_income
                if contract_income_tax_rec.exempt_remission == '1':
                    res['exempt_remission'] = contract_income_tax_rec.exempt_income or 0.0
                else:
                    res['exempt_not_taxble'] = contract_income_tax_rec.exempt_income or 0.0
                # Round down
                res['gross_amt'] = int(gross_amt) * 1.00
                res['fund_name'] = contract_income_tax_rec.fund_name or ''
                res['identification_id'] = employee.identification_id
                res['employeer_tax'] = employee.company_id.vat
                employee_address = ''
                if employee.address_home_id:
                    employee_address = employee.address_home_id._display_address(without_company = True)
                res['address_home'] = employee_address
                res['cessation_date'] = cessation_date
                res['sex'] = sex
                res['birthday'] = birthday
                res['bonus_amt'] = int(bonus_amt) * 1.00
                res['director_fee'] = formatLang(self.env, int(abs(director_fee)) * 1.00 or 0.0)
                res['pension'] = formatLang(self.env, int(pension) * 1.00 or 0.0)
                res['transport_allowance'] = formatLang(self.env, int(transport_allowance) * 1.00)
                res['entertainment_allowance'] = formatLang(self.env, int(entertainment_allowance) * 1.00)
                res['other_allowance'] = formatLang(self.env, int(other_allowance) * 1.00)
                res['total_d_2'] = int(total_d_2) * 1.00
                res['gratuity_payment_amt'] = int(gratuity_payment_amt) * 1.00
                res['notice_pay'] = int(notice_pay_amt) * 1.00
                res['ex_gratia'] = int(ex_gratia_amt) * 1.00
                res['others'] = int(others_amt) * 1.00
                res['nationality'] = employee.empnationality_id.name or ''
                res['other_data'] = formatLang(self.env, int(other_data) * 1.00 or 0.0)
                res['mbf'] = contract_income_tax_rec.mbf or 0.0
                res['contribution_employer'] = contribution_employer

                if CPF_designated_pension_provident_fund:
                    CPF_designated_pension_provident_fund = CPF_designated_pension_provident_fund % 1 > 0.00 and (int(CPF_designated_pension_provident_fund) + 1) or CPF_designated_pension_provident_fund
                res['CPF_designated_pension_provident_fund'] = formatLang(self.env, int(CPF_designated_pension_provident_fund) * 1.00 or 0.0)
                if donation_amt:
                    donation_amt = donation_amt % 1 > 0.00 and (int(donation_amt) + 1) or donation_amt
                res['donation_amt'] = formatLang(self.env, int(donation_amt) * 1.00 or 0.0)
                if gross_commission:
                    fromdate = '01/01/%s' % str(fromdate)
                    todate = '31/12/%s' % str(todate)
                    
######################## UNUSED CODE #################################
#                 else:
#                     fromdate = ''
#                     todate = ''
######################################################################

                res['insurance'] = formatLang(self.env, int(insurance) * 1.00 or 0.0)
                res['fromdate'] = fromdate or ''
                res['todate'] = todate or ''
                res['gross_commission'] = formatLang(self.env, int(gross_commission) * 1.00 or 0.0)
                res['approval_date'] = approval_date or ''
                res['compensation_loss_office'] = formatLang(self.env, int(compensation_loss_office) * 1.00 or 0.0)
                res['approve_obtain_iras'] = contract_income_tax_rec.approve_obtain_iras or ''
                res['retirement_benifit_up'] = formatLang(self.env, int(retirement_benifit_up) * 1.00 or 0.0)
                res['retirement_benifit_from'] = formatLang(self.env, int(retirement_benifit_from) * 1.00 or 0.0)
                res['excess_voluntary_contribution_cpf_employer'] = formatLang(self.env, int(excess_voluntary_contribution_cpf_employer) * 1.00 or 0.0)
                res['gains_profit_share_option'] = formatLang(self.env, int(gains_profit_share_option) * 1.00 or 0.0)
                res['benifits_in_kinds'] = formatLang(self.env, int(benifits_in_kinds) * 1.00 or 0.0)
                res['job_name'] = employee.job_id.name or ''
                res['join_date'] = join_date or ''
                res['fund_name'] = contract_income_tax_rec.fund_name or ''
                res['previous_year'] = previous_year or ''
                res['company_name'] = employee.company_id.name or ''
                res['company_house'] = employee.company_id.house_no or ''
                res['company_street'] = employee.company_id.street or ''
                res['company_street2'] = employee.company_id.street2 or ''
                res['company_city'] = employee.company_id.city or ''
                res['company_state'] = employee.company_id and employee.company_id.state_id and employee.company_id.state_id.name or ''
                res['company_zip'] = employee.company_id.zip or ''
                res['company_country'] = employee.company_id and employee.company_id.country_id and employee.company_id.country_id.name or ''
                res['lum_sum_total'] = lum_sum_total
                res['approve_director_fee_date'] = approve_director_fee_date or ''
                if from_date:
                    year = from_date.year
                res['year'] = year or ''
                res['joined_year'] = employee.joined_year
                res['reason'] = contract_income_tax_rec.reason
                res['contribution_mandetory'] = contract_income_tax_rec.contribution_mandetory
                res['contribution_charged'] = contract_income_tax_rec.contribution_charged
                res['bank_name'] = employee.bank_account_id and employee.bank_account_id.bank_id and employee.bank_account_id.bank_id.name or ''
                res['contribution_amount'] = 0
                if contract_income_tax_rec.contribution_mandetory == 'Yes':
                    res['contribution_amount']=contract_income_tax_rec.contribution_amount
                                
#################### UNUSED CODE--############

#                 res['amount_data'] = int(amount_data) * 1.00
#                 res['payment_period_form_date'] = payment_period_form_date
#                 res['payment_period_to_date'] = payment_period_to_date
#                 res['batch_dates'] = batchdate
#                 res['bonus_declare_date'] = bonus_declare_date or ''
#                 res['approve_director_fee_date'] = approve_director_fee_date or ''
#                 res['deginated_pension'] = contract_income_tax_rec.deginated_pension or ''
#                 res['contribution_employer'] = formatLang(self.env, int(contribution_employer) * 1.00 or 0.0)
#                 res['from_ir8s'] = contract_income_tax_rec.from_ir8s or ''
#                 res['gross_commission_indicator'] = formatLang(self.env, int(contract_income_tax_rec.gross_commission_indicator) * 1.00 or 0.0)
#                 res['prv_yr_gross_amt'] = formatLang(self.env, int(prv_yr_gross_amt) * 1.00 or 0.0)
#                 res['benefits_kind'] = contract_income_tax_rec.benefits_kind or ''
#                 res['section_applicable'] = contract_income_tax_rec.section_applicable or ''
#                 res['gratuity_payment'] = contract_income_tax_rec.gratuity_payment or ''
#                 res['compensation'] = contract_income_tax_rec.compensation or ''
#                 res['cessation_provisions'] = employee.cessation_provisions or ''
#                 res['gain_profit'] = formatLang(self.env, int(gain_profit) * 1.00 or 0.0)
#                 res['exempt_income'] = formatLang(self.env, int(exempt_income) * 1.00 or 0.0)
#                 res['employment_income'] = contract_income_tax_rec.employee_income_tax == 'H' and int(employment_income) * 1.00 or ''
#                 res['donations'] = mbf_amt + donation_amt
#                 res['catemp_amt'] = catemp_amt
#                 res['mbf_amt'] = int(mbf_amt) * 1.00
#                 res['net_amt'] = int(net_amt) * 1.00
#############################################


#                 #Lets be smart!
#                 #Rather than doing change on all amounts, do here
#                 #if any values in IR8A PDF are empty meaning 0.00, it must display the characters NA
#                 #This should have been done smartly for rounding up and down too!
#                 for reskey in res.keys():
#                     if isinstance(res[reskey], float) and not res[reskey]:
#                         res[reskey] = 'NA'
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
        return self.env['report'].render('sg_income_tax_report.ir8a_incometax_form_report', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: