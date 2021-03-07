# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from odoo import api, models,tools,_
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ppd_appendix8a_form(models.AbstractModel):

    _name = "report.sg_appendix8a_report.report_appendix8a"

    @api.multi
    def get_employee(self, data):
        result = []
        hr_contract_income_tax = self.env['hr.contract.income.tax']
        contract_ids = self.env['hr.contract'].search([('employee_id','in',data.get('employee_ids',[]))])
        if len(contract_ids.ids) == 0:
            raise Warning(_('No Contract found for selected dates'))
        furniture_value_indicator = pioneer_service = employer_name = employer_address = authorized_person = batchdate =''
        autho_person_desg = autho_person_tel = last_year=''

        from_date = to_date = start_date = end_date = False
        if data.get('start_date', False) and data.get('end_date', False):
            from_date = datetime.datetime.strptime(data.get('start_date', False), DEFAULT_SERVER_DATE_FORMAT)
            to_date = datetime.datetime.strptime(data.get('end_date', False), DEFAULT_SERVER_DATE_FORMAT)
            fiscal_start = from_date.year - 1
            fiscal_end = to_date.year - 1
            start_date = '%s-01-01' % tools.ustr(int(fiscal_start))
            end_date = '%s-12-31' % tools.ustr(int(fiscal_end))
            start_date = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
        if data.get('payroll_user'):
            payroll_use_id = int(data['payroll_user'])
            authorized_person = self.env['res.users'].browse(payroll_use_id).name
            payroll_emp = self.env['hr.employee'].search([('user_id','=',payroll_use_id)])
            if len(payroll_emp.ids) != 0:
                premp_brw = payroll_emp[0]
                autho_person_desg = premp_brw.job_id and premp_brw.job_id.id and premp_brw.job_id.name or ''
                autho_person_tel = premp_brw.work_phone  or ''
        if data.get('batch_date'):
            batchdate = datetime.datetime.strptime(data['batch_date'], DEFAULT_SERVER_DATE_FORMAT)
            batchdate = batchdate.strftime('%d/%m/%Y')
        for contract in contract_ids:
            contract_income_tax_ids = hr_contract_income_tax.search([('contract_id','=',contract.id),
                                                                     ('start_date', '>=', from_date),
                                                                     ('end_date', '<=', to_date)], limit=1)
            if contract_income_tax_ids and contract_income_tax_ids.ids:
                for rec in contract_income_tax_ids[0]:
                    from_sg_date = to_sg_date = ''
                    if rec.furniture_value_indicator:
                        furniture_value_indicator = dict(hr_contract_income_tax.fields_get(allfields=['furniture_value_indicator'])['furniture_value_indicator']['selection'])[rec.furniture_value_indicator]
                    if rec.pioneer_service:
                        pioneer_service = dict(hr_contract_income_tax.fields_get(allfields=['pioneer_service'])['pioneer_service']['selection'])[rec.pioneer_service]
                    if contract.employee_id.address_id and contract.employee_id.address_id.id:
                        employer_name = contract.employee_id.address_id.name
                        employer_address = str(contract.employee_id.address_id.house_no or '') + str(contract.employee_id.address_id.street or '') + ',' + str(contract.employee_id.address_id.street2 or '')
                        if contract.employee_id.address_id.state_id:
                          employer_address += ' , '
                          employer_address += contract.employee_id.address_id.state_id.name
                        if contract.employee_id.address_id.country_id:
                          employer_address += ' , '
                          employer_address += contract.employee_id.address_id.country_id.name
                        if contract.employee_id.address_id.zip:
                          employer_address += ' '
                          employer_address += contract.employee_id.address_id.zip
                    if rec.from_date:
                        from_sgdate = datetime.datetime.strptime(rec.from_date, DEFAULT_SERVER_DATE_FORMAT)
                        from_sg_date = from_sgdate.strftime('%d/%m/%Y')
                    if rec.to_date:
                        to_sgdate = datetime.datetime.strptime(rec.to_date, DEFAULT_SERVER_DATE_FORMAT)
                        to_sg_date = to_sgdate.strftime('%d/%m/%Y')
                    if from_date:
                        last_year=  fiscal_start or ''
                    result.append({'year_id':from_date.year or '',
                                   'last_year':last_year,
                                   'employee_name':contract.employee_id.name,
                                   'address': rec.address,
                                   'from_date':from_sg_date,
                                   'to_date':to_sg_date,
                                   'no_of_days':rec.no_of_days,
                                   'no_of_emp':rec.no_of_emp,
                                   'annual_value':rec.annual_value,
                                   'furniture_value_indicator':furniture_value_indicator,
                                   'furniture_value':rec.furniture_value,
                                   'rent_landlord':rec.rent_landloard,
                                   'place_of_residence_taxable_value':rec.place_of_residence_taxable_value,
                                   'total_rent_paid':rec.total_rent_paid,
                                   'total_taxable_value':rec.total_taxable_value,
                                   'utilities_misc_value':rec.utilities_misc_value,
                                   'driver_value':rec.driver_value,
                                   'employer_paid_amount':rec.employer_paid_amount,
                                   'taxalble_value_of_utilities_housekeeping':rec.taxalble_value_of_utilities_housekeeping,
                                   'actual_hotel_accommodation':rec.actual_hotel_accommodation,
                                   'employee_paid_amount':rec.employee_paid_amount,
                                   'taxable_value_of_hotel_acco':rec.taxable_value_of_hotel_acco,
                                   'cost_of_home_leave_benefits':rec.cost_of_home_leave_benefits,
                                   'no_of_passanger':rec.no_of_passanger,
                                   'spouse':rec.spouse,
                                   'children':rec.children,
                                   'pioneer_service':pioneer_service,
                                   'interest_payment':rec.interest_payment,
                                   'insurance_payment':rec.insurance_payment,
                                   'free_holidays':rec.free_holidays,
                                   'edu_expenses':rec.edu_expenses,
                                   'non_monetary_awards':rec.non_monetary_awards,
                                   'entrance_fees':rec.entrance_fees,
                                   'gains_from_assets':rec.gains_from_assets,
                                   'cost_of_motor':rec.cost_of_motor,
                                   'car_benefits':rec.car_benefits,
                                   'non_monetary_benefits':rec.non_monetary_benefits,
                                   'total_value_of_benefits':rec.total_value_of_benefits,
                                   'employer_name':employer_name,
                                   'employer_address':employer_address,
                                   'authorized_person': authorized_person,
                                   'autho_person_desg' :autho_person_desg,
                                   'autho_person_tel':autho_person_tel,
                                   'org_id_no':contract.employee_id.identification_id or '',
                                   'batchdate':batchdate or ''
                            })
        return result

    @api.multi
    def render_html(self,docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        datas = docs.read([])[0]
        report_lines = self.get_employee(datas)
        docargs = {'doc_ids': self.ids,
                   'doc_model': self.model,
                   'data': datas,
                   'docs': docs,
                   'time': time,
                   'get_employee' : report_lines}
        return self.env['report'].render('sg_appendix8a_report.report_appendix8a', docargs)

