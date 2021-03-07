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
import base64
import tempfile
import datetime
from odoo import tools
from datetime import date
from time import gmtime, strftime
from odoo.tools.translate import _
from odoo.exceptions import Warning
from odoo import fields, api, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class emp_ir8a_text_file(models.TransientModel):

    _name = 'emp.ir8a.text.file'

    @api.multi
    def _get_payroll_user_name(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        supervisors_list = [(False,'')]
        data_obj = self.env['ir.model.data']
        result_data = data_obj._get_id('l10n_sg_hr_payroll', 'group_hr_payroll_admin')
        model_data = data_obj.browse(result_data)
        group_data = self.env['res.groups'].browse(model_data.res_id)
        for user in group_data.users:
            supervisors_list.append((tools.ustr(user.id), tools.ustr(user.name)))
        return supervisors_list

    employee_ids = fields.Many2many('hr.employee', 'hr_employe_ir8a_text_rel', 'emp_id', 'employee_id', 'Employee', required=False)
    start_date = fields.Date('Start Date', required=True, default=lambda *a: time.strftime('%Y-01-01'))
    end_date = fields.Date('End Date', required=True, default=lambda *a: time.strftime('%Y-12-31'))
    source = fields.Selection(selection=[('1', 'Mindef'), 
                                         ('4', 'Government Department'), 
                                         ('5', 'Statutory Board'),
                                         ('6', 'Private Sector'), 
                                         ('9', 'Others')], string='Source', default='6', required=True)
    organization_id_type = fields.Selection(selection=[('7', 'UEN – Business Registration number issued by ACRA'),
                                                       ('8', 'UEN – Local Company Registration number issued by ACRA'),
                                                       ('A', 'ASGD – Tax Reference number assigned by IRAS'),
                                                       ('I', 'ITR – Income Tax Reference number assigned by IRAS'),
                                                       ('U', 'UENO – Unique Entity Number Others')], string='Organization ID Type', default='8', required=True)
    organization_id_no = fields.Char('Organization ID No', size=16, required=True)
    batch_indicatior = fields.Selection(selection = [('O', 'Original'), 
                                                     ('A', 'Amendment')], string='Batch Indicator', required=True)
    batch_date = fields.Date('Batch Date', required=True, default=fields.Date.today)
    payroll_user = fields.Selection(_get_payroll_user_name, string='Name of authorised person', size=128, required=True, )
    print_type = fields.Selection(selection=[('text','Text'), 
                                             ('pdf', 'PDF')], string='Print as', required=True, default='text')

    company_id = fields.Many2one('res.company','Company',required=True,default=lambda self: self.env.user.company_id)

    @api.onchange('batch_date')
    def onchange_batch_date(self):
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if self.batch_date > today:
            self.batch_date = False
            return {
                'warning':
                    {
                        'title': 'Warning',
                        'message': 'You are not allow to Select Future Date !'
                    }
            }

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.organization_id_no = self.company_id.company_registry

    def generate_export_field_value(self, total_length, field_value):
        res = ''

        field_value_split = str(abs(field_value)).split(('.'))
        if len(str(field_value_split[1])) == 1:
            field_value_to_count = str(field_value_split[0]) + str(field_value_split[1]) + '0'
        else:
            field_value_to_count = str(field_value_split[0]) + str(field_value_split[1])

        value_length = len(str(field_value_to_count))

        difference_count = int(total_length) - int(value_length)

        res = str(field_value_to_count)
        if int(difference_count) > 0:
            list_of_zero_values = '%0*d' % (int(difference_count), 0)
            res = str(list_of_zero_values) + res

        return res

    @api.multi
    def download_ir8a_txt_file(self):
        context = self.env.context
        if context is None:
            context = {}
        context = dict(context)
        context.update({'active_test': False})
        employee_obj = self.env['hr.employee']
        data = self.read([])[0]
        emp_ids = data.get('employee_ids', []) or []
        start_year = datetime.datetime.strptime(data.get('start_date',False), '%Y-%m-%d').strftime('%Y')
        to_year = datetime.datetime.strptime(data.get('end_date',False), '%Y-%m-%d').strftime('%Y')
        start_date_year = '%s-01-01' % tools.ustr(int(start_year))
        end_date_year = '%s-12-31' % tools.ustr(int(to_year))
        start_date = '%s-01-01' % tools.ustr(int(start_year) - 1)
        end_date = '%s-12-31' % tools.ustr(int(to_year) - 1)
        if data.has_key('start_date') and data.has_key('end_date') and data.get('start_date',False) >= data.get('end_date',False):
            raise ValidationError(_("You must be enter start date less than end date !"))
        for employee in employee_obj.browse(emp_ids):
            emp_name = employee and employee.name or ''
            emp_id = employee and employee.id or False

            contract_ids = self.env['hr.contract'].search([('employee_id', '=', emp_id)])
            contract_income_tax_ids = self.env['hr.contract.income.tax'].search([('contract_id', 'in', contract_ids.ids),
                                                                                 ('start_date', '>=', start_date_year),
                                                                                 ('end_date', '<=', end_date_year)
                                                                                 ])
            if not contract_income_tax_ids.ids:
                raise ValidationError(_('There is no Income tax details available between selected date %s and %s for the %s employee for contarct.' % (start_date_year, end_date_year, emp_name)))
            payslip_ids = self.env['hr.payslip'].search([('date_from', '>=', start_date),
                                                         ('date_from', '<=', end_date),
                                                         ('employee_id', '=', emp_id), 
                                                         ('state', 'in', ['draft', 'done', 'verify'])])
            if not payslip_ids.ids:
                raise ValidationError (_('There is no payslip details available between selected date %s and %s for the %s employee.' % (start_date, end_date, emp_name)))
        context.update({'employe_id': data['employee_ids'], 'datas': data})
        if data.get('print_type', '') == 'text':
            payslip_obj = self.env['hr.payslip']
            tgz_tmp_filename = tempfile.mktemp('.' + "txt")
            tmp_file = False
            start_date = end_date = prev_yr_start_date = prev_yr_end_date = False
            from_date = context.get('datas',False).get('start_date',False) or False
            to_date = context.get('datas',False).get('end_date',False) or False
            if from_date and to_date:
                from_date =  datetime.datetime.strptime(from_date, DEFAULT_SERVER_DATE_FORMAT)
                to_date =  datetime.datetime.strptime(to_date, DEFAULT_SERVER_DATE_FORMAT)
                basis_year = tools.ustr(from_date.year - 1)
                fiscal_start = from_date.year - 1
                fiscal_start_date = '%s0101' % tools.ustr(int(fiscal_start))
                fiscal_end = to_date.year - 1
                fiscal_end_date = '%s1231' % tools.ustr(int(fiscal_end))
                start_date = '%s-01-01' % tools.ustr(int(fiscal_start))
                end_date = '%s-12-31' % tools.ustr(int(fiscal_end))
                start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
                prev_yr_start = from_date.year - 2
                prev_yr_end = to_date.year - 2
                prev_yr_start_date = '%s-01-01' % tools.ustr(int(prev_yr_start))
                prev_yr_end_date = '%s-12-31' % tools.ustr(int(prev_yr_end))
                prev_yr_start_date = datetime.datetime.strptime(prev_yr_start_date, DEFAULT_SERVER_DATE_FORMAT)
                prev_yr_end_date = datetime.datetime.strptime(prev_yr_end_date, DEFAULT_SERVER_DATE_FORMAT)
            try:
                tmp_file = open(tgz_tmp_filename, "wr")
                batchdate = datetime.datetime.strptime(context.get('datas')['batch_date'], DEFAULT_SERVER_DATE_FORMAT)
                batchdate = batchdate.strftime('%Y%m%d')
                server_date = basis_year + strftime("%m%d", gmtime())
                emp_id = employee_obj.search([('user_id', '=', int(context.get('datas')['payroll_user']))])
                emp_designation = emp_contact = emp_email = ''
                user_obj = self.env['res.users']
                payroll_admin_user_name = user_obj.browse(int(context.get('datas')['payroll_user'])).name
                company_name = user_obj.browse(int(context.get('datas')['payroll_user'])).company_id.name
                for emp in emp_id:
                    emp_designation = emp.job_id.name
                    emp_contact = emp.work_phone
                    emp_email = emp.work_email
                header_record = '0'.ljust(1) + \
                                tools.ustr(context.get('datas')['source'] or '').ljust(1) + \
                                tools.ustr(basis_year).ljust(4) + \
                                '08'.ljust(2) + \
                                tools.ustr(context.get('datas')['organization_id_type'] or '').ljust(1) + \
                                tools.ustr(context.get('datas')['organization_id_no'] or '').ljust(12) + \
                                tools.ustr(payroll_admin_user_name or '')[:30].ljust(30) + \
                                tools.ustr(emp_designation)[:30].ljust(30) + \
                                tools.ustr(company_name)[:60].ljust(60) + \
                                tools.ustr(emp_contact)[:20].ljust(20) + \
                                tools.ustr(emp_email)[:60].ljust(60) + \
                                tools.ustr(context.get('datas')['batch_indicatior'] or '').ljust(1) + \
                                tools.ustr(server_date or '').ljust(8) + \
                                ''.ljust(30) + \
                                ''.ljust(10) + \
                                ''.ljust(930) + \
                                "\r\n"
                tmp_file.write(header_record)
                total_detail_record = 0
                tot_prv_yr_gross_amt = tot_payment_amount = tot_insurance = tot_employment_income = tot_exempt_income = tot_other_data = tot_director_fee = tot_mbf_amt = tot_donation_amt = tot_catemp_amt = tot_net_amt = tot_salary_amt = tot_bonus_amt = 0
                insurance = director_fee = gain_profit = exempt_income = gross_commission = emp_voluntary_contribution_cpf = benifits_in_kinds = gains_profit_share_option = excess_voluntary_contribution_cpf_employer = contribution_employer = retirement_benifit_from = retirement_benifit_up = compensation_loss_office = gratuity_payment_amt = entertainment_allowance = pension = employee_income = tot_employee_income = 0
                contract_ids = self.env['hr.contract'].search([('employee_id','in',context.get('employe_id'))])
                for contract in contract_ids:
                    contract_income_tax_ids = self.env['hr.contract.income.tax'].search([('contract_id', '=', contract.id),
                                                                                         ('start_date', '>=', start_date_year),
                                                                                         ('end_date', '<=', end_date_year)])
                    if contract_income_tax_ids:
                        for emp in contract_income_tax_ids[0]:
                            total_detail_record += 1
                            sex = birthday = join_date = cessation_date = bonus_declare_date = approve_director_fee_date = fromdate = todate = approval_date = ''
#                            if contract.employee_id.gender == '':
#                                raise ValidationError(_('Please configure gender for %s employee'  % (contract.employee_id.name)))
                            if contract.employee_id.gender == 'male':
                                sex = 'M'
                            if contract.employee_id.gender == 'female':
                                sex = 'F'
                            if contract.employee_id.birthday:
                                birthday = datetime.datetime.strptime(contract.employee_id.birthday, DEFAULT_SERVER_DATE_FORMAT)
                                birthday = birthday.strftime('%Y%m%d')
                            if contract.employee_id.join_date:
                                join_date = datetime.datetime.strptime(contract.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT)
                                if contract.employee_id.cessation_provisions == 'Y' and join_date.year > 1969 or contract.employee_id.cessation_provisions != 'Y' and join_date.year < 1969:
                                    raise ValidationError(_('One of the following configuration is still missing from employee \nPlease configure all the following details for employee %s. \n\n * Date must be before 1969/01/01 when Cessation Provisions Indicator = Y \n* Provisions Indicator must be Y when join date before 1969/01/01' % (contract.employee_id.name) ))
                                join_date = join_date.strftime('%Y%m%d')
                            if contract.date_end:
                                cessation_date = datetime.datetime.strptime(contract.date_end, DEFAULT_SERVER_DATE_FORMAT)
                                cessation_date = cessation_date.strftime('%Y%m%d')
                            if emp.bonus_declaration_date:
                                bonus_declare_date = datetime.datetime.strptime(emp.bonus_declaration_date, DEFAULT_SERVER_DATE_FORMAT)
                                bonus_declare_date = bonus_declare_date.strftime('%Y%m%d')
                            if emp.director_fee_approval_date:
                                approve_director_fee_date = datetime.datetime.strptime(emp.director_fee_approval_date, DEFAULT_SERVER_DATE_FORMAT)
                                approve_director_fee_date = approve_director_fee_date.strftime('%Y%m%d')
                            if emp.approval_date:
                                approval_date = datetime.datetime.strptime(emp.approval_date, DEFAULT_SERVER_DATE_FORMAT)
                                approval_date = approval_date.strftime('%Y%m%d')
                            entertainment_allowance = transport_allowance = salary_amt = other_allowance = other_data = amount_data = mbf_amt = donation_amt = catemp_amt = net_amt = bonus_amt = prv_yr_gross_amt = gross_comm = 0
                            prev_yr_payslip_ids = payslip_obj.search([('date_from', '>=', prev_yr_start_date),
                                                                      ('date_from', '<=', prev_yr_end_date), 
                                                                      ('employee_id', '=', contract.employee_id.id), 
                                                                      ('state', 'in', ['draft', 'done', 'verify'])])
#                            for payslip in prev_yr_payslip_ids:
#                                for line in payslip.line_ids:
#                                    if line.code == 'GROSS':
#                                        prv_yr_gross_amt += line.amount
                            payslip_ids = payslip_obj.search([('date_from', '>=', start_date), 
                                                              ('date_from', '<=', end_date), 
                                                              ('employee_id', '=', contract.employee_id.id), 
                                                              ('state', 'in', ['draft', 'done', 'verify'])], order="date_from")
                            for payslip in payslip_ids:
                                basic_flag = False
                                for line in payslip.line_ids:
                                    if line.code == 'BASIC':
                                        basic_flag = True
                                if basic_flag and emp.contract_id.wage:
                                    salary_amt += contract.wage
                                for line in payslip.line_ids:
                                    if not contract.wage and contract.rate_per_hour and line.code == 'SC100':
                                        salary_amt += line.total
                                    if line.code == 'CPFMBMF':
                                        mbf_amt += line.total
                                    if line.code in ['CPFSINDA', 'CPFCDAC', 'CPFECF']:
                                        donation_amt += line.total
                                    if line.category_id.code == 'CAT_CPF_EMPLOYEE':
                                        catemp_amt += line.total
                                    if line.code == 'GROSS':
    #                                    salary_amt += line.amount
                                        net_amt += line.total
                                    if line.code == 'SC121':
                                        salary_amt -= line.total
                                        bonus_amt += line.total
                                        net_amt -= line.total
                                    if line.code in ['SC106','SC108','SC123', 'FA']:
                                        other_allowance += line.total
                                        net_amt -= line.total
                                    if line.category_id.code in ['ADD', 'ALW']:
                                        other_data += line.total
                                        salary_amt += line.total
                                    if line.code in ['SC200', 'SC206']:
                                        salary_amt -= line.total
                                    if line.code in ['SC104', 'SC105']:
                                        salary_amt -= line.total
                                        if not fromdate:
                                            fromdate = datetime.datetime.strptime(payslip.date_from, DEFAULT_SERVER_DATE_FORMAT)
                                            fromdate = fromdate.strftime('%Y%m%d')
                                        todate = datetime.datetime.strptime(payslip.date_to, DEFAULT_SERVER_DATE_FORMAT)
                                        todate = todate.strftime('%Y%m%d')
                                        gross_comm += line.total
                                        net_amt -= line.total
                                    if line.code == 'TA':
                                        transport_allowance += line.total
                           # other_data = gross_comm + emp.pension + transport_allowance + emp.entertainment_allowance + other_allowance + emp.gratuity_payment_amt + emp.retirement_benifit_from + emp.contribution_employer + emp.excess_voluntary_contribution_cpf_employer + emp.gains_profit_share_option + emp.benifits_in_kinds
                            mbf_amt = '%0*d' % (5, int(abs(round(mbf_amt, 0))))
                            donation_amt = '%0*d' % (5, int(abs(round(donation_amt, 0))))
                            catemp_amt = '%0*d' % (7, int(abs(round(catemp_amt, 0))))
                            net_amt = '%0*d' % (9, int(abs(net_amt)))

                            salary_amt = '%0*d' % (9, int(abs(emp.payslip_net_amount)))

                            bonus_amt = '%0*d' % (9, int(abs(bonus_amt)))

                            insurance = '%0*d' % (5, int(abs(emp.insurance)))
                            tot_insurance +=  int(insurance[:5])
                            director_fee = '%0*d' % (9, int(abs(emp.director_fee)))
                            gain_profit = '%0*d' % (9, int(abs(emp.gain_profit)))
                            exempt_income = '%0*d' % (9, int(abs(emp.exempt_income)))
                            employment_income = '%0*d' % (9, int(abs(emp.employment_income)))


                            #gross_commission = '%0*d' % (11, int(abs(gross_comm * 100)))
                            gross_commission_str = self.generate_export_field_value(11, float(abs(emp.gross_commission)))

                            #pension = '%0*d' % (11, int(abs(emp.pension * 100)))
                            pension_str = self.generate_export_field_value(11, float(abs(emp.pension)))

                            #transport_allowance = '%0*d' % (11, int(abs(transport_allowance * 100)))
                            transport_allowance_str = self.generate_export_field_value(11, float(abs(transport_allowance)))

                            #entertainment_allowance = '%0*d' % (11, int(abs(emp.entertainment_allowance * 100)))
                            entertainment_allowance_str = self.generate_export_field_value(11, float(abs(emp.entertainment_allowance)))

                            #gratuity_payment_amt = '%0*d' % (11, int(abs(emp.gratuity_payment_amt * 100)))
                            gratuity_payment_amt_str = self.generate_export_field_value(11, float(abs(emp.gratuity_payment_amt)))

                            compensation_loss_office = '%0*d' % (11, int(abs(emp.compensation_loss_office * 100)))
                            retirement_benifit_up = '%0*d' % (11, int(abs(emp.retirement_benifit_up * 100)))

                            #retirement_benifit_from = '%0*d' % (11, int(abs(emp.retirement_benifit_from * 100)))
                            retirement_benifit_from_str = self.generate_export_field_value(11, float(abs(emp.retirement_benifit_from)))

                            #contribution_employer = '%0*d' % (11, int(abs(emp.contribution_employer * 100)))
                            contribution_employer_str = self.generate_export_field_value(11, float(abs(emp.contribution_employer)))

                            #excess_voluntary_contribution_cpf_employer = '%0*d' % (11, int(abs(emp.excess_voluntary_contribution_cpf_employer * 100)))
                            excess_voluntary_contribution_cpf_employer_str = self.generate_export_field_value(11, float(abs(emp.excess_voluntary_contribution_cpf_employer)))

                            #gains_profit_share_option = '%0*d' % (11, int(abs(emp.gains_profit_share_option * 100)))
                            gains_profit_share_option_str = self.generate_export_field_value(11, float(abs(emp.gains_profit_share_option)))

                            #benifits_in_kinds = '%0*d' % (11, int(abs(emp.benifits_in_kinds * 100)))
                            benifits_in_kinds_str = self.generate_export_field_value(11, float(abs(emp.benifits_in_kinds)))

                            emp_voluntary_contribution_cpf = '%0*d' % (7, int(abs(emp.emp_voluntary_contribution_cpf)))

                            if emp.employee_income_tax in ['F','H']:
                                employment_income = ''
                            elif emp.employee_income_tax in ['P']:
                                if emp.employment_income < 0:
                                    raise ValidationError('Employment income must be greater than zero')
                                employment_income = '%0*d' % (9, int(abs(emp.employment_income)))
                                tot_employment_income += int('%0*d' % (9, int(abs(emp.employment_income))))
                            if emp.employee_income_tax in ['F','P']:
                                employee_income = ''
#####                        if emp.employee_income_tax in ['H']:
                            elif emp.employee_income_tax in ['H']:
                                if emp.employee_income < 0:
                                    raise ValidationError('Employee income must be greater than zero')
                                employee_income = '%0*d' % (9, int(abs(emp.employee_income)))
                                tot_employee_income += int(abs(emp.employee_income))

                            other_allowance_str = self.generate_export_field_value(11, float(abs(emp.other_allowance)))

                            other_data = (int(emp.gross_commission) or 0) + (int(emp.pension) or 0) + (int(emp.transport) or 0) + \
                                       (int(emp.entertainment_allowance) or 0) + (int(emp.other_allowance) or 0) + (int(emp.gratuity_payment_amt) or 0) + \
                                       (int(emp.retirement_benifit_from) or 0) + (int(emp.contribution_employer) or 0) + \
                                       (int(emp.excess_voluntary_contribution_cpf_employer) or 0) + (int(emp.gains_profit_share_option) or 0)

                            other_allowance = '%0*d' % (11, int(abs(other_allowance * 100)))

                            if emp.benefits_kind == 'Y':
                                other_data += (int(emp.benifits_in_kinds) or 0)

                            amount_data = other_data + int(salary_amt) + int(emp.director_fee) + int(bonus_amt)
                            tot_other_data += other_data
                            other_data = '%0*d' % (9, int(abs(other_data)))
                            amount_data = '%0*d' % (9, int(abs(amount_data)))
                            if prv_yr_gross_amt != '':
                                tot_prv_yr_gross_amt += int(prv_yr_gross_amt)
                            tot_mbf_amt += int(mbf_amt[:5])
                            tot_donation_amt += int(donation_amt[:5])
                            tot_catemp_amt += int(catemp_amt[:7])
                            tot_net_amt += int(net_amt[:9])
                            tot_salary_amt += int(salary_amt[:9])
                            tot_bonus_amt += int(bonus_amt[:9])
                            tot_director_fee += int(director_fee[:9])
                            tot_exempt_income += int(exempt_income[:9])
                            house_no = street = level_no = unit_no = street2 = postal_code = countrycode = nationalitycode = unformatted_postal_code = employee_income_tax_born=exempt_remission_selection=gratuity_payment_selection=compensation_office=from_ir8s_selection=section_applicable_s=benefits_kind_Y=approve_iras_obtain=cessation_provisions_selection=''
                            if emp.employee_income > 0 and emp.employee_income_tax not in ['P','H'] or emp.employment_income > 0 and emp.employee_income_tax not in ['P','H']:
                                raise ValidationError(_('Employees Income Tax borne by employer must be P or H for %s employee.' % (contract.employee_id.name) ))
                            if emp.exempt_remission == '6':
                                exempt_income = ''
                            if emp.exempt_income != 0:
                                if not emp.exempt_remission in ['1', '3', '4', '5', '7']:
                                    raise ValidationError(_('Exempt/ Remission income Indicator must be in 1, 3, 4, 5 or 7 for %s employee.' % (contract.employee_id.name) ))
                            if emp.employee_income_tax == 'N':
                                employee_income_tax_born=''
                            if emp.employee_income_tax != 'N':
                                employee_income_tax_born=emp.employee_income_tax
#                            if emp.employment_income > 0 and emp.employee_income_tax != 'P':
#                                raise ValidationError(_('Employees Income Tax borne by employer must be P for %s employee.' % (contract.employee_id.name) ))
#                            if prv_yr_gross_amt > 0 and emp.employee_income_tax != 'H':
#                                raise ValidationError(_('Employees Income Tax borne by employer must be H for %s employee.' % (contract.employee_id.name) ))
                            if emp.gratuity_payment == 'Y':
                                gratuity_payment_selection=emp.gratuity_payment
                            if emp.gratuity_payment == 'N':
                                gratuity_payment_amt_str = ''
                            if emp.gratuity_payment_amt != 0:
                                if emp.gratuity_payment != 'Y':
                                    raise ValidationError(_('Gratuity/ Notice Pay/ Ex-gratia payment/ Others indicator must be Y for %s employee.' % (contract.employee_id.name) ))
                            if emp.compensation == 'Y':
                                compensation_office=emp.compensation
                            if not emp.approve_obtain_iras != '' or emp.compensation_loss_office != 0:
                                if emp.compensation != 'Y':
                                    raise ValidationError(_('Compensation for loss of office indicator must be Y for %s employee.' % (contract.employee_id.name) ))
                            if emp.exempt_remission != 'N':
                                exempt_remission_selection=emp.exempt_remission
                            if emp.from_ir8s != 'Y' and emp.emp_voluntary_contribution_cpf > 0:
                                raise ValidationError(_('Form IR8S must be applicable for %s employee.' % (contract.employee_id.name) ))
                            else:
                                from_ir8s_selection=emp.from_ir8s
                            if emp.section_applicable == 'Y':
                                section_applicable_s=emp.section_applicable
                            if emp.benefits_kind == 'Y':
                                benefits_kind_Y=emp.benefits_kind
                            if emp.benefits_kind == 'N':
                                benifits_in_kinds_str = ''
                            if emp.benifits_in_kinds > 0 and not emp.benefits_kind or emp.approval_date and emp.approve_obtain_iras != 'Y':
                                raise ValidationError(_('One of the following configuration is still missing from employee.\nPlease configure all the following details for employee %s. \n\n * Benefits-in-kind indicator must be Y \n* Approval obtained from IRAS must be Y' % (contract.employee_id.name) ))
                            approve_iras_obtain=emp.approve_obtain_iras
                            if emp.approve_obtain_iras == 'Y':
                                if not emp.approval_date:
                                    raise ValidationError('You must be configure approval date')
                                else:
                                    approval_date = datetime.datetime.strptime(emp.approval_date, DEFAULT_SERVER_DATE_FORMAT)
                                    approval_date = approval_date.strftime('%Y%m%d')
                            else:
                                approval_date = ''
#                            if emp.approval_date != False and emp.approve_obtain_iras != 'Y':
#                                raise ValidationError(_('Approval obtained from IRAS must be Y for %s employee.' % (contract.employee_id.name) ))
                            if contract.employee_id.cessation_provisions == 'Y':
                                cessation_provisions_selection=contract.employee_id.cessation_provisions
                            if contract.employee_id.address_type != "N":
                                if not contract.employee_id.address_home_id or contract.employee_id.address_home_id.zip and len(contract.employee_id.address_home_id.zip) < 6:
                                    raise ValidationError(_('One of the following configuration is still missing from employee\'s profile.\nPlease configure all the following details for employee %s. \n\n * Home Address \n* Postal code must be 6 numeric digits' % (contract.employee_id.name) ))
#                                if contract.employee_id.address_home_id.zip and len(contract.employee_id.address_home_id.zip) < 6:
#                                    raise ValidationError(_('Postal code must be 6 Numeric digit for %s employee home address.' % (contract.employee_id.name) ))
#                                if contract.employee_id.address_type == "L" and not :
#                                    raise ValidationError(_('You must be configure House No for %s employee.' % (contract.employee_id.name)))
                                street2 = contract.employee_id.address_home_id.street2
                                level_no = contract.employee_id.address_home_id.level_no
                                unit_no = contract.employee_id.address_home_id.unit_no
#                                if contract.employee_id.address_type == "L" and not :
#                                    raise ValidationError(_('You must be configure Postal Code for %s employee.' % (contract.employee_id.name)))
                                if contract.employee_id.address_type in ['F', 'C'] and not contract.employee_id.address_home_id.street2:
                                    raise ValidationError(_('You must be configure street2 for %s employee home address.' % (contract.employee_id.name) ))
                                if contract.employee_id.address_type == "F":
                                    house_no = ''
                                    street = ''
                                    postal_code = ''
                                    level_no= ''
                                    unit_no = ''
                                    countrycode = contract.employee_id.empcountry_id.code
                                if contract.employee_id.address_type == "L":
                                    unformatted_postal_code = ''
                                    countrycode = ''
                                    street2 = ''
                                    if not contract.employee_id.address_home_id.street or not contract.employee_id.address_home_id.house_no or not contract.employee_id.address_home_id.zip:
                                        raise ValidationError(_('''One of the following configuration is still missing from employee\'s profile.\nPlease configure all the following details for employee %s. \n\n
                                            * Street \n* House No \n* Postal Code'''
                                         % (contract.employee_id.name)))
                                    street = contract.employee_id.address_home_id.street
                                    house_no = contract.employee_id.address_home_id.house_no
                                    postal_code = contract.employee_id.address_home_id.zip
                                if contract.employee_id.address_type == 'C':
                                    if not contract.employee_id.address_home_id.zip:
                                        raise ValidationError(_('You must be configure postal code for %s employee home address.' % (contract.employee_id.name) ))
                                    house_no = ''
                                    street = ''
                                    postal_code = ''
                                    unformatted_postal_code = contract.employee_id.address_home_id.zip
                                    countrycode = ''

#                             if contract.employee_id.address_type == "F" and not contract.employee_id.empcountry_id:
#                                 raise ValidationError(_('You must be configure Country Code for %s employee.' % (contract.employee_id.name) ))
#                             if contract.employee_id.address_home_id.unit_no != False and not contract.employee_id.address_home_id.level_no:
#                                 raise ValidationError(_('You must be configure Level no for %s employee home address.' % (contract.employee_id.name)))
#                             if contract.employee_id.address_home_id.level_no != False and not contract.employee_id.address_home_id.unit_no:
#                                 raise ValidationError(_('You must be configure Unit no for %s employee home address.' % (contract.employee_id.name)))
#                             if not contract.employee_id.empnationality_id:
#                                 raise ValidationError(_('You must be configure Nationality Code for %s employee.' % (contract.employee_id.name) ))
                            if not contract.employee_id.empnationality_id or (contract.employee_id.address_home_id.level_no != False and not contract.employee_id.address_home_id.unit_no) or \
                                (contract.employee_id.address_type == "F" and not contract.employee_id.empcountry_id) or (contract.employee_id.address_home_id.unit_no != False and not contract.employee_id.address_home_id.level_no):
                                raise ValidationError(_('''One of the following configuration is still missing from employee\'s profile.\nPlease configure all the following details for employee %s. \n\n
                                            * Nationality Code \n* Unit no of home address \n* Country Code \n* Level no of home address '''
                                         % (contract.employee_id.name)))

                            if contract.employee_id.empnationality_id:
                                nationalitycode = contract.employee_id.empnationality_id.code
                            payment_period_form_date = fiscal_start_date
                            payment_period_to_date = fiscal_end_date
                            if cessation_date:
                                payment_period_to_date = cessation_date
                            if emp.employee_income_tax == 'F' or emp.employee_income_tax == 'H':
                                employment_income = ''
                            period_date_start = period_date_end = gross_comm_indicator =''
                            if emp.gross_commission > 0:
                                period_date_start = fromdate
                                period_date_end = todate
                                gross_comm_indicator = 'M'
                            else:
                                period_date_start = ''
                                period_date_end = ''
                                gross_comm_indicator = ''
                            detail_record = '1'.ljust(1) + \
                                            tools.ustr(contract.employee_id.identification_no or '').ljust(1) + \
                                            tools.ustr(contract.employee_id.identification_id or '')[:12].ljust(12) + \
                                            tools.ustr(contract.employee_id.name or '')[:80].ljust(80) + \
                                            tools.ustr(contract.employee_id.address_type or '')[:1].ljust(1) + \
                                            tools.ustr(house_no or '')[:10].ljust(10) + \
                                            tools.ustr(street or '')[:32].ljust(32) + \
                                            tools.ustr(level_no or '')[:3].ljust(3) + \
                                            tools.ustr(unit_no or '')[:5].ljust(5) + \
                                            tools.ustr(postal_code or '')[:6].ljust(6) + \
                                            tools.ustr(street2 or '')[:30].ljust(30) + \
                                            ''.ljust(30) + \
                                            ''.ljust(30) + \
                                            tools.ustr(unformatted_postal_code or '')[:6].ljust(6) + \
                                            tools.ustr(countrycode or '')[:3].ljust(3) + \
                                            tools.ustr(nationalitycode or '')[:3].ljust(3) + \
                                            tools.ustr(sex).ljust(1) + \
                                            tools.ustr(birthday).ljust(8) + \
                                            tools.ustr(amount_data)[:9].ljust(9) + \
                                            tools.ustr(payment_period_form_date).ljust(8) + \
                                            tools.ustr(payment_period_to_date).ljust(8) + \
                                            tools.ustr(mbf_amt)[:5].ljust(5) + \
                                            tools.ustr(donation_amt)[:5].ljust(5) + \
                                            tools.ustr(catemp_amt)[:7].ljust(7) + \
                                            tools.ustr(insurance)[:5].ljust(5) + \
                                            tools.ustr(salary_amt)[:9].ljust(9) + \
                                            tools.ustr(bonus_amt)[:9].ljust(9) + \
                                            tools.ustr(director_fee)[:9].ljust(9) + \
                                            tools.ustr(other_data)[:9].ljust(9) + \
                                            tools.ustr(gain_profit)[:9].ljust(9) + \
                                            tools.ustr(exempt_income)[:9].ljust(9) + \
                                            tools.ustr(employment_income or '')[:9].ljust(9) + \
                                            tools.ustr(employee_income)[:9].ljust(9) + \
                                            tools.ustr(benefits_kind_Y or '').ljust(1) + \
                                            tools.ustr(section_applicable_s or '').ljust(1) + \
                                            tools.ustr(employee_income_tax_born or '').ljust(1) + \
                                            tools.ustr(gratuity_payment_selection or '').ljust(1) + \
                                            tools.ustr(compensation_office or '').ljust(1) + \
                                            tools.ustr(approve_iras_obtain or '').ljust(1) + \
                                            tools.ustr(approval_date).ljust(8) + \
                                            tools.ustr(cessation_provisions_selection or '').ljust(1) + \
                                            tools.ustr(from_ir8s_selection or '').ljust(1) + \
                                            tools.ustr(exempt_remission_selection or '').ljust(1) + \
                                            ''.ljust(1) + \
                                            tools.ustr(gross_commission_str)[:11].ljust(11) + \
                                            tools.ustr(period_date_start).ljust(8) + \
                                            tools.ustr(period_date_end).ljust(8) + \
                                            tools.ustr(gross_comm_indicator).ljust(1) + \
                                            tools.ustr(pension_str)[:11].ljust(11) + \
                                            tools.ustr(transport_allowance_str)[:11].ljust(11) + \
                                            tools.ustr(entertainment_allowance_str)[:11].ljust(11) + \
                                            tools.ustr(other_allowance_str)[:11].ljust(11) + \
                                            tools.ustr(gratuity_payment_amt_str)[:11].ljust(11) + \
                                            tools.ustr(compensation_loss_office)[:11].ljust(11) + \
                                            tools.ustr(retirement_benifit_up)[:11].ljust(11) + \
                                            tools.ustr(retirement_benifit_from_str)[:11].ljust(11) + \
                                            tools.ustr(contribution_employer_str)[:11].ljust(11) + \
                                            tools.ustr(excess_voluntary_contribution_cpf_employer_str)[:11].ljust(11) + \
                                            tools.ustr(gains_profit_share_option_str)[:11].ljust(11) + \
                                            tools.ustr(benifits_in_kinds_str)[:11].ljust(11) + \
                                            ''.ljust(7) + \
                                            tools.ustr(contract.employee_id.job_id.name or '')[:30].ljust(30) + \
                                            tools.ustr(join_date).ljust(8) + \
                                            tools.ustr(cessation_date).ljust(8) + \
                                            tools.ustr(bonus_declare_date).ljust(8) + \
                                            tools.ustr(approve_director_fee_date).ljust(8) + \
                                            tools.ustr(emp.fund_name or '').ljust(60) + \
                                            tools.ustr(emp.deginated_pension or '').ljust(60) + \
                                            ''.ljust(1) + \
                                            ''.ljust(8) + \
                                            ''.ljust(393) + \
                                            ''.ljust(50) + \
                                             "\r\n"
                            print "Employee Income:" + str(employee_income)
                            print "Total: " + str(tot_employee_income)
                            tmp_file.write(detail_record)
                tot_payment_amount = tot_salary_amt + tot_bonus_amt + tot_director_fee + tot_other_data

                #print "Total after loop: " + str(tot_employee_income)

                total_detail_record = '%0*d' % (6, int(abs(total_detail_record)))
                tot_payment_amount = '%0*d' % (12, int(abs(tot_payment_amount)))
                tot_mbf_amt = '%0*d' % (12, int(abs(tot_mbf_amt)))
                tot_donation_amt = '%0*d' % (12, int(abs(tot_donation_amt)))
                tot_catemp_amt = '%0*d' % (12, int(abs(tot_catemp_amt)))
                tot_net_amt = '%0*d' % (12, int(abs(tot_net_amt)))
                tot_salary_amt = '%0*d' % (12, int(abs(tot_salary_amt)))
                tot_bonus_amt = '%0*d' % (12, int(abs(tot_bonus_amt)))
                tot_director_fee = '%0*d' % (12, int(abs(tot_director_fee)))
                tot_other_data = '%0*d' % (12, int(abs(tot_other_data)))
                tot_exempt_income = '%0*d' % (12, int(abs(tot_exempt_income)))
                tot_employment_income= '%0*d' % (12, int(abs(tot_employment_income)))
                tot_insurance = '%0*d' % (12, int(abs(tot_insurance)))
                tot_employee_income = '%0*d' % (12, int(abs(tot_employee_income)))
                footer_record = '2'.ljust(1) + \
                                tools.ustr(total_detail_record)[:6].ljust(6) + \
                                tools.ustr(tot_payment_amount)[:12].ljust(12) + \
                                tools.ustr(tot_salary_amt)[:12].ljust(12) + \
                                tools.ustr(tot_bonus_amt)[:12].ljust(12) + \
                                tools.ustr(tot_director_fee)[:12].ljust(12) + \
                                tools.ustr(tot_other_data)[:12].ljust(12) + \
                                tools.ustr(tot_exempt_income)[:12].ljust(12) + \
                                tools.ustr(tot_employment_income)[:12].ljust(12) + \
                                tools.ustr(tot_employee_income)[:12].ljust(12) + \
                                tools.ustr(tot_donation_amt)[:12].ljust(12) + \
                                tools.ustr(tot_catemp_amt)[:12].ljust(12) + \
                                tools.ustr(tot_insurance)[:12].ljust(12) + \
                                tools.ustr(tot_mbf_amt)[:12].ljust(12) + \
                                ' '.ljust(1049) + "\r\n"

               # print ("Total employee Income: " + str(tot_employee_income))
                tmp_file.write(footer_record)
            finally:
                if tmp_file:
                    tmp_file.close()
            file = open(tgz_tmp_filename, "rb")
            out = file.read()
            file.close()
            res = base64.b64encode(out)
            module_rec = self.env['binary.ir8a.text.file.wizard'].create({'name': 'IR8A.txt', 'ir8a_txt_file' : res})
            return {
              'name': _('Binary'),
              'res_id' : module_rec.id,
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'binary.ir8a.text.file.wizard',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': context,
            }
        elif data.get('print_type', '') == 'pdf':
            if not employee.bank_account_id or not employee.gender or not employee.birthday or not employee.identification_id or not employee.work_phone or not employee.work_email:
                raise ValidationError(_('One of the following configuration is still missing from employee\'s profile.\nPlease configure all the following details for employee %s. \n\n * Bank Account \n* Gender \n* Birth Day \n* Identification No \n* Email or Contact ' % (emp_name)))
            data = {
                'ids' : [],
                'model' : 'hr.payslip',
                'form' : data
            }
            ret = {
                'type': 'ir.actions.report.xml',
                'report_name' : 'sg_income_tax_report.ir8a_incometax_form_report',
                'datas': data
            }
        return ret

emp_ir8a_text_file()

class binary_ir8a_text_file_wizard(models.TransientModel):

    _name = 'binary.ir8a.text.file.wizard'
    
    name = fields.Char('Name', size=64, default='IR8A.txt')
    ir8a_txt_file = fields.Binary('Click On Download Link To Download File', readonly=True)
    
binary_ir8a_text_file_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
