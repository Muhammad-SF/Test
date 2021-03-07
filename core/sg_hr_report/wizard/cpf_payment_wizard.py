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
import xlwt
import base64
import tempfile
from datetime import datetime
from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class cpf_payment_wizard(models.TransientModel):

    _name = 'cpf.payment.wizard'

    employee_ids = fields.Many2many('hr.employee', 'cpf_employee_rel', 'wizard_id', 'employee_id', 'Employees')
    date_start = fields.Date('Date Start', default=lambda *a: time.strftime('%Y-%m-01'))
    date_stop = fields.Date('Date Stop', default=lambda *a: str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10])
    export_report = fields.Selection([('pdf', 'PDF'), ('excel', 'Excel')], "Export", default='pdf')


    @api.multi
    def get_pdf_data(self):
        cpf_binary_obj = self.env['cpf.binary.wizard']
        cr, uid, context = self.env.args
        if context is None: context = {}
        context = dict(context)
        payment_wiz_data = self.read([])
        data = {}
        if payment_wiz_data:
            data = payment_wiz_data[0]
        start_date = data.get('date_start', False) or False
        stop_date = data.get('date_stop', False) or False
        end_date = data.get('date_stop', False) or False
        emp_ids = data.get('employee_ids', False) or []

        context.update({'employee_id': emp_ids, 'date_start': start_date, 'date_stop': end_date})

        final_result = {}
        final_data = []

        # static data
        emp_obj = self.env['hr.employee']
        payslip_obj = self.env['hr.payslip']
        hr_contract_obj = self.env['hr.contract']
        month_dict = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May',
                      '06': 'June',
                      '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November',
                      '12': 'December'}
        period = month_dict.get(start_date.split('-')[1]) + ', ' + start_date.split('-')[0]

        # static data
        cr, uid, context = self.env.args
        company_data = self.env['res.users'].browse(uid).company_id
        company_dict = {
            'name': company_data.name,
            'street': company_data.street,
            'address': str(company_data and company_data.street2 or ' ') + ' ' + str(
                company_data and company_data.country_id and company_data.country_id.name or '') + ' ' + str(
                company_data.zip or ''),
            'telephone': str(company_data.phone or ' '),
            'fax': str(company_data.fax or ''),
            'code': str(company_data.company_code or ''),
            'date': datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y'),
            'period': period
        }
        final_result.update(company_dict)

        t_cpfsdl_amount = t_p_cpf_sdl_amount = t_p_fwl_amount = t_p_cpf_amount = t_gross_amount = t_ecf_amount = t_cdac_amount = t_sinda_amount = t_mbmf_amount = t_cpf_amount = 0.00
        total_additional_amount = total_cpfsdl_amount = total_p_cpf_amount = total_gross_amount = total_ecf_amount = total_cdac_amount = total_sinda_amount = total_mbmf_amount = total_cpf_amount = 0.00
        emp_cpfsdl_amount = emp_sdl_amount = emp_ecf_amount = emp_fwl_amount = emp_cdac_amount = emp_sinda_amount = emp_mbmf_amount = emp_cpf_amount = 0.00

        join_date = start_date
        emply_ids = emp_obj.search([('id', 'in', emp_ids)])

        employee_no_category_total = {}
        employee_dict = {}
        cpf_amount_dict = {}
        employee_no_category = {}
        for emp_record in emply_ids:
            payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id),
                                              ('date_from', '>=', start_date),
                                              ('date_from', '<=', stop_date),
                                              ('state', 'in', ['draft', 'done', 'verify'])])
            previous_date = cpf_binary_obj._default_previous_date(start_date)
            previous_payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id)],
                                                      order='date_from ASC',
                                                      limit=1)
            if previous_payslip_ids:
                join_date = previous_payslip_ids.date_from
            while (join_date <= previous_date[0]):
                previous_payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id),
                                                           ('date_from', '>=', previous_date[0]),
                                                           ('date_from', '<=', previous_date[1]),
                                                           ('state', 'in', ['draft', 'done', 'verify'])])
                if previous_payslip_ids:
                    break
                else:
                    previous_date = cpf_binary_obj._default_previous_date(previous_date[0])
            if not payslip_ids:
                raise ValidationError(_('There is no payslip details between selected date %s and %s') %(previous_date[0], previous_date[1]))
            additional_amount = cpfsdl_amount = p_cpf_amount = gross_amount = ecf_amount = fwl_amount = cdac_amount = sinda_amount = mbmf_amount = cpf_amount = 0.00

            for payslip_rec in payslip_ids:
                for line in payslip_rec.line_ids:
                    if line.register_id.name == 'CPF':
                        cpf_amount += line.amount
                    if line.register_id.name == 'CPF - MBMF':
                        mbmf_amount += line.amount
                    if line.register_id.name == 'CPF - SINDA':
                        sinda_amount += line.amount
                    if line.register_id.name == 'CPF - CDAC':
                        cdac_amount += line.amount
                    if line.register_id.name == 'CPF - ECF':
                        ecf_amount += line.amount
                    if line.register_id.name == 'CPF - FWL':
                        fwl_amount += line.amount
                        t_p_fwl_amount += line.amount
                    if line.register_id and line.register_id.name == 'BONUS':
                        gross_amount -= line.amount
                    if line.category_id.code == 'GROSS':
                        gross_amount += line.amount
                    if line.code == 'CPFSDL':
                        cpfsdl_amount += line.amount
                        t_p_cpf_sdl_amount += line.amount
                    if line.register_id and line.register_id.name == 'BONUS':
                        additional_amount += line.amount
            cpf_amount_dict.update({
                'amount_cpf': cpf_amount,
                'amount_mbmf': mbmf_amount,
                'amount_sinda': sinda_amount,
                'amount_cdac': cdac_amount,
                'amount_ecf': ecf_amount,
                'amount_fwl': fwl_amount,
                'amount_t_p_fwl': t_p_fwl_amount,
                'amount_gross': gross_amount,
                'amount_cpfsdl': cpfsdl_amount,
                'amount_t_p_cpf_sdl': t_p_cpf_sdl_amount,
                'amount_additional': additional_amount,
            })

            if not gross_amount:
                continue
            if not cpf_amount and not mbmf_amount and not sinda_amount and not cdac_amount and not ecf_amount and not cpfsdl_amount:
                continue

            # previous cpf
            if previous_payslip_ids:
                if payslip_rec.date_from != payslip_rec.date_from:
                    for previous_line in previous_payslip_ids.line_ids:
                        if previous_line.register_id.name == 'CPF':
                            p_cpf_amount += previous_line.amount
            # Counts Employee
            if fwl_amount:
                emp_fwl_amount += 1
            if cpf_amount != 0:
                emp_cpf_amount += 1
            if mbmf_amount != 0:
                emp_mbmf_amount += 1
            if sinda_amount != 0:
                emp_sinda_amount += 1
            if cdac_amount != 0:
                emp_cdac_amount += 1
            if ecf_amount != 0:
                emp_ecf_amount += 1
            if cpfsdl_amount != 0:
                emp_sdl_amount += 1

            # writes in xls file
            do_total = True
            t_cpf_amount += cpf_amount
            total_cpf_amount += cpf_amount
            t_mbmf_amount += mbmf_amount
            total_mbmf_amount += mbmf_amount
            t_sinda_amount += sinda_amount
            total_sinda_amount += sinda_amount
            t_cdac_amount += cdac_amount
            total_cdac_amount += cdac_amount
            t_ecf_amount += ecf_amount
            total_ecf_amount += ecf_amount
            total_cpfsdl_amount += cpfsdl_amount
            t_cpfsdl_amount += cpfsdl_amount
            t_gross_amount += gross_amount
            total_gross_amount += gross_amount
            total_additional_amount += additional_amount
            t_p_cpf_amount += p_cpf_amount
            total_p_cpf_amount += p_cpf_amount

            employee_no_category.update({
                'employee_name': payslip_rec.employee_id and payslip_rec.employee_id.name or '',
                'identification_no': payslip_rec.employee_id and payslip_rec.employee_id.identification_id or '',
                'amount_emp_fwl': emp_fwl_amount,
                'amount_emp_cpf': emp_cpf_amount,
                'amount_emp_mbmf': emp_mbmf_amount,
                'amount_emp_sinda': emp_sinda_amount,
                'amount_emp_cdac': emp_cdac_amount,
                'amount_emp_ecf': emp_ecf_amount,
                'amount_emp_sdl': emp_sdl_amount,
                'amount_t_cpf': t_cpf_amount,
                'amount_t_mbmf': t_mbmf_amount,
                'amount_t_sinda': t_sinda_amount,
                'amount_t_cdac': t_cdac_amount,
                'amount_t_ecf': t_ecf_amount,
                'amount_t_cpfsdl': t_cpfsdl_amount,
                'amount_t_gross': t_gross_amount,
                'amount_t_p_cpf': t_p_cpf_amount,
            })
            contract_id = hr_contract_obj.search([('employee_id', '=', emp_record.id), '|',
                                                  ('date_end', '>=', payslip_rec.date_from),
                                                  ('date_end', '=', False)])
            old_contract_id = hr_contract_obj.search([('employee_id', '=', emp_record.id),
                                                      ('date_end', '<=', payslip_rec.date_from)
                                                      ])
            for contract in contract_id:
                if payslip_rec.employee_id.active == False:
                    employee_no_category.update({'existing': 'Left'})
                elif contract.date_start >= payslip_rec.date_from and not old_contract_id.ids:
                    employee_no_category.update({'existing': 'New Join'})
                else:
                    employee_no_category.update({'existing': 'Existing'})
            cpf_amount_dict.update(employee_no_category)
            employee_dict.update(cpf_amount_dict)
            employee_no_category_total.update({
                'amount_total_cpf': total_cpf_amount,
                'amount_total_mbmf': total_mbmf_amount,
                'amount_total_sinda': total_sinda_amount,
                'amount_total_cdac': total_cdac_amount,
                'amount_total_ecf': total_ecf_amount,
                'amount_total_cpfsdl': total_cpfsdl_amount,
                'amount_total_gross': total_gross_amount,
                'amount_total_additional': total_additional_amount,
                'amount_total_p_cpf': total_p_cpf_amount
            })

            employee_dict.update(employee_no_category_total)
        final_result.update(employee_dict)
        final_data.append(final_result)
        return final_data


    @api.multi
    def get_xls_file(self):
        '''
        The method used to call download file of wizard
        @self : Record Set
        @api.multi : The decorator of multi
        @return: Return of wizard of action in dictionary
        -----------------------------------------------------
        '''
        cpf_binary_obj = self.env['cpf.binary.wizard']
        cr, uid, context = self.env.args
        if context is None: context = {}
        context = dict(context)
        payment_wiz_data = self.read([])
        data = {}
        if payment_wiz_data:
            data = payment_wiz_data[0]
        start_date = data.get('date_start', False) or False
        stop_date = data.get('date_stop', False) or False
        end_date = data.get('date_stop', False) or False
        emp_ids = data.get('employee_ids', False) or []
        if start_date >= end_date:
            raise ValidationError(_("You must be enter start date less than end date !"))
        for employee in self.env['hr.employee'].browse(emp_ids):
            if not employee.identification_id:
                raise ValidationError(_('There is no identification no define for %s employee.' % (employee.name)))
        context.update({'employee_id': emp_ids, 'date_start': start_date, 'date_stop': end_date})

        company_data = self.env['res.users'].browse(uid).company_id
        if data.get("export_report", False) == "pdf":
            data.update({'currency': " " + tools.ustr(company_data.currency_id.symbol), 'company': company_data.name})
            for employee in self.env['hr.employee'].browse(data.get('employee_ids')):
                if not employee.identification_id:
                    raise Warning(_('There is no identification no define for %s employee.' % (employee.name)))

            return self.env['report'].with_context(landscape=True).get_action(self, 'sg_hr_report.report_payment_advice')
        else:
            wbk = xlwt.Workbook()
            sheet = wbk.add_sheet('sheet 1', cell_overwrite_ok=True)
            font = xlwt.Font()
            font.bold = True
            bold_style = xlwt.XFStyle()
            bold_style.font = font
            border = xlwt.easyxf('font: bold on, color black; align: wrap no; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color white;')
            borders = xlwt.easyxf('font: bold off, color black; align: wrap no; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_color white;')
            style = xlwt.easyxf('align: wrap no')
            style.num_format_str = '#,##0.00'
            new_style = xlwt.easyxf('font: bold on; align: wrap no')
            new_style.num_format_str = '#,##0.00'

            # static data
            sheet.write(0, 4, company_data.name)
            sheet.write(1, 3, company_data.street or '')
            sheet.write(2, 3, str(company_data and company_data.street2 or ' ') + ' ' + str(company_data and company_data.country_id and company_data.country_id.name or '') + ' ' + str(company_data.zip) or '')
            sheet.write(3, 4, 'Tel : ' + str(company_data.phone or ' ') + ',' + 'Fax : ' + str(company_data.fax or ''))
            sheet.write(4, 5, 'PAYMENT ADVICE')
            sheet.write(6, 0, 'MANDATORY REF NO. : ' + str(company_data.company_code or ''))
            sheet.write(7, 0, 'VOLUNTARY  REF NO. : ')
            sheet.write(8, 0, company_data.name)
            sheet.write(9, 0, '6 Jalan Kilang #04-00')
            sheet.write(6, 8, 'SUBM MODE')
            sheet.write(7, 8, 'DATE')
            sheet.write(6, 10, ':')
            sheet.write(7, 10, ':')
            sheet.write(6, 11, 'INTERNAL')
            sheet.write(12, 0, 'PART 1 : Payment Details For ', bold_style)
            sheet.write(13, 8, 'AMOUNT' , bold_style)
            sheet.write(13, 10, 'NO. OF EMPLOYEE', bold_style)
            sheet.write(15, 0, '1. CPF Contribution')
            sheet.write(16, 1, 'Mandatory Contribution')
            sheet.write(17, 1, 'Voluntary Contribution')
            sheet.write(18, 0, '2. B/F CPF late Payment interest')
            sheet.write(19, 0, 'Interest charged on last payment')
            sheet.write(20, 0, '3. Late payment interest on CPF Contribution')
            sheet.write(21, 0, '4. Late payment penalty for Foreign Worker Levy')
            sheet.write(22, 0, '5. Foreign Worker Levy')
            sheet.write(23, 0, '6. Skills Development Levy')
            sheet.write(24, 0, '7. Donation to Community Chest')
            sheet.write(25, 0, '8. Mosque Building & Mendaki Fund (MBMF)')
            sheet.write(26, 0, '9. SINDA Fund')
            sheet.write(27, 0, '10. CDAC Fund')
            sheet.write(28, 0, '11. Eurasian Community Fund (EUCF)')
            # total
            sheet.write(30, 7, 'Total', bold_style)
            # static data
            sheet.write(31, 4, 'Please fill in cheque details if you are paying by cheque')
            sheet.write(32, 4, 'BANK')
            sheet.write(32, 5, ':')
            sheet.write(33, 4, 'CHEQUE NO.')
            sheet.write(33, 5, ':')
            sheet.write(34, 4, 'THE EMPLOYER HEREBY GUARANTEES')
            sheet.write(35, 4, 'THE ACCURACY')
            sheet.write(36, 4, 'OF THE CPF RETURNS FOR')
            sheet.write(37, 4, 'AS SHOWN ON THE SUBMITTED DISKETTE.')
            sheet.write(39, 4, 'EMPLOYER\'S AUTHORIZED SIGNATORY')
            sheet.write(42, 0, 'PART 2 : Contribution Details For', bold_style)
            # data header
            sheet.write(44, 0, 'Employee Name', border)
            sheet.write(43, 3, 'CPF',  border)
            sheet.write(44, 3, 'Account No.', border)
            sheet.write(43, 4, 'Mandatory CPF', border)
            sheet.write(44, 4, 'Contribution', border)
            sheet.write(43, 5, 'Voluntary CPF', border)
            sheet.write(44, 5, 'Contribution', border)
            sheet.write(43, 6, 'Last', border)
            sheet.write(44, 6, 'Contribution', border)
    #        sheet.write(41, 8, 'CPF', bold_style)
    #        sheet.write(42, 8, 'Status', bold_style)
            sheet.write(43, 8, 'MBMF', border)
            sheet.write(44, 8, 'Fund', border)
            sheet.write(43, 9, 'SINDA', border)
            sheet.write(44, 9, 'Fund', border)
            sheet.write(43, 10, 'CDAC', border)
            sheet.write(44, 10, 'Fund', border)
            sheet.write(43, 11, 'ECF', border)
            sheet.write(44, 11, 'Fund', border)
            sheet.write(43, 12, 'SDL', border)
            sheet.write(44, 12, 'Fund', border)
            sheet.write(43, 13, 'Ordinary', border)
            sheet.write(44, 13, 'Wages', border)
            sheet.write(43, 14, 'Additional', border)
            sheet.write(44, 14, 'Wages', border)
            sheet.write(43, 0, '', border)
            sheet.write(43, 1, '', border)
            sheet.write(43, 2, '', border)
            sheet.write(43, 7, '', border)
            sheet.write(44, 1, '', border)
            sheet.write(44, 2, '', border)
            sheet.write(44, 7, '', border)


            emp_obj = self.env['hr.employee']
            payslip_obj = self.env['hr.payslip']
            hr_contract_obj = self.env['hr.contract']
            category_ids = self.env['hr.employee.category'].search([])
            start_row = raw_no = 45
            # start_date = self.date_start or False
            # stop_date = self.date_stop or False
            # employee_ids_lst = context.get('employee_id',False)
            # print"\n\nemployee_list_ids:\n\n", employee_ids_lst
            month_dict = {'01':'January', '02':'February', '03': 'March', '04':'April', '05':'May', '06':'June', '07':'July', '08':'August', '09':'September', '10':'October', '11': 'November', '12': 'December'}
            period = month_dict.get(start_date.split('-')[1]) + ', ' + start_date.split('-')[0]
            sheet.write(36, 7, period)
            sheet.write(7, 11, datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y'))
            sheet.write(42, 2, period, bold_style)
            sheet.write(12, 2, period, bold_style)
            t_cpfsdl_amount = t_p_cpf_sdl_amount = t_p_fwl_amount = t_p_cpf_amount = t_gross_amount = t_ecf_amount = t_cdac_amount = t_sinda_amount = t_mbmf_amount = t_cpf_amount = 0.00
            total_additional_amount = total_cpfsdl_amount = total_p_cpf_amount = total_gross_amount = total_ecf_amount = total_cdac_amount = total_sinda_amount = total_mbmf_amount = total_cpf_amount = 0.00
            emp_cpfsdl_amount = emp_sdl_amount = emp_ecf_amount = emp_fwl_amount = emp_cdac_amount = emp_sinda_amount = emp_mbmf_amount = emp_cpf_amount = 0.00
            # no category
            join_date = start_date
            emply_ids = emp_obj.search([('id', 'in', emp_ids),
                                        ('category_ids', '=', False)])
            do_total = False
            for emp_record in emply_ids:
                payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id),
                                                  ('date_from', '>=', start_date),
                                                  ('date_from', '<=', stop_date),
                                                  ('state', 'in', ['draft', 'done', 'verify'])])
                previous_date = cpf_binary_obj._default_previous_date(start_date)
                previous_payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id)], order='date_from ASC', limit=1)
                if previous_payslip_ids:
                    join_date = previous_payslip_ids.date_from
                while(join_date <= previous_date[0]):
                    previous_payslip_ids = payslip_obj.search([ ('employee_id', '=', emp_record.id),
                                                                ('date_from', '>=', previous_date[0]),
                                                                ('date_from', '<=', previous_date[1]),
                                                                ('state', 'in', ['draft', 'done', 'verify'])])
                    if previous_payslip_ids:
                        break
                    else:
                        previous_date = cpf_binary_obj._default_previous_date(previous_date[0])
                # if not payslip_ids:
                #     raise ValidationError(_('There is no payslip details between selected date %s and %s') %(previous_date[0], previous_date[1]))
                additional_amount = cpfsdl_amount = p_cpf_amount = gross_amount = ecf_amount = fwl_amount = cdac_amount = sinda_amount = mbmf_amount = cpf_amount = 0.00
                for payslip_rec in payslip_ids:
                    for line in payslip_rec.line_ids:
                        if line.register_id.name == 'CPF':
                            cpf_amount += line.amount
                        if line.register_id.name == 'CPF - MBMF':
                            mbmf_amount += line.amount
                        if line.register_id.name == 'CPF - SINDA':
                            sinda_amount += line.amount
                        if line.register_id.name == 'CPF - CDAC':
                            cdac_amount += line.amount
                        if line.register_id.name == 'CPF - ECF':
                            ecf_amount += line.amount
                        if line.register_id.name == 'CPF - FWL':
                            fwl_amount += line.amount
                            t_p_fwl_amount += line.amount
                        if line.register_id and line.register_id.name == 'BONUS':
                            gross_amount -= line.amount
                        if line.category_id.code == 'GROSS':
                            gross_amount += line.amount
                        if line.code == 'CPFSDL':
                            cpfsdl_amount += line.amount
                            t_p_cpf_sdl_amount += line.amount
                        if line.register_id and line.register_id.name == 'BONUS':
                            additional_amount += line.amount
                if not gross_amount:
                    continue
                if not cpf_amount and not mbmf_amount and not sinda_amount and not cdac_amount and not ecf_amount and not cpfsdl_amount:
                    continue
                sheet.write(raw_no, 0, payslip_rec.employee_id and payslip_rec.employee_id.name or '', borders)
                sheet.write(raw_no, 1, '', borders)
                sheet.write(raw_no, 2, '', borders)
                sheet.write(raw_no, 3, payslip_rec.employee_id and payslip_rec.employee_id.identification_id or '', borders)
                    # previous cpf
                if previous_payslip_ids:
                    if payslip_rec.date_from != payslip_rec.date_from:
                        for previous_line in previous_payslip_ids.line_ids:
                            if previous_line.register_id.name == 'CPF':
                                p_cpf_amount += previous_line.amount
                # Counts Employee
                if fwl_amount:
                    emp_fwl_amount += 1
                if cpf_amount != 0:
                    emp_cpf_amount += 1
                if mbmf_amount != 0:
                    emp_mbmf_amount += 1
                if sinda_amount != 0:
                    emp_sinda_amount += 1
                if cdac_amount != 0:
                    emp_cdac_amount += 1
                if ecf_amount != 0:
                    emp_ecf_amount += 1
                if cpfsdl_amount != 0:
                    emp_sdl_amount += 1

                # writes in xls file
                do_total = True
                sheet.write(raw_no, 4, "%.2f" % (cpf_amount or 0.00), borders)
                t_cpf_amount += cpf_amount
                total_cpf_amount += cpf_amount
                sheet.write(raw_no, 5, "%.2f" % (0.00), borders)
                # sheet.write(raw_no, 6, borders)
                sheet.write(raw_no, 7, '', borders)
                sheet.write(raw_no, 8, "%.2f" % (mbmf_amount or 0.00), borders)
                t_mbmf_amount += mbmf_amount
                total_mbmf_amount += mbmf_amount
                sheet.write(raw_no, 9, "%.2f" % (sinda_amount or 0.00), borders)
                t_sinda_amount += sinda_amount
                total_sinda_amount += sinda_amount
                sheet.write(raw_no, 10, "%.2f" % (cdac_amount or 0.00), borders)
                t_cdac_amount += cdac_amount
                total_cdac_amount += cdac_amount
                sheet.write(raw_no, 11, "%.2f" % (ecf_amount or 0.00), borders)
                t_ecf_amount += ecf_amount
                total_ecf_amount += ecf_amount
                sheet.write(raw_no, 12, "%.2f" % (cpfsdl_amount or 0.00), borders)
                total_cpfsdl_amount += cpfsdl_amount
                t_cpfsdl_amount += cpfsdl_amount
                sheet.write(raw_no, 13, "%.2f" % (gross_amount or 0.00), borders)
                sheet.write(raw_no, 14, "%.2f" % (additional_amount or 0.00), borders)
                t_gross_amount += gross_amount
                total_gross_amount += gross_amount
                total_additional_amount += additional_amount
                sheet.write(raw_no, 6, "%.2f" % (p_cpf_amount or 0.00), borders)
                t_p_cpf_amount += p_cpf_amount
                total_p_cpf_amount += p_cpf_amount
                #sheet.write(raw_no, 6, 0.00, style)
                contract_id = hr_contract_obj.search([('employee_id', '=', emp_record.id), '|',
                                                      ('date_end','>=', payslip_rec.date_from),
                                                      ('date_end','=',False)])
                old_contract_id = hr_contract_obj.search([('employee_id', '=', emp_record.id),
                                                          ('date_end','<=', payslip_rec.date_from)
                                                        ])
                for contract in contract_id:
                    if payslip_rec.employee_id.active == False:
                        sheet.write(raw_no, 7, 'Left', border)
                    elif contract.date_start >= payslip_rec.date_from and not old_contract_id.ids:
                        sheet.write(raw_no, 7, 'New Join', border)
                    else:
                        sheet.write(raw_no, 7, 'Existing', border)
                raw_no += 1
            if do_total:
                raw_no = raw_no + 1
                sheet.write(raw_no, 0, 'Total Employee:', borders)
                sheet.write(raw_no, 1, '', borders)
                sheet.write(raw_no, 2, '', borders)
                sheet.write(raw_no, 3, '', borders)
                start_row = start_row + 1

                sheet.write(raw_no, 4, "%.2f" %(total_cpf_amount), borders)  # cpf
                sheet.write(raw_no, 5, "%.2f" % (0.00), borders)  # v_cpf
                sheet.write(raw_no, 6, "%.2f" % (total_p_cpf_amount or 0.00), borders)  # p_cpf
                sheet.write(raw_no, 7, '', borders)
                sheet.write(raw_no, 8, "%.2f" % (total_mbmf_amount or 0.00), borders)  # MBPF
                sheet.write(raw_no, 9, "%.2f" % (total_sinda_amount or 0.00), borders)  # SINDA
                sheet.write(raw_no, 10, "%.2f" % (total_cdac_amount or 0.00), borders)  # CDAC
                sheet.write(raw_no, 11, "%.2f" % (total_ecf_amount or 0.00), borders)  # ECF
                sheet.write(raw_no, 12, "%.2f" % (total_cpfsdl_amount or 0.00), borders)  # CPFSDL
                sheet.write(raw_no, 13, "%.2f" % (total_gross_amount or 0.00), borders)  # O_WAGE
                sheet.write(raw_no, 14, "%.2f" % (total_additional_amount), borders)
        #        sheet.write(raw_no, 13, xlwt.Formula("sum(N" + str(start_row) + ":N" + str(raw_no - 1) + ")"), new_style)  # AD_WAGE

            # emp by category
            start_row = raw_no = raw_no + 2

            emp_rec = emp_obj.search([('id', 'in', emp_ids),
                                     ('category_ids', '!=', False)])
            for category in category_ids:
                emp_flag= False
                total_additional_amount = total_cpfsdl_amount = total_p_cpf_amount = total_gross_amount = total_ecf_amount = total_cdac_amount = total_sinda_amount = total_mbmf_amount = total_cpf_amount = 0.00
                for emp_record in emp_rec:
                    if (emp_record.category_ids and emp_record.category_ids[0].id != category.id) or not emp_record.category_ids:
                        continue
                    payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id),
                                                      ('date_from', '>=', start_date),
                                                      ('date_from', '<=', stop_date),
                                                      ('state', 'in', ['draft', 'done', 'verify'])])

                    previous_date = cpf_binary_obj._default_previous_date(start_date)
                    previous_payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id)],
                                                               order='date_from ASC', limit=1)
                    if previous_payslip_ids:
                        join_date = previous_payslip_ids.date_from
                    while(join_date <= previous_date[0]):
                        previous_payslip_ids = payslip_obj.search([('employee_id', '=', emp_record.id),
                                                                   ('date_from', '>=', previous_date[0]),
                                                                   ('date_from', '<=', previous_date[1]),
                                                                   ('state', 'in', ['draft', 'done', 'verify'])])
                        if previous_payslip_ids:
                            break
                        else:
                            previous_date = cpf_binary_obj._default_previous_date(previous_date[0])
                    # if not payslip_ids:
                    #     raise ValidationError(_('There is no payslip details between selected date %s and %s') %(previous_date[0], previous_date[1]))
                    additional_amount = cpfsdl_amount = p_cpf_amount = gross_amount = ecf_amount = fwl_amount = cdac_amount = sinda_amount = mbmf_amount = cpf_amount = 0.00
                    for payslip_rec in payslip_ids:
                        for line in payslip_rec.line_ids:
                            if line.register_id.name == 'CPF':
                                cpf_amount += line.amount
                            if line.register_id.name == 'CPF - MBMF':
                                mbmf_amount += line.amount
                            if line.register_id.name == 'CPF - SINDA':
                                sinda_amount += line.amount
                            if line.register_id.name == 'CPF - CDAC':
                                cdac_amount += line.amount
                            if line.register_id.name == 'CPF - ECF':
                                ecf_amount += line.amount
                            if line.register_id.name == 'CPF - FWL':
                                fwl_amount += line.amount
                                t_p_fwl_amount += line.amount
                            if line.register_id and line.register_id.name == 'BONUS':
                                gross_amount -= line.amount
                            if line.category_id.code == 'GROSS':
                                gross_amount += line.amount
                            if line.code == 'CPFSDL':
                                cpfsdl_amount += line.amount
                                t_p_cpf_sdl_amount += line.amount
                            if line.register_id and line.register_id.name == 'BONUS':
                                additional_amount += line.amount

                    if not gross_amount:
                        continue
                    if not cpf_amount and not mbmf_amount and not sinda_amount and not cdac_amount and not ecf_amount and not cpfsdl_amount:
                        t_p_fwl_amount -= fwl_amount
                        continue
                    sheet.write(raw_no, 0, payslip_rec.employee_id and payslip_rec.employee_id.name or '', borders)
                    sheet.write(raw_no, 1, '', borders)
                    sheet.write(raw_no, 2, '', borders)
                    sheet.write(raw_no, 3, payslip_rec.employee_id and payslip_rec.employee_id.identification_id or '', borders)
                        # previous cpf
                    if previous_payslip_ids:
                        if payslip_rec.date_from != payslip_rec.date_from:
                            for previous_line in previous_payslip_ids.line_ids:
                                if previous_line.register_id.name == 'CPF':
                                        p_cpf_amount += previous_line.amount

                    # Counts Employee
                    if fwl_amount:
                        emp_fwl_amount += 1
                    if cpf_amount != 0:
                        emp_cpf_amount += 1
                    if mbmf_amount != 0:
                        emp_mbmf_amount += 1
                    if sinda_amount != 0:
                        emp_sinda_amount += 1
                    if cdac_amount != 0:
                        emp_cdac_amount += 1
                    if ecf_amount != 0:
                        emp_ecf_amount += 1
                    if cpfsdl_amount != 0:
                        emp_sdl_amount += 1

                    # writes in xls file
                    emp_flag = True
                    sheet.write(raw_no, 4, "%.2f" % (cpf_amount or 0.00), borders)
                    t_cpf_amount += cpf_amount
                    total_cpf_amount += cpf_amount
                    sheet.write(raw_no, 5, "%.2f" % (0.00), borders)
                    # sheet.write(raw_no, 6, borders)
                    sheet.write(raw_no, 7, '', borders)
                    sheet.write(raw_no, 8, "%.2f" % (mbmf_amount or 0.00), borders)
                    t_mbmf_amount += mbmf_amount
                    total_mbmf_amount += mbmf_amount
                    sheet.write(raw_no, 9, "%.2f" % (sinda_amount or 0.00), borders)
                    t_sinda_amount += sinda_amount
                    total_sinda_amount += sinda_amount
                    sheet.write(raw_no, 10, "%.2f" % (cdac_amount or 0.00), borders)
                    t_cdac_amount += cdac_amount
                    total_cdac_amount += cdac_amount
                    sheet.write(raw_no, 11, "%.2f" % (ecf_amount or 0.00), borders)
                    t_ecf_amount += ecf_amount
                    total_ecf_amount += ecf_amount
                    sheet.write(raw_no, 12, "%.2f" % (cpfsdl_amount or 0.00), borders)
                    t_cpfsdl_amount += cpfsdl_amount
                    total_cpfsdl_amount += cpfsdl_amount
                    sheet.write(raw_no, 13,  "%.2f" % (gross_amount or 0.00), borders)
                    sheet.write(raw_no, 14, "%.2f" % (additional_amount or 0.00), borders)
                    t_gross_amount += gross_amount
                    total_gross_amount += gross_amount
                    sheet.write(raw_no, 6, "%.2f" % (p_cpf_amount or 0.00), borders)
                    t_p_cpf_amount += p_cpf_amount
                    total_p_cpf_amount += p_cpf_amount
                    total_additional_amount += additional_amount

                    #sheet.write(raw_no, 6, 0.00, style)
                    contract_id = hr_contract_obj.search([('employee_id', '=', emp_record.id), '|',
                                                          ('date_end','>=', payslip_rec.date_from),
                                                          ('date_end','=',False)])
                    old_contract_id = hr_contract_obj.search([('employee_id', '=', emp_record.id),
                                                              ('date_end','<=', payslip_rec.date_from)])
                    for contract in contract_id:
                        if payslip_rec.employee_id.active == False:
                            sheet.write(raw_no, 7, 'Left', borders)
                        elif contract.date_start >= payslip_rec.date_from and not old_contract_id.ids:
                            sheet.write(raw_no, 7, 'New Join', borders)
                        else:
                            sheet.write(raw_no, 7, 'Existing', borders)
                    raw_no += 1

                if emp_flag:
                    raw_no = raw_no + 1
                    sheet.write(raw_no, 0, 'Total %s :' % category.name , borders)
                    sheet.write(raw_no, 1, '', borders)
                    sheet.write(raw_no, 2, '', borders)
                    sheet.write(raw_no, 3, '', borders)
                    start_row = start_row + 1

                    sheet.write(raw_no, 4, "%.2f" % (total_cpf_amount or 0.00), borders)  # cpf
                    sheet.write(raw_no, 5, "%.2f" % (0.00), borders)  # v_cpf
                    sheet.write(raw_no, 6, "%.2f" % (total_p_cpf_amount or 0.00), borders)  # p_cpf
                    sheet.write(raw_no, 7, '', borders)
                    sheet.write(raw_no, 8, "%.2f" % (total_mbmf_amount or 0.00), borders)  # MBPF
                    sheet.write(raw_no, 9, "%.2f" % (total_sinda_amount or 0.00), borders)  # SINDA
                    sheet.write(raw_no, 10, "%.2f" % (total_cdac_amount or 0.00), borders)  # CDAC
                    sheet.write(raw_no, 11, "%.2f" % (total_ecf_amount or 0.00), borders)  # ECF
                    sheet.write(raw_no, 12, "%.2f" % (total_cpfsdl_amount or 0.00), borders)  # ECF
                    sheet.write(raw_no, 13, "%.2f" % (total_gross_amount or 0.00), borders)  # O_WAGE
                    sheet.write(raw_no, 14, "%.2f" % (total_additional_amount), borders)

                    raw_no = raw_no + 2
                    start_row = start_row+ 3
            # amount columns
            sheet.write(16, 8,(t_cpf_amount or 0.00), style)  # cpf
            sheet.write(17, 8, 0.00, style)
            sheet.write(18, 8, 0.00, style)
            sheet.write(19, 8, 0.00, style)
            sheet.write(20, 8, 0.00, style)
            sheet.write(21, 8, 0.00, style)
            sheet.write(22, 8, t_p_fwl_amount, style)
            sheet.write(23, 8, t_p_cpf_sdl_amount, style)
            sheet.write(24, 8, 0.00, style)
            sheet.write(25, 8, (t_mbmf_amount or 0.00), style)  # MBPF
            sheet.write(26, 8,(t_sinda_amount or 0.00), style)  # SINDA
            sheet.write(27, 8,(t_cdac_amount or 0.00), style)  # CDAC
            sheet.write(28, 8,(t_ecf_amount or 0.00), style)  # ECF

            # no of employee
            sheet.write(16, 10, emp_cpf_amount)
            sheet.write(17, 10, 0)
            sheet.write(18, 10, 0)
            sheet.write(19, 10, 0)
            sheet.write(20, 10, 0)
            sheet.write(21, 10, 0)
            sheet.write(22, 10, emp_fwl_amount)
            sheet.write(23, 10, emp_sdl_amount)
            sheet.write(24, 10, 0)
            sheet.write(25, 10, emp_mbmf_amount)
            sheet.write(26, 10, emp_sinda_amount)
            sheet.write(27, 10, emp_cdac_amount)
            sheet.write(28, 10, emp_ecf_amount)

            sheet.write(30, 8, xlwt.Formula("sum(I17:I29)"), new_style)  # Total

            wbk.save(tempfile.gettempdir() + "/payslip.xls")

            file = open(tempfile.gettempdir() + "/payslip.xls", "rb")
            out = file.read()
            file.close()
            res = base64.b64encode(out)

            if not start_date and stop_date:
                return ''
            end_date = datetime.strptime(stop_date, DEFAULT_SERVER_DATE_FORMAT)
            monthyear = end_date.strftime('%m%Y')
            file_name = "Payment Advice " + monthyear + '.xls'

            module_rec = cpf_binary_obj.create({'name': file_name, 'xls_file' : res})
            return {'name': _('Payment Advice Report'),
                  'res_id' : module_rec.id,
                  'view_type': 'form',
                  "view_mode": 'form',
                  'res_model': 'cpf.binary.wizard',
                  'type': 'ir.actions.act_window',
                  'target': 'new',
                  'context': context}
        
cpf_payment_wizard()


class cpf_binary_wizard(models.TransientModel):
    _name = 'cpf.binary.wizard'
    
    name = fields.Char('Name', size=256)
    xls_file = fields.Binary('Click On Download Link To Download Xls File', readonly=True)

    @api.model
    def _default_previous_date(self, date):
        date_obj = datetime.strptime(date , DEFAULT_SERVER_DATE_FORMAT)
        date_obj = date_obj - relativedelta(months=1)
        return [str(date_obj.year) + "-" + str(date_obj.month) + "-01", (date_obj + relativedelta(months=+1,day=1,days=-1)).strftime('%Y-%m-%d')]
    
    @api.multi
    def action_back(self):
        if self._context is None:
            context = {}
        return {'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'cpf.payment.wizard',
                'target': 'new'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: