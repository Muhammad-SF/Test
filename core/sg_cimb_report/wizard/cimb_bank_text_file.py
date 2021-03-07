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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class cimb_bank_text_file(models.TransientModel):

    _name = 'cimb.bank.text.file'

    source_account_number = fields.Integer('Source Account Number', size=11)
    account_name = fields.Char('Account Name', size=100)
    remark = fields.Char('Remark', size=80)
    transaction_date = fields.Date('Transaction Date')
    start_date = fields.Date('Start Date', default=time.strftime('%Y-01-01'))
    end_date = fields.Date('End Date', default=time.strftime('%Y-12-31'))

    @api.multi
    def download_cimb_bank_txt_file(self):
        '''
            The method used to call download file of wizard
            @self : Record Set
            @api.multi : The decorator of multi
            @return: Return of wizard of action in dictionary
            ---------------------------------------------------------------------------------------
        '''
        context = self.env.context
        context = dict(context)
        if context is None:
            context = {}
        cimb_bnk_data = self.read([])
        data = {}
        if cimb_bnk_data:
            data = cimb_bnk_data[0]
        start_date = data.get('start_date', False)
        end_date = data.get('end_date', False)
        if start_date >= end_date:
            raise ValidationError(_("You must be enter start date less than end date !"))
        context.update({'datas': data})
        emp_ids = self.env['hr.employee'].search([('bank_account_id', '!=', False)], order='name')
        payslip_ids = self.env['hr.payslip'].search([('employee_id', 'in', emp_ids.ids), 
                                                     ('cheque_number','=',False),
                                                     ('date_from', '>=', start_date), 
                                                     ('date_from', '<=', end_date), 
                                                     ('state', 'in', ['draft', 'done', 'verify'])], order = "employee_name")
        if not payslip_ids:
            raise ValidationError(_('There is no payslip found to generate text file.'))
#        here maked temporary csv file for pay
        tgz_tmp_filename = tempfile.mktemp('.' + "csv")
        tmp_file = False
        try:
            tmp_file = open(tgz_tmp_filename, "wr")
            net_amount_total=0.0
            detail_record = ''
            for payslip in payslip_ids:
                if not payslip.employee_id.bank_account_id:
                    raise ValidationError(_('There is no bank detail found for %s .' % (payslip.employee_id.name)))
                bank_list = []
                if not payslip.employee_id.bank_account_id.acc_number:
                    bank_list.append('Bank Account Number')
                if not payslip.employee_id.bank_account_id.branch_id:
                    bank_list.append('Branch Code')
                if not payslip.employee_id.bank_account_id.bank_bic:
                    bank_list.append('Bank Code')
#                if not payslip.employee_id.gender:
#                    raise ValidationError(_('There is no gender define for %s employee.' % (payslip.employee_id.name)))
#                if not payslip.employee_id.birthday:
#                    raise ValidationError(_('There is no birth date define for %s employee.' % (payslip.employee_id.name)))
#                if not payslip.employee_id.identification_id:
#                    raise ValidationError(_('There is no identification no define for %s employee.' % (payslip.employee_id.name)))
#                if not payslip.employee_id.work_phone or not payslip.employee_id.work_email:
#                    raise ValidationError(_('You must be configure Contact no or email for %s employee.' % (payslip.employee_id.name)))
                remaing_bank_detail = ''
                if bank_list:
                    for bank in bank_list:
                        remaing_bank_detail += tools.ustr(bank) + ', '
                    raise ValidationError(_('%s not found For %s Employee.' % (remaing_bank_detail, payslip.employee_id.name)))
                net_amount = 0.0
                for line in payslip.line_ids:
                    if line.code == 'NET':
                        net_amount = line.total
                        net_amount_total += line.total
                net_amount = '%.2f' % net_amount
                detail_record += tools.ustr(payslip.employee_id.bank_account_id.acc_number)[:40] + \
                            ',' + tools.ustr(payslip.employee_id.name)[:100] + \
                            ',SGD'.ljust(4) + \
                            ',' + tools.ustr(net_amount)[:17] + \
                            ',' + tools.ustr(context.get('datas')['remark'] or '')[:80] + \
                            ',' + tools.ustr(payslip.employee_id.bank_account_id.bank_bic)[:40] + \
                            ',' + tools.ustr(payslip.employee_id.bank_account_id.branch_id)[:40] + \
                            ',N'.ljust(2) + \
                            ''[:100] + "\r\n"
            net_amount_total = '%.2f' % net_amount_total
            transactiondate = datetime.datetime.strptime(context.get('datas')['transaction_date'], DEFAULT_SERVER_DATE_FORMAT)
            transactiondate = transactiondate.strftime('%Y%m%d')
            header_record = tools.ustr(context.get('datas')['source_account_number'])[:40] + \
                            ',' + tools.ustr(context.get('datas')['account_name'] or '')[:100] + \
                            ',SGD'.ljust(4) + \
                            ',' + tools.ustr(net_amount_total)[:17] + \
                            ',' + tools.ustr(context.get('datas')['remark'] or '')[:80] + \
                            ',' + tools.ustr(len(payslip_ids))[:5] + \
                            ',' + tools.ustr(transactiondate or '')[:8] + "\r\n"
            tmp_file.write(header_record)
            tmp_file.write(detail_record)
        finally:
            if tmp_file:
                tmp_file.close()
        file = open(tgz_tmp_filename, "rb")
        out = file.read()
        file.close()
        res = base64.b64encode(out)
        module_rec = self.env['binary.cimb.bank.text.file.wizard'].create({'name': 'CIMB_Bank.csv', 'cimb_bank_txt_file' : res})
        return {
          'name': _('CIMB Bank File'),
          'res_id' : module_rec.id,
          'view_type': 'form',
          "view_mode": 'form',
          'res_model': 'binary.cimb.bank.text.file.wizard',
          'type': 'ir.actions.act_window',
          'target': 'new',
          'context': context,
        }


class binary_cimb_bank_text_file_wizard(models.TransientModel):
    _name = 'binary.cimb.bank.text.file.wizard'

    name = fields.Char('Name', size=64, default='CIMB_Bank.csv')
    cimb_bank_txt_file = fields.Binary('Click On Download Link To Download File', readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: