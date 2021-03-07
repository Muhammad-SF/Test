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
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class cpf_rule_text_file(models.TransientModel):

    _name = 'cpf.rule.text.file'

    employee_ids = fields.Many2many('hr.employee', 'hr_employe_cpf_text_rel','cpf_emp_id','employee_id','Employee', required=False)
    include_fwl = fields.Boolean('INCLUDE FWL')
    date_start = fields.Date('Date Start', default=lambda *a: time.strftime('%Y-%m-01'))
    date_stop = fields.Date('Date Stop', default=lambda *a: str(datetime.datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])

    @api.multi
    def download_cpf_txt_file(self):
        '''
        The method used to call download file of wizard
        @self : Record Set
        @api.multi : The decorator of multi
        @return: Return of wizard of action in dictionary
        --------------------------------------------------------
        '''
        cr, uid, context = self.env.args
        context = dict(context)
        if context is None:
            context = {}
        hr_contract_obj = self.env['hr.contract']
        cpf_data_wiz = self.read([])
        data = {}
        if cpf_data_wiz:
            data = cpf_data_wiz[0]
        start_date = data.get('date_start', False)
        end_date = data.get('date_stop', False)
        emp_ids = data.get('employee_ids',[]) or []
        if start_date >= end_date:
            raise ValidationError(_("You must be enter start date less than end date !"))
        for employee in self.env['hr.employee'].browse(emp_ids):
            emp_name = employee and employee.name or ''
#            if not employee.bank_account_id:
#                raise ValidationError(_('There is no Bank Account define for %s employee.' % (emp_name)))
#            if not employee.gender:
#                raise ValidationError(_('There is no gender define for %s employee.' % (emp_name)))
#            if not employee.birthday:
#                raise ValidationError(_('There is no birth date define for %s employee.' % (emp_name)))
            if not employee.identification_id:
                raise ValidationError(_('There is no identification no define for %s employee.' % (emp_name)))
