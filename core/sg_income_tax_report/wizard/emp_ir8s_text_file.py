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
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class emp_ir8s_text_file(models.TransientModel):
    _name = 'emp.ir8s.text.file'

    @api.multi
    def _get_payroll_user_name(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        supervisors_list = [(False, '')]
        data_obj = self.env['ir.model.data']
        result_data = data_obj._get_id('l10n_sg_hr_payroll', 'group_hr_payroll_admin')
        model_data = data_obj.browse(result_data)
        group_data = self.env['res.groups'].browse(model_data.res_id)
        for user in group_data.users:
            supervisors_list.append((tools.ustr(user.id), tools.ustr(user.name)))
        return supervisors_list

    employee_ids = fields.Many2many('hr.employee', 'hr_employe_ir8s_txt_rel', 'emp_id', 'employee_id', 'Employee', required = True)
    start_date = fields.Date('Start Date', required = True, default = lambda *a: time.strftime('%Y-01-01'))
    end_date = fields.Date('End Date', required = True, default = lambda *a: time.strftime('%Y-12-31'))
    source = fields.Selection(selection = [('1', 'Mindef'),
                                         ('2', 'Government Department'),
                                         ('5', 'Statutory Board'),
                                         ('6', 'Private Sector'),
                                         ('9', 'Others')], string = 'Source', default = '6', required = True)
    organization_id_type = fields.Selection(selection = [('7', 'UEN - Business'),
                                                       ('8', 'UEN - Local'),
                                                       ('A', 'ASGD'),
                                                       ('I', 'ITR'),
                                                       ('U', 'UENO')], string = 'Organization ID Type', default='8',required = True)
    organization_id_no = fields.Char('Organization ID No', size = 16, required = True)
    batch_indicatior = fields.Selection([('O', 'Original'),
                                         ('A', 'Amendment')], default = 'O', string = 'Batch Indicator', required = True)
    batch_date = fields.Date('Batch Date', required = True, default=fields.Date.today)
    payroll_user = fields.Selection(_get_payroll_user_name, string = 'Name of authorised person', size = 128, required = True)
    print_type = fields.Selection(selection = [('text', 'Text'), ('pdf', 'PDF')], string = 'Print as', required = True, default = 'text')
    company_id = fields.Many2one('res.company','Company',required=True ,default=lambda self: self.env.user.company_id)

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

    @api.multi
    def download_ir8s_txt_file(self):
        context = self.env.context
        if context is None:
            context = {}
        context = dict(context)
        context.update({'active_test': False})
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        hr_contract_income_tax_obj = self.env['hr.contract.income.tax']
        payslip_obj = self.env['hr.payslip']
        data = self.read([])[0]
        emp_ids = data.get('employee_ids', []) or []
        start_year = datetime.datetime.strptime(data.get('start_date', False), '%Y-%m-%d').strftime('%Y')
        to_year = datetime.datetime.strptime(data.get('end_date', False), '%Y-%m-%d').strftime('%Y')
        start_date_year = '%s-01-01' % tools.ustr(int(start_year))
        end_date_year = '%s-12-31' % tools.ustr(int(to_year))
        start_date = '%s-01-01' % tools.ustr(int(start_year) - 1)
        end_date = '%s-12-31' % tools.ustr(int(to_year) - 1)
        if data.has_key('start_date') and data.has_key('end_date') and data.get('start_date', False) >= data.get('end_date', False):
            raise ValidationError(_("You must be enter start date less than end date !"))
        for employee in employee_obj.browse(emp_ids):
            emp_name = employee and employee.name or ''
            emp_id = employee and employee.id or False
            
            if not employee.bank_account_id or not employee.gender or not employee.birthday or not employee.identification_id or not employee.work_phone or not employee.work_email:
                raise ValidationError(_('One of the following configuration is still missing from employee\'s profile.\nPlease configure all the following details for employee %s. \n\n * Bank Account \n* Gender \n* Birth Day \n* Identification No \n* Email or Contact ' % (emp_name)))
            
            contract_ids = contract_obj.search([('employee_id', '=', emp_id)])
            contract_income_tax_rec = hr_contract_income_tax_obj.search([('contract_id', 'in', contract_ids.ids),
                                                                         ('start_date', '>=', start_date_year),
                                                                         ('end_date', '<=', end_date_year)
                                                                         ])
            if not contract_income_tax_rec.ids:
                raise ValidationError(_('There is no Income tax details available between selected date %s and %s for the %s employee for contarct.' % (start_date_year, end_date_year, emp_name)))
            payslip_ids = payslip_obj.search([('date_from', '>=', start_date),
                                              ('date_from', '<=', end_date),
                                              ('employee_id', '=', emp_id),
                                              ('state', 'in', ['draft', 'done', 'verify'])])
            if not payslip_ids.ids:
                raise ValidationError (_('There is no payslip details available between selected date %s and %s for the %s employee.' % (start_date, end_date, emp_name)))
        context.update({'employe_id': data['employee_ids'], 'datas': data})
        if data.get('print_type', '') == 'text':
            tgz_tmp_filename = tempfile.mktemp('.' + "txt")
            tmp_file = current_year = False
            start_date = context.get('datas').get('start_date', False) or False
            end_date = context.get('datas').get('end_date', False) or False
            if start_date and end_date:
                current_year = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).year - 1
                start_year = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).year - 1
                end_year = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT).year - 1
                start_date = '%s-01-01' % tools.ustr(int(start_year))
                end_date = '%s-12-31' % tools.ustr(int(end_year))
                start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
            try:
                tmp_file = open(tgz_tmp_filename, "wr")
                batchdate = datetime.datetime.strptime(context.get('datas')['batch_date'], DEFAULT_SERVER_DATE_FORMAT)
                batchdate = batchdate.strftime('%Y%m%d')
                server_date = strftime("%Y%m%d", gmtime())
                emp_id = employee_obj.search([('user_id', '=', int(context.get('datas')['payroll_user']))])
                emp_designation = emp_email = emp_contact = ''
                emp_pay_user = self.env['res.users'].browse(int(context.get('datas')['payroll_user']))
                payroll_admin_user_name = emp_pay_user.name
                company_name = emp_pay_user.company_id.name
                for emp in emp_id:
                    emp_designation = emp.job_id.name
                    emp_email = emp.work_email
                    emp_contact = emp.work_phone
                header_record = '0'.ljust(1) + \
                                tools.ustr(context.get('datas')['source'] or '').ljust(1) + \
                                tools.ustr(current_year or '').ljust(4) + \
                                tools.ustr(context.get('datas')['organization_id_type'] or '').ljust(1) + \
                                tools.ustr(context.get('datas')['organization_id_no'] or '').ljust(12) + \
                                tools.ustr(payroll_admin_user_name or '')[:30].ljust(30) + \
                                tools.ustr(emp_designation)[:30].ljust(30) + \
                                tools.ustr(company_name)[:60].ljust(60) + \
                                tools.ustr(emp_contact).ljust(20) + \
                                tools.ustr(emp_email).ljust(60) + \
                                tools.ustr(context.get('datas')['batch_indicatior'] or '').ljust(1) + \
                                tools.ustr(server_date).ljust(8) + \
                                ''.ljust(30) + \
                                ''.ljust(10) + \
                                ''.ljust(932) + "\r\n"
                tmp_file.write(header_record)
                contract_ids = contract_obj.search([('employee_id', 'in', context.get('employe_id'))])
                for contract in contract_ids:
                    contract_income_tax_rec = hr_contract_income_tax_obj.search([('contract_id', '=', contract.id),
                                                                                 ('start_date', '>=', start_date_year),
                                                                                 ('end_date', '<=', end_date_year)])
                    for income_tax_rec in contract_income_tax_rec:
                        payslip_rec = payslip_obj.search([('date_from', '>=', start_date),
                                                          ('date_from', '<=', end_date),
                                                          ('employee_id', '=', contract.employee_id.id),
                                                          ('state', 'in', ['draft', 'done', 'verify'])])
                        jan_gross_amt = feb_gross_amt = march_gross_amt = apr_gross_amt = may_gross_amt = june_gross_amt = july_gross_amt = aug_gross_amt = sept_gross_amt = oct_gross_amt = nov_gross_amt = dec_gross_amt = 0
                        jan_empoyer_amt = feb_empoyer_amt = march_empoyer_amt = apr_empoyer_amt = may_empoyer_amt = june_empoyer_amt = july_empoyer_amt = aug_empoyer_amt = sept_empoyer_amt = oct_empoyer_amt = nov_empoyer_amt = dec_empoyer_amt = 0
                        jan_empoyee_amt = feb_empoyee_amt = march_empoyee_amt = apr_empoyee_amt = may_empoyee_amt = june_empoyee_amt = july_empoyee_amt = aug_empoyee_amt = sept_empoyee_amt = oct_empoyee_amt = nov_empoyee_amt = dec_empoyee_amt = 0
                        tot_gross_amt = tot_empoyee_amt = tot_empoyer_amt = 0

                        additional_wage_from_date = additional_wage_to_date = fromdate = todate = add_wage_date = eyer_date = eyee_date = ''
                        if income_tax_rec.start_date:
                            fromdate = datetime.datetime.strptime(income_tax_rec.start_date, DEFAULT_SERVER_DATE_FORMAT)
                            form_year = fromdate.year - 1
                            fromdate = str(form_year) + fromdate.strftime('%m%d')
                        if income_tax_rec.end_date:
                            todate = datetime.datetime.strptime(income_tax_rec.end_date, DEFAULT_SERVER_DATE_FORMAT)
                            to_year = todate.year - 1
                            todate = str(to_year) + todate.strftime('%m%d')
                        if income_tax_rec.add_wage_pay_date:
                            add_wage_date = datetime.datetime.strptime(income_tax_rec.add_wage_pay_date, DEFAULT_SERVER_DATE_FORMAT)
                            add_wage_date = add_wage_date.strftime('%Y%m%d')
                        if income_tax_rec.refund_eyers_date:
                            eyer_date = datetime.datetime.strptime(income_tax_rec.refund_eyers_date, DEFAULT_SERVER_DATE_FORMAT)
                            eyer_date = eyer_date.strftime('%Y%m%d')
                        if income_tax_rec.refund_eyees_date:
                            eyee_date = datetime.datetime.strptime(income_tax_rec.refund_eyees_date, DEFAULT_SERVER_DATE_FORMAT)
                            eyee_date = eyee_date.strftime('%Y%m%d')

                        eyer_contibution = eyee_contibution = additional_wage = refund_eyers_contribution = refund_eyers_interest_contribution = refund_eyees_contribution = refund_eyees_interest_contribution = 0
                        eyer_contibution = '%0*d' % (7, int(abs(income_tax_rec.eyer_contibution)))
                        eyee_contibution = '%0*d' % (7, int(abs(income_tax_rec.eyee_contibution)))
                        additional_wage = '%0*d' % (7, int(abs(income_tax_rec.additional_wage)))
                        refund_eyers_contribution = '%0*d' % (7, int(abs(income_tax_rec.refund_eyers_contribution)))
                        refund_eyers_interest_contribution = '%0*d' % (7, int(abs(income_tax_rec.refund_eyers_interest_contribution)))
                        refund_eyees_contribution = '%0*d' % (7, int(abs(income_tax_rec.refund_eyees_contribution)))
                        refund_eyees_interest_contribution = '%0*d' % (7, int(abs(income_tax_rec.refund_eyees_interest_contribution)))
                        if income_tax_rec.additional_wage:
                            additional_wage_from_date = fromdate
                            additional_wage_to_date = todate
                        for payslip in payslip_rec:
                            payslip_month = ''
                            payslip_month = datetime.datetime.strptime(payslip.date_from, DEFAULT_SERVER_DATE_FORMAT)
                            payslip_month = payslip_month.strftime('%m')
                            gross_amt = empoyer_amt = empoyee_amt = 0
                            for line in payslip.line_ids:
                                if line.code == 'GROSS':
                                    gross_amt = line.total
                                if line.category_id.code == 'CAT_CPF_EMPLOYER':
                                    empoyer_amt += line.total
                                if line.category_id.code == 'CAT_CPF_EMPLOYEE':
                                    empoyee_amt += line.total
                            tot_gross_amt += gross_amt
                            tot_empoyer_amt += empoyer_amt
                            tot_empoyee_amt += empoyee_amt

                            if payslip_month == '01':
                                jan_gross_amt = gross_amt
                                jan_empoyer_amt = empoyer_amt
                                jan_empoyee_amt = empoyee_amt
                            if payslip_month == '02':
                                feb_gross_amt = gross_amt
                                feb_empoyer_amt = empoyer_amt
                                feb_empoyee_amt = empoyee_amt
                            if payslip_month == '03':
                                march_gross_amt = gross_amt
                                march_empoyer_amt = empoyer_amt
                                march_empoyee_amt = empoyee_amt
                            if payslip_month == '04':
                                apr_gross_amt = gross_amt
                                apr_empoyer_amt = empoyer_amt
                                apr_empoyee_amt = empoyee_amt
                            if payslip_month == '05':
                                may_gross_amt = gross_amt
                                may_empoyer_amt = empoyer_amt
                                may_empoyee_amt = empoyee_amt
                            if payslip_month == '06':
                                june_gross_amt = gross_amt
                                june_empoyer_amt = empoyer_amt
                                june_empoyee_amt = empoyee_amt
                            if payslip_month == '07':
                                july_gross_amt = gross_amt
                                july_empoyer_amt = empoyer_amt
                                july_empoyee_amt = empoyee_amt
                            if payslip_month == '08':
                                aug_gross_amt = gross_amt
                                aug_empoyer_amt = empoyer_amt
                                aug_empoyee_amt = empoyee_amt
                            if payslip_month == '09':
                                sept_gross_amt = gross_amt
                                sept_empoyer_amt = empoyer_amt
                                sept_empoyee_amt = empoyee_amt
                            if payslip_month == '10':
                                oct_gross_amt = gross_amt
                                oct_empoyer_amt = empoyer_amt
                                oct_empoyee_amt = empoyee_amt
                            if payslip_month == '11':
                                nov_gross_amt = gross_amt
                                nov_empoyer_amt = empoyer_amt
                                nov_empoyee_amt = empoyee_amt
                            if payslip_month == '12':
                                dec_gross_amt = gross_amt
                                dec_empoyer_amt = empoyer_amt
                                dec_empoyee_amt = empoyee_amt

                        jan_gross_amt = '%0*d' % (9, int(abs(jan_gross_amt * 100)))
                        jan_empoyer_amt = '%0*d' % (9, int(abs(jan_empoyer_amt * 100)))
                        jan_empoyee_amt = '%0*d' % (9, int(abs(jan_empoyee_amt * 100)))

                        feb_gross_amt = '%0*d' % (9, int(abs(feb_gross_amt * 100)))
                        feb_empoyer_amt = '%0*d' % (9, int(abs(feb_empoyer_amt * 100)))
                        feb_empoyee_amt = '%0*d' % (9, int(abs(feb_empoyee_amt * 100)))

                        march_gross_amt = '%0*d' % (9, int(abs(march_gross_amt * 100)))
                        march_empoyer_amt = '%0*d' % (9, int(abs(march_empoyer_amt * 100)))
                        march_empoyee_amt = '%0*d' % (9, int(abs(march_empoyee_amt * 100)))

                        apr_gross_amt = '%0*d' % (9, int(abs(apr_gross_amt * 100)))
                        apr_empoyer_amt = '%0*d' % (9, int(abs(apr_empoyer_amt * 100)))
                        apr_empoyee_amt = '%0*d' % (9, int(abs(apr_empoyee_amt * 100)))

                        may_gross_amt = '%0*d' % (9, int(abs(may_gross_amt * 100)))
                        may_empoyer_amt = '%0*d' % (9, int(abs(may_empoyer_amt * 100)))
                        may_empoyee_amt = '%0*d' % (9, int(abs(may_empoyee_amt * 100)))

                        june_gross_amt = '%0*d' % (9, int(abs(june_gross_amt * 100)))
                        june_empoyer_amt = '%0*d' % (9, int(abs(june_empoyer_amt * 100)))
                        june_empoyee_amt = '%0*d' % (9, int(abs(june_empoyee_amt * 100)))

                        july_gross_amt = '%0*d' % (9, int(abs(july_gross_amt * 100)))
                        july_empoyer_amt = '%0*d' % (9, int(abs(july_empoyer_amt * 100)))
                        july_empoyee_amt = '%0*d' % (9, int(abs(july_empoyee_amt * 100)))

                        aug_gross_amt = '%0*d' % (9, int(abs(aug_gross_amt * 100)))
                        aug_empoyer_amt = '%0*d' % (9, int(abs(aug_empoyer_amt * 100)))
                        aug_empoyee_amt = '%0*d' % (9, int(abs(aug_empoyee_amt * 100)))

                        sept_gross_amt = '%0*d' % (9, int(abs(sept_gross_amt * 100)))
                        sept_empoyer_amt = '%0*d' % (9, int(abs(sept_empoyer_amt * 100)))
                        sept_empoyee_amt = '%0*d' % (9, int(abs(sept_empoyee_amt * 100)))

                        oct_gross_amt = '%0*d' % (9, int(abs(oct_gross_amt * 100)))
                        oct_empoyer_amt = '%0*d' % (9, int(abs(oct_empoyer_amt * 100)))
                        oct_empoyee_amt = '%0*d' % (9, int(abs(oct_empoyee_amt * 100)))

                        nov_gross_amt = '%0*d' % (9, int(abs(nov_gross_amt * 100)))
                        nov_empoyer_amt = '%0*d' % (9, int(abs(nov_empoyer_amt * 100)))
                        nov_empoyee_amt = '%0*d' % (9, int(abs(nov_empoyee_amt * 100)))

                        dec_gross_amt = '%0*d' % (9, int(abs(dec_gross_amt * 100)))
                        dec_empoyer_amt = '%0*d' % (9, int(abs(dec_empoyer_amt * 100)))
                        dec_empoyee_amt = '%0*d' % (9, int(abs(dec_empoyee_amt * 100)))

                        tot_gross_amt = '%0*d' % (7, int(abs(tot_gross_amt)))
                        tot_empoyer_amt = '%0*d' % (7, int(abs(tot_empoyer_amt)))
                        tot_empoyee_amt = '%0*d' % (7, int(abs(tot_empoyee_amt)))
                        detail_record = '1'.ljust(1) + \
                                        tools.ustr(contract.employee_id.identification_no or '').ljust(1) + \
                                        tools.ustr(contract.employee_id.identification_id or '')[:12].ljust(12) + \
                                        tools.ustr(contract.employee_id.name or '')[:80].ljust(80) + \
                                        tools.ustr(jan_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(jan_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(jan_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(feb_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(feb_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(feb_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(march_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(march_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(march_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(apr_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(apr_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(apr_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(may_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(may_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(may_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(june_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(june_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(june_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(july_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(july_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(july_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(aug_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(aug_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(aug_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(sept_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(sept_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(sept_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(oct_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(oct_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(oct_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(nov_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(nov_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(nov_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(dec_gross_amt)[:9].ljust(9) + \
                                        tools.ustr(dec_empoyer_amt)[:9].ljust(9) + \
                                        tools.ustr(dec_empoyee_amt)[:9].ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        ''.ljust(9) + \
                                        tools.ustr(tot_gross_amt)[:7].ljust(7) + \
                                        tools.ustr(tot_empoyer_amt)[:7].ljust(7) + \
                                        tools.ustr(tot_empoyee_amt)[:7].ljust(7) + \
                                        ''.ljust(7) + \
                                        ''.ljust(7) + \
                                        ''.ljust(7) + \
                                        tools.ustr('').ljust(8) + \
                                        tools.ustr('').ljust(8) + \
                                        tools.ustr('').ljust(1) + \
                                        tools.ustr('').ljust(1) + \
                                        tools.ustr(income_tax_rec.singapore_permanent_resident_status or '').ljust(1) + \
                                        tools.ustr(income_tax_rec.approval_has_been_obtained_CPF_board or '').ljust(1) + \
                                        tools.ustr(eyer_contibution)[:7].ljust(7) + \
                                        tools.ustr(eyee_contibution)[:7].ljust(7) + \
                                        tools.ustr(additional_wage)[:7].ljust(7) + \
                                        tools.ustr(additional_wage_from_date).ljust(8) + \
                                        tools.ustr(additional_wage_to_date).ljust(8) + \
                                        tools.ustr(add_wage_date).ljust(8) + \
                                        tools.ustr(refund_eyers_contribution)[:7].ljust(7) + \
                                        tools.ustr(refund_eyers_interest_contribution)[:7].ljust(7) + \
                                        tools.ustr(eyer_date).ljust(8) + \
                                        tools.ustr(refund_eyees_contribution)[:7].ljust(7) + \
                                        tools.ustr(refund_eyees_interest_contribution)[:7].ljust(7) + \
                                        tools.ustr(eyee_date).ljust(8) + \
                                        tools.ustr(additional_wage)[:7].ljust(7) + \
                                        tools.ustr(additional_wage_from_date).ljust(8) + \
                                        tools.ustr(additional_wage_to_date).ljust(8) + \
                                        tools.ustr(add_wage_date).ljust(8) + \
                                        tools.ustr(refund_eyers_contribution)[:7].ljust(7) + \
                                        tools.ustr(refund_eyers_interest_contribution)[:7].ljust(7) + \
                                        tools.ustr(eyer_date).ljust(8) + \
                                        tools.ustr(refund_eyees_contribution)[:7].ljust(7) + \
                                        tools.ustr(refund_eyees_interest_contribution)[:7].ljust(7) + \
                                        tools.ustr(eyee_date).ljust(8) + \
                                        tools.ustr(additional_wage)[:7].ljust(7) + \
                                        tools.ustr(additional_wage_from_date).ljust(8) + \
                                        tools.ustr(additional_wage_to_date).ljust(8) + \
                                        tools.ustr(add_wage_date).ljust(8) + \
                                        tools.ustr(refund_eyers_contribution)[:7].ljust(7) + \
                                        tools.ustr(refund_eyers_interest_contribution)[:7].ljust(7) + \
                                        tools.ustr(eyer_date).ljust(8) + \
                                        tools.ustr(refund_eyees_contribution)[:7].ljust(7) + \
                                        tools.ustr(refund_eyees_interest_contribution)[:7].ljust(7) + \
                                        tools.ustr(eyee_date).ljust(8) + \
                                        ''.ljust(107) + \
                                        ''.ljust(50) + \
                                         "\r\n"
                        tmp_file.write(detail_record)
            finally:
                if tmp_file:
                    tmp_file.close()
            file = open(tgz_tmp_filename, "rb")
            out = file.read()
            file.close()
            res = base64.b64encode(out)
            module_rec = self.env['binary.ir8s.text.file.wizard'].create({'name': 'IR8S.txt', 'ir8s_txt_file' : res})
            return {
                  'name': _('Binary'),
                  'res_id' : module_rec.id,
                  'view_type': 'form',
                  "view_mode": 'form',
                  'res_model': 'binary.ir8s.text.file.wizard',
                  'type': 'ir.actions.act_window',
                  'target': 'new',
                  'context': context}
        elif data.get('print_type', '') == 'pdf':
            data = {
                'ids' : [],
                'model' : 'hr.payslip',
                'form' : data
            }
            ret = {
                'type' : 'ir.actions.report.xml',
                'report_name' : 'sg_income_tax_report.ir8s_incometax_form_report',
                'datas' : data
            }
        return ret

emp_ir8s_text_file()

class binary_ir8s_text_file_wizard(models.TransientModel):
    _name = 'binary.ir8s.text.file.wizard'

    name = fields.Char('Name', size = 64, default = 'IR8S.txt')
    ir8s_txt_file = fields.Binary('Click On Download Link To Download File', readonly = True)

binary_ir8s_text_file_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
