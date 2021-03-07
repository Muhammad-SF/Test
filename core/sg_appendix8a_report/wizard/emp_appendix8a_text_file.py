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
from time import gmtime, strftime
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError,Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class emp_appendix8a_text_file(models.TransientModel):

    _name = 'emp.appendix8a.text.file'


    @api.multi
    def _get_payroll_user_name(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        supervisors_list = [(False,'')]
        result_data = self.env['ir.model.data']._get_id('l10n_sg_hr_payroll', 'group_hr_payroll_admin')
        model_data = self.env['ir.model.data'].browse(result_data)
        group_data = self.env['res.groups'].browse(model_data.res_id)
        for user in group_data.users:
            supervisors_list.append((tools.ustr(user.id), tools.ustr(user.name)))
        return supervisors_list

    employee_ids = fields.Many2many('hr.employee', 'hr_employe_appendix8a_text_rel', 'emp_id', 'employee_id', 'Employee', required=False)
    start_date = fields.Date('Start Date', required=True, default=lambda *a: time.strftime('%Y-01-01'))
    end_date = fields.Date('End Date', required=True, default=lambda *a: time.strftime('%Y-12-31'))
    source = fields.Selection([('1', 'Mindef'), ('4', 'Government Department'), ('5', 'Statutory Board'),
                                ('6', 'Private Sector'), ('9', 'Others')], string='Source',default='6')
    organization_id_type =  fields.Selection([('7', 'UEN – Business Registration number issued by ACRA'),
                                              ('8', 'UEN – Local Company Registration number issued by ACRA'),
                                              ('A', 'ASGD – Tax Reference number assigned by IRAS'),
                                              ('I', 'ITR – Income Tax Reference number assigned by IRAS'),
                                              ('U', 'UENO – Unique Entity Number Others')], string='Organization ID Type',default='8')
    organization_id_no =  fields.Char('Organization ID No', size=16)
    batch_indicatior =  fields.Selection([('O', 'Original'), ('A', 'Amendment')], string='Batch Indicator')
    batch_date =  fields.Date('Batch Date', default=fields.Date.today)
    payroll_user =  fields.Selection(_get_payroll_user_name, 'Name of authorised person', size=128)
    print_type =  fields.Selection([('text','Text'), ('pdf', 'PDF')], 'Print as', required=True,default='text')
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
    def download_appendix8a_txt_file(self):
        context = self.env.context
        if context is None:
            context = {}
        context = dict(context)
        context.update({'active_test': False})
        data = self.read([])[0]
        start_year = datetime.datetime.strptime(data.get('start_date',False), '%Y-%m-%d').strftime('%Y')
        to_year = datetime.datetime.strptime(data.get('end_date',False), '%Y-%m-%d').strftime('%Y')
        start_date = '%s-01-01' % tools.ustr(int(start_year) - 1)
        end_date = '%s-12-31' % tools.ustr(int(to_year) - 1)
        start_date_year = '%s-01-01' % tools.ustr(int(start_year))
        end_date_year = '%s-12-31' % tools.ustr(int(to_year))
        if data.has_key('start_date') and data.has_key('end_date') and data.get('start_date',False) >= data.get('end_date',False):
            raise ValidationError(_("You must be enter start date less than end date !"))
        context.update({'employe_id': data['employee_ids'], 'datas': data})
        if data.get('print_type', '') == 'text':
            tgz_tmp_filename = tempfile.mktemp('.' + "txt")
            tmp_file = False
            start_date = end_date = prev_yr_start_date = prev_yr_end_date = False
            from_date = context.get('datas',False).get('start_date',False) or False
            to_date = context.get('datas',False).get('end_date',False) or False
            if from_date and to_date:
                from_date =  datetime.datetime.strptime(from_date, DEFAULT_SERVER_DATE_FORMAT)
                to_date =  datetime.datetime.strptime(to_date, DEFAULT_SERVER_DATE_FORMAT)
                basis_year = tools.ustr(from_date.year - 1)
                fiscal_start_date = '%s0101' % tools.ustr(int(from_date.year - 1))
                fiscal_end_date = '%s1231' % tools.ustr(int(from_date.year) - 1)
                start_date = '%s-01-01' % tools.ustr(int(from_date.year) - 1)
                end_date = '%s-12-31' % tools.ustr(int(from_date.year) - 1)
                start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
            try:
                tmp_file = open(tgz_tmp_filename, "wr")
                batchdate = datetime.datetime.strptime(context.get('datas')['batch_date'], DEFAULT_SERVER_DATE_FORMAT)
                batchdate = batchdate.strftime('%Y%m%d')
                server_date = basis_year + strftime("%m%d", gmtime())
                emp_rec = self.env['hr.employee'].search([('user_id', '=', int(context.get('datas')['payroll_user']))])
                emp_designation = ''
                emp_contact = ''
                emp_email = ''
                user_brw = self.env['res.users'].browse(int(context.get('datas')['payroll_user']))
                payroll_admin_user_name = user_brw.name
                company_name = user_brw.company_id.name
                for emp in emp_rec:
                    emp_designation = emp.job_id.name
                    emp_email = emp.work_email
                    emp_contact = emp.work_phone
                """ Header for Appendix8A """
                header_record = '0'.ljust(1) + \
                                tools.ustr(context.get('datas')['source'] or '').ljust(1) + \
                                tools.ustr(basis_year or '').ljust(4) + \
                                tools.ustr(context.get('datas')['organization_id_type'] or '').ljust(1) + \
                                tools.ustr(context.get('datas')['organization_id_no'] or '').ljust(12) + \
                                tools.ustr(payroll_admin_user_name or '')[:30].ljust(30) + \
                                tools.ustr(emp_designation or '')[:30].ljust(30) + \
                                tools.ustr(company_name)[:60].ljust(60) + \
                                tools.ustr(emp_contact)[:20].ljust(20) + \
                                tools.ustr(emp_email)[:60].ljust(60) + \
                                tools.ustr(context.get('datas')['batch_indicatior'] or '').ljust(1) + \
                                tools.ustr(batchdate).ljust(8) + \
                                ''.ljust(30) + \
                                ''.ljust(10) + \
                                ''.ljust(432) + \
                                "\r\n"
                tmp_file.write(header_record)
                
                """ get the contract for selected employee"""
                contract_ids = self.env['hr.contract'].search([('employee_id','in',context.get('employe_id'))])
                from_date = to_date = ''
                for contract in contract_ids:
                    contract_income_tax_ids = self.env['hr.contract.income.tax'].search([('contract_id','=',contract.id),
                                                                                         ('start_date', '>=', start_date_year),
                                                                                         ('end_date', '<=', end_date_year)])
                    if not contract.employee_id.identification_id:
                        raise ValidationError(_('There is no identification no define for %s employee.' % (contract.employee_id.name)))
                    if contract_income_tax_ids and contract_income_tax_ids.ids:
                        for emp in contract_income_tax_ids[0]:
                            if emp.from_date:
                                from_date = datetime.datetime.strptime(emp.from_date, DEFAULT_SERVER_DATE_FORMAT)
                                from_date = from_date.strftime('%Y%m%d')
                            if emp.to_date:
                                to_date = datetime.datetime.strptime(emp.to_date, DEFAULT_SERVER_DATE_FORMAT)
                                to_date = to_date.strftime('%Y%m%d')
                            annual_value=rent_landloard=place_of_residence_taxable_value=total_rent_paid=0
                            utilities_misc_value=driver_value=employer_paid_amount=taxalble_value_of_utilities_housekeeping=''
                            actual_hotel_accommodation=employee_paid_amount=taxable_value_of_hotel_acco=''
                            cost_of_home_leave_benefits=interest_payment=insurance_payment=free_holidays=edu_expenses=''
                            non_monetary_awards=entrance_fees=gains_from_assets=cost_of_motor=car_benefits=non_monetary_benefits=''
                            """ string variable declaration"""
                            pioneer_service = furniture_value = total_taxable_value= address= ''

                            annual_value = self.generate_export_field_value(9, float(abs(emp.annual_value)))

                            """Must be blank if item annual_value(6a) is not blank or > zero """
                            if int(emp.annual_value) > 0:
                                rent_landloard = ''
                            else:
                                rent_landloard = self.generate_export_field_value(9, float(abs(emp.rent_landloard)))
                                #rent_landloard = '%0*d' % (9, int(abs(emp.rent_landloard)))
                            line11 = line22 = line33 = ''
                            if int(emp.annual_value) > 0 or emp.rent_landloard > 0:
                                if not emp.address:
                                    raise ValidationError(_('There is no address define for %s employee.' % (contract.employee_id.name)))
                                if emp.address:
                                    emp_address = str(emp.address)
                                    demo_lst = list(emp_address)
                                    line1 = []
                                    line2 = []
                                    line3 = []
                                    indexes = [i for i,x in enumerate(demo_lst) if x == '\n']
                                    if len(indexes) == 0:
                                        address = emp_address
                                    elif len(indexes) == 1:
                                        for lst in range(0,indexes[0]):
                                            line1.append(demo_lst[lst])
                                        for lst1 in range(int(indexes[0]) + 1, len(demo_lst)):
                                            line2.append(demo_lst[lst1])
                                    elif len(indexes) == 2:
                                        for lst in range(0,indexes[0]):
                                            line1.append(demo_lst[lst])
                                        for lst1 in range(int(indexes[0]) + 1, int(indexes[1])):
                                            line2.append(demo_lst[lst1])
                                        for lst2 in range(int(indexes[1]) + 1, len(demo_lst)):
                                            line3.append(demo_lst[lst2])
                                    line11 = ''.join(line1)
                                    line22 = ''.join(line2)
                                    line33 = ''.join(line3)
                            """ Cannot be blank when Value of Furniture & Fitting indicator is not blank."""
                            if emp.furniture_value_indicator:
                                if int(emp.furniture_value) < 0:
                                    raise Warning(_('Cannot be blank or zero when Value of Furniture & Fitting indicator is not blank.'))
                                else:

                                    furniture_value = self.generate_export_field_value(9, float(abs(emp.furniture_value)))
                                    #furniture_value = '%0*d' % (9, int(abs(emp.furniture_value)))
                            
                            """No of employee cannot be blank when annual value or  rent paid to landlord is not blank or not zero"""
                            no_of_emp = 0
                            if (emp.annual_value) > 0 or (emp.rent_landloard) > 0:
                                if (emp.no_of_emp) == 0:
                                    raise Warning(_('No of employee can not be zero or blank when annual value or rent paid to landlord is not blank'))
                                else:
                                    no_of_emp = '%0*d' % (2, int(emp.no_of_emp))
                                
                            """ If not blank, must be Y or N."""
#                            if emp.pioneer_service == 'yes':
#                                pioneer_service = 'Y'
#                            elif emp.pioneer_service == 'no':
#                                pioneer_service = 'N'
#                            else:  
#                                pioneer_service = ''
#                                
#                            if not emp.pioneer_service:
#                                cost_of_home_leave_benefits = ''
#                            else:
                            #cost_of_home_leave_benefits = '%0*d' % (9, int(abs(emp.cost_of_home_leave_benefits)))
                            cost_of_home_leave_benefits = self.generate_export_field_value(9, float(abs(emp.cost_of_home_leave_benefits)))

                            place_of_residence_taxable_value = self.generate_export_field_value(9, float(abs(emp.place_of_residence_taxable_value)))
                            #place_of_residence_taxable_value = '%0*d' % (9, abs(emp.place_of_residence_taxable_value))

                            #total_rent_paid = '%0*d' % (9, abs(emp.total_rent_paid))
                            total_rent_paid = self.generate_export_field_value(9, float(abs(emp.total_rent_paid)))

                            #utilities_misc_value = '%0*d' % (9, int(abs(emp.utilities_misc_value)))
                            utilities_misc_value = self.generate_export_field_value(9, float(abs(emp.utilities_misc_value)))

                            #driver_value = '%0*d' % (9, int(abs(emp.driver_value)))
                            driver_value = self.generate_export_field_value(9, float(abs(emp.driver_value)))

                            #employer_paid_amount = '%0*d' % (9, int(abs(emp.employer_paid_amount)))
                            employer_paid_amount = self.generate_export_field_value(9, float(abs(emp.employer_paid_amount)))

                            #taxalble_value_of_utilities_housekeeping = '%0*d' % (9, int(abs(emp.taxalble_value_of_utilities_housekeeping)))
                            taxalble_value_of_utilities_housekeeping = self.generate_export_field_value(9, float(abs(emp.taxalble_value_of_utilities_housekeeping)))

                            #actual_hotel_accommodation = '%0*d' % (9, int(abs(emp.actual_hotel_accommodation)))
                            actual_hotel_accommodation = self.generate_export_field_value(9, float(abs(emp.actual_hotel_accommodation)))

                            #employee_paid_amount = '%0*d' % (9, int(abs(emp.employee_paid_amount)))
                            employee_paid_amount = self.generate_export_field_value(9, float(abs(emp.employee_paid_amount)))


                            actual_taxable_value_of_hotel_acco = float(emp.taxable_value_of_hotel_acco)
                            if actual_taxable_value_of_hotel_acco < 0:
                                taxable_value_of_hotel_acco = '%0*d' % (9, 0)
                            else:
                                #taxable_value_of_hotel_acco = '%0*d' % (9, int(abs(emp.taxable_value_of_hotel_acco)))
                                taxable_value_of_hotel_acco = self.generate_export_field_value(9, float(abs(emp.taxable_value_of_hotel_acco)))


                            #interest_payment = '%0*d' % (9, int(abs(emp.interest_payment)))
                            interest_payment = self.generate_export_field_value(9, float(abs(emp.interest_payment)))

                            #insurance_payment = '%0*d' % (9, int(abs(emp.insurance_payment)))
                            insurance_payment = self.generate_export_field_value(9, float(abs(emp.insurance_payment)))

                            #free_holidays = '%0*d' % (9, int(abs(emp.free_holidays)))
                            free_holidays = self.generate_export_field_value(9, float(abs(emp.free_holidays)))

                            #edu_expenses = '%0*d' % (9, int(abs(emp.edu_expenses)))
                            edu_expenses = self.generate_export_field_value(9, float(abs(emp.edu_expenses)))

                            #non_monetary_awards = '%0*d' % (9, int(abs(emp.non_monetary_awards)))
                            non_monetary_awards = self.generate_export_field_value(9, float(abs(emp.non_monetary_awards)))

                            #entrance_fees = '%0*d' % (9, int(abs(emp.entrance_fees)))
                            entrance_fees = self.generate_export_field_value(9, float(abs(emp.entrance_fees)))

                            #gains_from_assets = '%0*d' % (9, int(abs(emp.gains_from_assets)))
                            gains_from_assets = self.generate_export_field_value(9, float(abs(emp.gains_from_assets)))

                            #cost_of_motor = '%0*d' % (9, int(abs(emp.cost_of_motor)))
                            cost_of_motor = self.generate_export_field_value(9, float(abs(emp.cost_of_motor)))

                            #car_benefits = '%0*d' % (9, int(abs(emp.car_benefits)))
                            car_benefits = self.generate_export_field_value(9, float(abs(emp.car_benefits)))

                            #non_monetary_benefits = '%0*d' % (9, int(abs(emp.non_monetary_benefits)))
                            non_monetary_benefits = self.generate_export_field_value(9, float(abs(emp.non_monetary_benefits)))

                            no_of_passanger = '%0*d' % (3, int(abs(emp.no_of_passanger)))
                            spouse = '%0*d' % (2, int(abs(emp.spouse)))
                            children = '%0*d' % (2, int(abs(emp.children)))
                            
                            """ 6f = 6d – 6e"""
                            #total_taxable_value = '%0*d' % (9, int(abs(emp.total_taxable_value)))
                            total_taxable_value = self.generate_export_field_value(9, float(abs(emp.total_taxable_value)))
                            
                            """ Value must be the sum of item 6f, 6j, 7c, 8a to 8k."""    
                            #total_value_of_benefits = '%0*d' % (9, int(abs(emp.total_value_of_benefits)))
                            total_value_of_benefits = self.generate_export_field_value(9,float(abs(emp.total_value_of_benefits)))


                            detail_record = '1'.ljust(1) + \
                                            tools.ustr(contract.employee_id.identification_no or '').ljust(1) + \
                                            tools.ustr(contract.employee_id.identification_id or '')[:12].ljust(12) + \
                                            tools.ustr(contract.employee_id.name or '')[:40].ljust(40) + \
                                            ''.ljust(40) + \
                                            tools.ustr(line11 or '')[:30].ljust(30) + \
                                            tools.ustr(line22 or '')[:30].ljust(30) + \
                                            tools.ustr(line33 or '')[:30].ljust(30) + \
                                            tools.ustr(from_date)[:8].ljust(8) + \
                                            tools.ustr(to_date)[:8].ljust(8) + \
                                            tools.ustr(emp.no_of_days)[:3].ljust(3) +\
                                            tools.ustr(no_of_emp)[:2].ljust(2) +\
                                            tools.ustr(annual_value)[:9].ljust(9,'0') +\
                                            tools.ustr(emp.furniture_value_indicator or '')[:1].ljust(1) +\
                                            tools.ustr(furniture_value)[:9].ljust(9) +\
                                            tools.ustr(rent_landloard)[:9].ljust(9) +\
                                            tools.ustr(place_of_residence_taxable_value)[:9].ljust(9) +\
                                            tools.ustr(total_rent_paid)[:9].ljust(9) +\
                                            tools.ustr(total_taxable_value)[:9].ljust(9) +\
                                            tools.ustr(utilities_misc_value)[:9].ljust(9) +\
                                            tools.ustr(driver_value)[:9].ljust(9) +\
                                            tools.ustr(employer_paid_amount)[:9].ljust(9) +\
                                            tools.ustr(taxalble_value_of_utilities_housekeeping)[:9].ljust(9) +\
                                            tools.ustr(actual_hotel_accommodation)[:9].ljust(9) +\
                                            tools.ustr(employee_paid_amount)[:9].ljust(9) +\
                                            tools.ustr(taxable_value_of_hotel_acco)[:9].ljust(9) +\
                                            tools.ustr(cost_of_home_leave_benefits)[:9].ljust(9) +\
                                            tools.ustr(no_of_passanger)[:2].ljust(2) +\
                                            tools.ustr(spouse)[:2].ljust(2) +\
                                            tools.ustr(children)[:2].ljust(2) +\
                                            tools.ustr('')[:1].ljust(1) +\
                                            tools.ustr(interest_payment)[:9].ljust(9) +\
                                            tools.ustr(insurance_payment)[:9].ljust(9) +\
                                            tools.ustr(free_holidays)[:9].ljust(9) +\
                                            tools.ustr(edu_expenses)[:9].ljust(9) +\
                                            tools.ustr(non_monetary_awards)[:9].ljust(9) +\
                                            tools.ustr(entrance_fees)[:9].ljust(9) +\
                                            tools.ustr(gains_from_assets)[:9].ljust(9) +\
                                            tools.ustr(cost_of_motor)[:9].ljust(9) +\
                                            tools.ustr(car_benefits)[:9].ljust(9) +\
                                            tools.ustr(non_monetary_benefits)[:9].ljust(9) +\
                                            tools.ustr(total_value_of_benefits)[:9].ljust(9) +\
                                            ''.ljust(212) +\
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
            module_rec = self.env['binary.appendix8a.text.file.wizard'].create({'name': 'appendix8a.txt', 'appendix8a_txt_file' : res})
            return {
              'name': _('Binary'),
              'res_id' : module_rec.id,
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'binary.appendix8a.text.file.wizard',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': context,
            }
        elif data.get('print_type', '') == 'pdf':
            data = {
                'ids' : [],
                'model' : 'hr.payslip',
                'form' : data
            }
            ret =  {
                'type' : 'ir.actions.report.xml',
                'report_name': 'sg_appendix8a_report.report_appendix8a',
                'datas' : data
            }
        return ret


emp_appendix8a_text_file()

class binary_appendix8a_text_file_wizard(models.TransientModel):

    _name = 'binary.appendix8a.text.file.wizard'

    name = fields.Char('Name', size=64, default='appendix8a.txt')
    appendix8a_txt_file = fields.Binary('Click On Download Link To Download File', readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: