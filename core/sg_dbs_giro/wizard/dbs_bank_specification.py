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
import string
import base64
import datetime
import tempfile
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class binary_dbs_bank_file_wizard(models.TransientModel):

    _name = 'binary.dbs.bank.file.wizard'

    name = fields.Char('Name', size = 64, default = '_get_file_name')
    cpf_txt_file = fields.Binary('Click On Download Link To Download Text File', readonly = True)

    @api.model
    def _get_file_name(self):
        context = self.env.context
        if context is None:
            context = {}
        context = dict(context)
        start_date = context.get('start_date', False) or False
        end_date = context.get('end_date', False) or False
        if not start_date and end_date:
            return 'dbs_txt_file.txt'
        end_date = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
        monthyear = end_date.strftime('%b%Y')
        file_name = 'dbs_txt_file_' + monthyear + '.txt'
        return file_name

    @api.multi
    def get_wiz_action(self):
        context = self.env.context
        return {
              'name': 'dbs.bank.specification.form',
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'dbs.bank.specification',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': context
        }

class dbs_bank_specification(models.TransientModel):

    _name = 'dbs.bank.specification'

#    branch_number = fields.Integer('Branch Number', size = 3, required = True)
#    bank_number = fields.Integer('Bank Number', size = 4, required = True, default = 7171)
    batch_ref = fields.Char('Batch Reference', size = 35, required = True)
    batch_number = fields.Integer('Batch Number', size = 5, required = True)
    account_number = fields.Char('Account Number', size = 34, required = True)
    originator_name = fields.Char("Originator's Name", size = 20, required = True)
    start_date = fields.Date('Start Date', required = True)
    end_date = fields.Date('End Date', required = True)
    value_date = fields.Date("Value Date", required = True, default = time.strftime('%Y-%m-%d'))
#    msg_seq_no = fields.Char("Message Sequence Number", size = 5, required = True)
    sender_comp_id = fields.Char("Sender's Company ID", size = 8, required = True)
    payment_type = fields.Selection([('20', 'Payments'),('22', 'Salary'),
                                      ('30', 'Collection')],
                                      'Payment Type', required = True)


    @api.multi
    def get_text_file(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        context = dict(context)
        bank_data = {}
        data = self.read([])
        if data:
            bank_data = data[0]
#        if bank_data and bank_data.get('branch_number') and len(str(bank_data.get('branch_number'))) > 3:
#            raise ValidationError(_('Branch number length must be less than or equal to three digits.'))
        if bank_data and bank_data.get('batch_number') and len(str(bank_data.get('batch_number'))) > 5:
            raise ValidationError(_('Batch number length must be less than or equal to five digits.'))
#        if bank_data and bank_data.get('account_number') and len(str(bank_data.get('account_number'))) > 11:
#            raise ValidationError(_('Account number length must be less than or equal to eleven digits.'))
        context.update({'account_number': bank_data.get("account_number"),
                        'start_date': bank_data.get("start_date", False), 'end_date': bank_data.get("end_date", False),
                        'value_date': bank_data.get("value_date"), 'batch_number': bank_data.get("batch_number"),
                        'originator_name':bank_data.get('originator_name'),'payment_type': bank_data.get('payment_type', ''),
                        'sender_comp_id':bank_data.get('sender_comp_id'),'batch_ref': bank_data.get('batch_ref', '')})
        tgz_tmp_filename = tempfile.mktemp('.' + "txt")
        tmp_file = open(tgz_tmp_filename, "wr")
        try:
            start_date = context.get('start_date', False) or False
            end_date = context.get('end_date', False)
            payslip_obj = self.env['hr.payslip']
            if not start_date and end_date:
                return False
            header2_record = ''
            batch_number = context.get('batch_number')
            if batch_number > 89999:
                raise ValidationError(_('Batch Number must be between 00001 to 89999.'))
            value_date = datetime.datetime.strptime(context.get("value_date"), "%Y-%m-%d")
            """ First 8 digit for date &time and 14 space in header(Creation Date & Time)"""
            header2_record += time.strftime('%d%m%Y%H%M%S').ljust(14) 
            """ Sender's Company ID in header"""
            header2_record += context.get('sender_comp_ids', '').ljust(8)
            """ First 8 Digit for Value Date and 8 space in header """
            header2_record += value_date.strftime('%d%m%Y').ljust(8)
            """ Originating Account Number """
            header2_record += context.get('account_number').ljust(34)
            """Originator’s Name"""
            header2_record += context.get('originator_name').ljust(140)
            """ Here leave the space in the header """
            header2_record += ''.ljust(34)
            """ Unique Batch ID Generated in the header """
            header2_record += str(batch_number).ljust(5)
            """ Batch Reference in the header """
            header2_record += context.get('batch_ref', '').ljust(35)
            """ Indicator Value 'C' in 279 space from the header """
            header2_record += 'C'.ljust(1)
            """Filer in the header """
            header2_record += ''.ljust(719)
            """ Record Type Value '01' in the header """
            header2_record += '01'.ljust(2)
            """Carriage Return <CR> & Line Feed <LF>"""
            header2_record += '\r\n'
            tmp_file.write(header2_record)
            emp_rec = self.env["hr.employee"].search([('bank_account_id', '!=', False)], order = "name")
            total_credit_trans = 0
            summary_amount = 0
            hash_total = 0
            if emp_rec and emp_rec.ids:
                payslip_id = payslip_obj.search([('employee_id', 'in', emp_rec.ids),
                                                 ('date_from', '>=', start_date),
                                                 ('date_to', '<=', end_date),
                                                 ('state', 'in', ['done'])
                                                 ])
                if len(payslip_id.ids) == 0:
                        raise ValidationError(_('There is no single payslip details found between selected date %s and %s') % (start_date, end_date))
            for employee in emp_rec:
                payslip_id = payslip_obj.search([('employee_id', '=', employee.id),
                                                 ('date_from', '>=', start_date),
                                                 ('date_to', '<=', end_date),
                                                 ('state', 'in', ['done'])
                                                 ])
                total_amount = 0
                emp_name = employee and employee.name or ''
#                if not employee.gender:
#                    raise ValidationError(_('There is no gender define for %s employee.' % (emp_name)))
#                if not employee.birthday:
#                    raise ValidationError(_('There is no birth date define for %s employee.' % (emp_name)))
#                if not employee.identification_id:
#                    raise ValidationError(_('There is no identification no define for %s employee.' % (emp_name)))
#                if not employee.work_phone or not employee.work_email:
#                    raise ValidationError(_('You must be configure Contact no or email for %s employee.' % (emp_name)))
                payslip_ref = ''
                if payslip_id and payslip_id.ids:
                    for payslip in payslip_id:
                        payment_detail = ''
                        payslip_ref = payslip.number
                        """ Details of Record """
                        """ Type of Payment """
                        payment_detail += context.get('payment_type', '').ljust(2)
                        """ Beneficiary Reference """
                        payment_detail += emp_name.ljust(35)
                        """Receiving Bank BIC """
                        bank_bic = employee.bank_account_id and employee.bank_account_id.bank_bic or ''
                        payment_detail += bank_bic.ljust(35)
                        """Receiving Account Number"""
                        emp_bank_ac_no = employee.bank_account_id and employee.bank_account_id.acc_number or ''
                        branch_code = employee.bank_account_id and employee.bank_account_id and \
                                      employee.bank_account_id.branch_code or ''
                        emp_account_code = branch_code + emp_bank_ac_no
                        payment_detail += emp_account_code.ljust(34)
    
                        """Receiving Account Name"""
                        rec_account_name = employee and employee.bank_account_id and employee.bank_account_id.partner_id \
                                         and employee.bank_account_id.partner_id.name or ''
                        payment_detail += rec_account_name.ljust(140)
    
                        """Purpose Code of payment"""
                        payment_detail += 'SALA'.ljust(4)
                        """Bulk Transfer Currency as Value:‘SGD’"""
                        payment_detail += 'SGD'.ljust(3)
                        """ Amount In Cents """
                        total_amount = 0.0
                        for line in payslip.line_ids:
                            if line.code == "NET":
                                total_amount = line.amount
                        summary_amount += total_amount
                        if total_amount:
                            total_amount = int(round(total_amount * 100))
                            payment_detail += ('%011d' % total_amount).rjust(11)
                        else:
                            payment_detail += ('%011d' % 0).rjust(11)
                        """ DDA Reference """
                        payment_detail += 'DDA Ref'.ljust(35)
                        """ Details of Payment """
                        payment_detail += payslip_ref.ljust(140)
                        """ Priority Indicator as Value:'N' """
                        payment_detail += 'N'.ljust(1)
                        """ Ultimate Originator Name/Reference """
                        ultimate_originator = 'Ultimate Originator' + context.get('originator_name', '')
                        payment_detail += ultimate_originator.ljust(140)
                        """ Ultimate Receiver Name/Reference """
                        ultimate_rec_name = 'Ultimate Receiving Name' + emp_name
                        payment_detail += ultimate_rec_name.ljust(140)
                        """Filer in the header """
                        payment_detail += ''.ljust(278)
                        """ Record Type Value '10' in the header """
                        payment_detail += '10'.ljust(2)
                        """Carriage Return <CR> & Line Feed <LF>"""
                        payment_detail += '\r\n'
                        tmp_file.write(payment_detail)
                        """ Record of Batch Trailer """
                        receiving_acc_no = ''
                        originator_acc_no = ''
                        if emp_bank_ac_no.__len__() <= 11:
                            receiving_acc_no = emp_bank_ac_no.ljust(11, '0')
                        else:
                            receiving_acc_no = emp_bank_ac_no[0:11].ljust(11)
                        if len(context.get('account_number')) <= 11:
                            originator_acc_no = str(context.get('account_number')).ljust(11, '0')
                        else:
                            originator_acc_no = context.get('account_number')[0:11].ljust(11)
                        """ Here, If the account number has an alphabet, convert the alphabet to ‘0’. """
                        receiving_acc_no = str(receiving_acc_no.replace('-', ''))
                        originator_acc_no = list(originator_acc_no.replace('', ','))
                        lower_alphabet = list(string.ascii_lowercase)
                        upper_alphabet = list(string.ascii_uppercase)
                        recv_accunt = origin_acc_no = ''
                        if len(receiving_acc_no) <= 11:
                            receiving_acc_no = receiving_acc_no.ljust(11, '0')
                        receiving_acc_no = list(receiving_acc_no.replace('', ','))
                        for rec_account_no in receiving_acc_no:
                            if rec_account_no in lower_alphabet or rec_account_no in upper_alphabet:
                                recv_accunt += '0'
                            if rec_account_no != ',' and rec_account_no not in lower_alphabet and rec_account_no not in upper_alphabet:
                                recv_accunt += rec_account_no
                        for org_account_no in originator_acc_no:
                            if org_account_no in lower_alphabet or org_account_no in upper_alphabet:
                                origin_acc_no += '0'
                            if org_account_no != ',' and org_account_no not in lower_alphabet and org_account_no not in upper_alphabet:
                                origin_acc_no += org_account_no
                        """Derivation of Account Number Hash Total
                           Subtract the first 11 characters of originating account from
                           the first 11 characters of each receiving account.
                           Take absolute values. """
                        recev_orig_acc_result = abs(int(recv_accunt)) - abs(int(origin_acc_no))
                        hash_total += recev_orig_acc_result
                        total_credit_trans += 1
            """ Batch summary"""
            summary_details = ""
            """ Total Number Of Credit Transactions """
            summary_details += ('%011d' % total_credit_trans).rjust(11, '0')
            """ Total Credit Amount In Cents """
            summary_amount = str(summary_amount * 100)
            if summary_amount:
                summary_amount = int(summary_amount.split('.')[0])
            summary_details += ('%018d' % summary_amount).rjust(18, '0')
            """ Filler(5) & Total Number Of Debit Transactions & Total Debit Amount In Cents & Filler(26)"""
            summary_details += ''.rjust(11, '0') + ''.rjust(18, '0') + ''.rjust(26)
            """ Account Number Hash Total & Filler space(903)"""
            if hash_total:
                summary_details += ('%011d' % abs(hash_total))[:11].rjust(11)
            """Filler & Record Type & Carriage Return <CR> & Line Feed <LF>"""
            summary_details += ''.ljust(903) + '20'
            summary_details += '\r\n'
            tmp_file.write(summary_details)
            batch_number += 1
        finally:
            tmp_file.close()
        file = open(tgz_tmp_filename, "rb")
        out = file.read()
        file.close()
        res_base = base64.b64encode(out) 
        binary_dbs_txt_obj = self.env['binary.dbs.bank.file.wizard']
        file_name = binary_dbs_txt_obj.with_context(context)._get_file_name()
        dbs_rec = binary_dbs_txt_obj.create({'name': file_name, 'cpf_txt_file': res_base})
        return {
              'name': _('Text file'),
              'res_id': dbs_rec.id,
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'binary.dbs.bank.file.wizard',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': context
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