#            if not employee.work_phone or not employee.work_email:
#                raise ValidationError(_('You must be configure Contact no or email for %s employee.' % (emp_name)))
        payslip_rec = self.env['hr.payslip'].search([('date_from', '>=', start_date),
                                                     ('date_to','<=',end_date),
                                                     ('employee_id', 'in', emp_ids),
                                                     ('state', 'in', ['draft', 'done', 'verify'])])
        if not payslip_rec.ids:
            raise ValidationError(_('There is no payslip details available between selected date %s and %s') %(start_date, end_date))
        total_record = 0.0
        summary_record_amount_total = 0.0
        employee_id = data['employee_ids']
        include_fwl = data.get('include_fwl', False)
        if not employee_id:
            return False
        current_date = datetime.datetime.today()
        year_month_date = current_date.strftime('%Y%m%d')
        hour_minute_second = current_date.strftime('%H%M%S')
        year_month = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).strftime('%Y%m')
        tgz_tmp_filename = tempfile.mktemp('.'+"txt")
        tmp_file = False
        company_data = self.env['res.users'].browse(uid).company_id
        try:
            payslip_ids = self.env['hr.payslip'].search([('date_from', '>=', start_date),
                                                         ('date_from','<=',end_date),
                                                         ('employee_id', 'in', employee_id),
                                                         ('state', 'in', ['draft', 'done', 'verify'])])
            tmp_file = open(tgz_tmp_filename, "wr")
            header_record = 'F'.ljust(1) + \
                            ' '.ljust(1) + \
                            str(company_data.company_code)[:10].ljust(10) + \
                            'PTE'.ljust(3) + \
                            '01'.ljust(2) + \
                            ' '.ljust(1) + \
                            '01'.ljust(2) + \
                            year_month_date.ljust(8) + \
                            hour_minute_second.ljust(6) + \
                            'FTP.DTL'.ljust(13) + \
                            ' '.ljust(103) + "\r\n"
            tmp_file.write(header_record)

            summary_total_employee = 0.0
            for payslip in payslip_ids:
                summary_total_employee += 1
            summary_total_employee = '%0*d' % (7, summary_total_employee)

            sdl_salary_rule_code = fwl_salary_rule_code = ecf_salary_rule_code = cdac_salary_rule_code = sinda_salary_rule_code = mbmf_salary_rule_code = cpf_salary_rule_code = ''
            sdl_amount = fwl_amount = ecf_amount = cdac_amount = sinda_amount = mbmf_amount = cpf_amount = 0.0
            cpf_emp = mbmf_emp = sinda_emp = cdac_emp = ecf_emp = fwl_emp = sdl_emp = 0
            for payslip in payslip_ids:
                count_mbmf_emp = count_sinda_emp = count_cdac_emp = count_ecf_emp = count_fwl_emp = True
                for line in payslip.line_ids:
                    if line.register_id.name == 'CPF':
                        cpf_salary_rule_code = '01'
                        cpf_amount += line.amount
                    elif line.register_id.name == 'CPF - MBMF':
                        mbmf_salary_rule_code = '02'
                        mbmf_amount += line.amount
                        if count_mbmf_emp:
                            mbmf_emp += 1
                            count_mbmf_emp = False
                    elif line.register_id.name == 'CPF - SINDA':
                        sinda_salary_rule_code = '03'
                        sinda_amount += line.amount
                        if count_sinda_emp:
                            sinda_emp += 1
                            count_sinda_emp = False
                    elif line.register_id.name == 'CPF - CDAC':
                        cdac_salary_rule_code = '04'
                        cdac_amount += line.amount
                        if count_cdac_emp:
                            cdac_emp += 1
                            count_cdac_emp = False
                    elif line.register_id.name == 'CPF - ECF':
                        ecf_salary_rule_code = '05'
                        ecf_amount += line.amount
                        if count_ecf_emp:
                            ecf_emp += 1
                            count_ecf_emp = False
                    elif line.register_id.name == 'CPF - FWL':
                        fwl_salary_rule_code = '08'
                        fwl_amount += line.amount
                        if count_fwl_emp:
                            fwl_emp += 1
                            count_fwl_emp = False
                    elif line.register_id.name == 'CPF - SDL':
                        sdl_salary_rule_code = '11'
                        sdl_amount += line.amount
                    else:
                        salary_rule_code = ''
                        amount = 0.0
            
            if cpf_salary_rule_code and cpf_amount:
                total_record += 1
                cpf_amount = cpf_amount*100
                new_amt = int(round(cpf_amount))
                if new_amt < 0 :
                    new_amt = new_amt * -1
                final_amt = '%0*d' % (12, new_amt)
                summary_record_amount_total += float(final_amt)
                cpf_emp = '%0*d' % (7, 0)
                summary_record = 'F'.ljust(1) + \
                                '0'.ljust(1) + \
                                str(company_data.company_code)[:10].ljust(10) + \
                                'PTE'.ljust(3) + \
                                '01'.ljust(2) + \
                                ' '.ljust(1) + \
                                '01'.ljust(2) + \
                                str(year_month).ljust(6) + \
                                cpf_salary_rule_code.ljust(2) + \
                                str(final_amt).ljust(12) + \
                                str(cpf_emp).ljust(7) + \
                                ' '.ljust(103) + "\r\n"
                tmp_file.write(summary_record)
                
            if mbmf_salary_rule_code and mbmf_amount and mbmf_emp:
                total_record += 1
                mbmf_amount = mbmf_amount*100
                new_amt = int(round(mbmf_amount))
                if new_amt < 0 :
                    new_amt = new_amt * -1
                final_amt = '%0*d' % (12, new_amt)
                summary_record_amount_total += float(final_amt)
                mbmf_emp = '%0*d' % (7, mbmf_emp)
                summary_record = 'F'.ljust(1) + \
                                '0'.ljust(1) + \
                                str(company_data.company_code)[:10].ljust(10) + \
                                'PTE'.ljust(3) + \
                                '01'.ljust(2) + \
                                ' '.ljust(1) + \
                                '01'.ljust(2) + \
                                str(year_month).ljust(6) + \
                                mbmf_salary_rule_code.ljust(2) + \
                                str(final_amt).ljust(12) + \
                                str(mbmf_emp).ljust(7) + \
                                ' '.ljust(103) + "\r\n"
                tmp_file.write(summary_record)
            
            if sinda_salary_rule_code and sinda_amount and sinda_emp:
                total_record += 1
                sinda_amount = sinda_amount*100
                new_amt = int(round(sinda_amount))
                if new_amt < 0 :
                    new_amt = new_amt * -1
                final_amt = '%0*d' % (12, new_amt)
                summary_record_amount_total += float(final_amt)
                sinda_emp = '%0*d' % (7, sinda_emp)
                summary_record = 'F'.ljust(1) + \
                                '0'.ljust(1) + \
                                str(company_data.company_code)[:10].ljust(10) + \
                                'PTE'.ljust(3) + \
                                '01'.ljust(2) + \
                                ' '.ljust(1) + \
                                '01'.ljust(2) + \
                                str(year_month).ljust(6) + \
                                sinda_salary_rule_code.ljust(2) + \
                                str(final_amt).ljust(12) + \
                                str(sinda_emp).ljust(7) + \
                                ' '.ljust(103) + "\r\n"
                tmp_file.write(summary_record)
            
            if cdac_salary_rule_code and cdac_amount and cdac_emp:
                total_record += 1
                cdac_amount = cdac_amount*100
                new_amt = int(round(cdac_amount))
                if new_amt < 0 :
                    new_amt = new_amt * -1
                final_amt = '%0*d' % (12, new_amt)
                summary_record_amount_total += float(final_amt)
                cdac_emp = '%0*d' % (7, cdac_emp)
                summary_record = 'F'.ljust(1) + \
                                '0'.ljust(1) + \
                                str(company_data.company_code)[:10].ljust(10) + \
                                'PTE'.ljust(3) + \
                                '01'.ljust(2) + \
                                ' '.ljust(1) + \
                                '01'.ljust(2) + \
                                str(year_month).ljust(6) + \
                                cdac_salary_rule_code.ljust(2) + \
                                str(final_amt).ljust(12) + \
                                str(cdac_emp).ljust(7) + \
                                ' '.ljust(103) + "\r\n"
                tmp_file.write(summary_record)
            
            if ecf_salary_rule_code and ecf_amount and ecf_emp:
                total_record += 1
                ecf_amount = ecf_amount*100
                new_amt = int(round(ecf_amount))
                if new_amt < 0 :
                    new_amt = new_amt * -1
                final_amt = '%0*d' % (12, new_amt)
                summary_record_amount_total += float(final_amt)
                ecf_emp = '%0*d' % (7, ecf_emp)
                summary_record = 'F'.ljust(1) + \
                                '0'.ljust(1) + \
                                str(company_data.company_code)[:10].ljust(10) + \
                                'PTE'.ljust(3) + \
                                '01'.ljust(2) + \
                                ' '.ljust(1) + \
                                '01'.ljust(2) + \
                                str(year_month).ljust(6) + \
                                ecf_salary_rule_code.ljust(2) + \
                                str(final_amt).ljust(12) + \
                                str(ecf_emp).ljust(7) + \
                                ' '.ljust(103) + "\r\n"
                tmp_file.write(summary_record)
            if include_fwl and fwl_salary_rule_code and fwl_amount and fwl_emp:
                total_record += 1
                fwl_amount = fwl_amount*100
                new_amt = int(round(fwl_amount))
                if new_amt < 0 :
                    new_amt = new_amt * -1
                final_amt = '%0*d' % (12, new_amt)
                summary_record_amount_total += float(final_amt)
                fwl_emp = '%0*d' % (7, fwl_emp)
                summary_record = 'F'.ljust(1) + \
                                '0'.ljust(1) + \
                                str(company_data.company_code)[:10].ljust(10) + \
                                'PTE'.ljust(3) + \
                                '01'.ljust(2) + \
                                ' '.ljust(1) + \
                                '01'.ljust(2) + \
                                str(year_month).ljust(6) + \
                                fwl_salary_rule_code.ljust(2) + \
                                str(final_amt).ljust(12) + \
                                str(fwl_emp).ljust(7) + \
                                ' '.ljust(103) + "\r\n"
                tmp_file.write(summary_record)
            
            if sdl_salary_rule_code and sdl_amount:
                total_record += 1
                sdl_amount = sdl_amount*100
                new_amt = int(round(sdl_amount))
                if new_amt < 0 :
                    new_amt = new_amt * -1
                final_amt = '%0*d' % (12, new_amt)
                summary_record_amount_total += float(final_amt)
                sdl_emp = '%0*d' % (7, 0)
                summary_record = 'F'.ljust(1) + \
                                '0'.ljust(1) + \
                                str(company_data.company_code)[:10].ljust(10) + \
                                'PTE'.ljust(3) + \
                                '01'.ljust(2) + \
                                ' '.ljust(1) + \
                                '01'.ljust(2) + \
                                str(year_month).ljust(6) + \
                                sdl_salary_rule_code.ljust(2) + \
                                str(final_amt).ljust(12) + \
                                str(sdl_emp).ljust(7) + \
                                ' '.ljust(103) + "\r\n"
                tmp_file.write(summary_record)
            for payslip in payslip_ids:
                employee_status = ''
                contract_id = hr_contract_obj.search([('employee_id', '=', payslip.employee_id.id), '|',
                                                      ('date_end','>=', payslip.date_from),
                                                      ('date_end','=',False)])
                old_contract_id = hr_contract_obj.search([('employee_id', '=', payslip.employee_id.id),
                                                          ('date_end','<=', payslip.date_from)])
                for contract in contract_id:
                    if payslip.employee_id.active == False:
                        employee_status = 'L'
                    elif contract.date_start >= payslip.date_from and not old_contract_id:
                        employee_status = 'N'
                    else:
                        employee_status = 'E'
                salary_rule_code = ''
                amount = gross = 0.0
                sdl_salary_rule_code = fwl_salary_rule_code = ecf_salary_rule_code = cdac_salary_rule_code = sinda_salary_rule_code = mbmf_salary_rule_code = cpf_salary_rule_code = ''
                sdl_amount = fwl_amount = ecf_amount = cdac_amount = sinda_amount = mbmf_amount = cpf_amount = 0.0
                for line in payslip.line_ids:
                    if line.register_id.name == 'CPF':
                        cpf_salary_rule_code = '01'
                        cpf_amount += line.amount
                    elif line.register_id.name == 'CPF - MBMF':
                        mbmf_salary_rule_code = '02'
                        mbmf_amount += line.amount
                    elif line.register_id.name == 'CPF - SINDA':
                        sinda_salary_rule_code = '03'
                        sinda_amount += line.amount
                    elif line.register_id.name == 'CPF - CDAC':
                        cdac_salary_rule_code = '04'
                        cdac_amount += line.amount
                    elif line.register_id.name == 'CPF - ECF':
                        ecf_salary_rule_code = '05'
                        ecf_amount += line.amount
                    elif line.register_id.name == 'CPF - FWL':
                        fwl_salary_rule_code = '08'
                        fwl_amount += line.amount

                    if line.salary_rule_id.code in ['GROSS']:
                        gross = line.amount
                        gross = gross * 100
                        new_gross = int(round(gross))
                        if new_gross < 0:
                            new_gross = new_gross * -1
                        final_gross = '%0*d' % (10, new_gross)
                identificaiton_id = ''
                if payslip.employee_id.identification_id:
                    if payslip.employee_id.identification_id.__len__() <= 9:
                        identificaiton_id += tools.ustr(payslip.employee_id.identification_id.ljust(9))
                    else:
                        identificaiton_id += tools.ustr(payslip.employee_id.identification_id[0:9].ljust(9))
                else:
                    identificaiton_id = ' '.ljust(9)
                employee_name_text = ''
                if payslip.employee_id.name:
                    if payslip.employee_id.name.__len__() <= 22:
                        employee_name_text += tools.ustr(payslip.employee_id.name.ljust(22))
                    else:
                        employee_name_text += tools.ustr(payslip.employee_id.name[0:22].ljust(22))
                else:
                    employee_name_text = ' '.ljust(22)
                if cpf_salary_rule_code and cpf_amount:
                    total_record += 1
                    cpf_amount = cpf_amount*100
                    new_amt = int(round(cpf_amount))
                    if new_amt < 0 :
                        new_amt = new_amt * -1
                    final_amt = '%0*d' % (12, new_amt)
                    detail_record = 'F'.ljust(1) + \
                                    '1'.ljust(1) + \
                                    str(company_data.company_code)[:10].ljust(10) + \
                                    'PTE'.ljust(3) + \
                                    '01'.ljust(2) + \
                                    ' '.ljust(1) + \
                                    '01'.ljust(2) + \
                                    str(year_month).ljust(6) + \
                                    cpf_salary_rule_code.ljust(2) + \
                                    identificaiton_id + \
                                    str(final_amt).ljust(12) + \
                                    final_gross.ljust(10) + \
                                    '0000000000'.ljust(10) + \
                                    employee_status.ljust(1) + \
                                    employee_name_text + \
                                    ' '.ljust(58) + "\r\n"
                    tmp_file.write(detail_record)
                
                if mbmf_salary_rule_code and mbmf_amount:
                    total_record += 1
                    mbmf_amount = mbmf_amount*100
                    new_amt = int(round(mbmf_amount))
                    if new_amt < 0 :
                        new_amt = new_amt * -1
                    final_amt = '%0*d' % (12, new_amt)
                    detail_record = 'F'.ljust(1) + \
                                    '1'.ljust(1) + \
                                    str(company_data.company_code)[:10].ljust(10) + \
                                    'PTE'.ljust(3) + \
                                    '01'.ljust(2) + \
                                    ' '.ljust(1) + \
                                    '01'.ljust(2) + \
                                    str(year_month).ljust(6) + \
                                    mbmf_salary_rule_code.ljust(2) + \
                                    identificaiton_id + \
                                    str(final_amt).ljust(12) + \
                                    final_gross.ljust(10) + \
                                    '0000000000'.ljust(10) + \
                                    ' ' + \
                                    employee_name_text + \
                                    ' '.ljust(58) + "\r\n"
                    tmp_file.write(detail_record)
                
                if sinda_salary_rule_code and sinda_amount:
                    total_record += 1
                    sinda_amount = sinda_amount*100
                    new_amt = int(round(sinda_amount))
                    if new_amt < 0 :
                        new_amt = new_amt * -1
                    final_amt = '%0*d' % (12, new_amt)
                    detail_record = 'F'.ljust(1) + \
                                    '1'.ljust(1) + \
                                    str(company_data.company_code)[:10].ljust(10) + \
                                    'PTE'.ljust(3) + \
                                    '01'.ljust(2) + \
                                    ' '.ljust(1) + \
                                    '01'.ljust(2) + \
                                    str(year_month).ljust(6) + \
                                    sinda_salary_rule_code.ljust(2) + \
                                    identificaiton_id + \
                                    str(final_amt).ljust(12) + \
                                    final_gross.ljust(10) + \
                                    '0000000000'.ljust(10) + \
                                    ' ' + \
                                    employee_name_text + \
                                    ' '.ljust(58) + "\r\n"
                    tmp_file.write(detail_record)
                
                if cdac_salary_rule_code and cdac_amount:
                    total_record += 1
                    cdac_amount = cdac_amount*100
                    new_amt = int(round(cdac_amount))
                    if new_amt < 0 :
                        new_amt = new_amt * -1
                    final_amt = '%0*d' % (12, new_amt)
                    detail_record = 'F'.ljust(1) + \
                                    '1'.ljust(1) + \
                                    str(company_data.company_code)[:10].ljust(10) + \
                                    'PTE'.ljust(3) + \
                                    '01'.ljust(2) + \
                                    ' '.ljust(1) + \
                                    '01'.ljust(2) + \
                                    str(year_month).ljust(6) + \
                                    cdac_salary_rule_code.ljust(2) + \
                                    identificaiton_id + \
                                    str(final_amt).ljust(12) + \
                                    final_gross.ljust(10) + \
                                    '0000000000'.ljust(10) + \
                                    ' ' + \
                                    employee_name_text + \
                                    ' '.ljust(58) + "\r\n"
                    tmp_file.write(detail_record)
                
                if ecf_salary_rule_code and ecf_amount:
                    total_record += 1
                    ecf_amount = ecf_amount*100
                    new_amt = int(round(ecf_amount))
                    if new_amt < 0 :
                        new_amt = new_amt * -1
                    final_amt = '%0*d' % (12, new_amt)
                    detail_record = 'F'.ljust(1) + \
                                    '1'.ljust(1) + \
                                    str(company_data.company_code)[:10].ljust(10) + \
                                    'PTE'.ljust(3) + \
                                    '01'.ljust(2) + \
                                    ' '.ljust(1) + \
                                    '01'.ljust(2) + \
                                    str(year_month).ljust(6) + \
                                    ecf_salary_rule_code.ljust(2) + \
                                    identificaiton_id + \
                                    str(final_amt).ljust(12) + \
                                    final_gross.ljust(10) + \
                                    '0000000000'.ljust(10) + \
                                    ' ' + \
                                    employee_name_text + \
                                    ' '.ljust(58) + "\r\n"
                    tmp_file.write(detail_record)
                
                if include_fwl and fwl_salary_rule_code and fwl_amount:
                    total_record += 1
                    fwl_amount = fwl_amount*100
                    new_amt = int(round(fwl_amount))
                    if new_amt < 0 :
                        new_amt = new_amt * -1
                    final_amt = '%0*d' % (12, new_amt)
                    detail_record = 'F'.ljust(1) + \
                                    '1'.ljust(1) + \
                                    str(company_data.company_code)[:10].ljust(10) + \
                                    'PTE'.ljust(3) + \
                                    '01'.ljust(2) + \
                                    ' '.ljust(1) + \
                                    '01'.ljust(2) + \
                                    str(year_month).ljust(6) + \
                                    fwl_salary_rule_code.ljust(2) + \
                                    identificaiton_id + \
                                    str(final_amt).ljust(12) + \
                                    final_gross.ljust(10) + \
                                    '0000000000'.ljust(10) + \
                                    ' ' + \
                                    employee_name_text + \
                                    ' '.ljust(58) + "\r\n"
                    tmp_file.write(detail_record)

            summary_record_amount_total = '%0*d' % (15,summary_record_amount_total)
            total_record = total_record + 2
            total_record = '%0*d' % (7, total_record)
            trailer_record = 'F'.ljust(1) + \
                            '9'.ljust(1) + \
                            str(company_data.company_code)[:10].ljust(10) + \
                            'PTE'.ljust(3) + \
                            '01'.ljust(2) + \
                            ' '.ljust(1) + \
                            '01'.ljust(2) + \
                            str(total_record).ljust(7) + \
                            str(summary_record_amount_total).ljust(15) + \
                            ' '.ljust(108) + "\r\n"
            tmp_file.write(trailer_record)
        finally:
            if tmp_file:
                tmp_file.close()
        file = open(tgz_tmp_filename, "rb")
        out = file.read()
        file.close()
        res = base64.b64encode(out)
        
        if not start_date and end_date:
            return ''
        end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
        monthyear = end_date.strftime('%b%Y')
        if company_data.company_code:
            company_uen=company_data.company_code
        else:
            raise ValidationError(_("You must be enter company-code in company detail !"))
        file_name = company_uen+monthyear+'01.txt'
        module_rec = self.env['binary.cpf.text.file.wizard'].create({'name': file_name, 'cpf_txt_file' : res})
        return {'name': _('Text File'),
                'res_id' : module_rec.id,
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'binary.cpf.text.file.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context}
    
cpf_rule_text_file()

class binary_cpf_text_file_wizard(models.TransientModel):
    _name = 'binary.cpf.text.file.wizard'

    name = fields.Char('Name', size=64)
    cpf_txt_file = fields.Binary('Click On Download Link To Download Text File', readonly=True)
    
    @api.multi
    def action_back(self):
        if self._context is None:
            context = {}
        return {'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'cpf.rule.text.file',
                'target': 'new'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: