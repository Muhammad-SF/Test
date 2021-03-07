# -*- encoding: utf-8 -*-
import base64
import tempfile
from datetime import datetime
from odoo import fields, models, api

class BinaryUobBankFileWizard(models.TransientModel):
    _name = 'binary.uob.bank.file.wizard'

    @api.model
    def _get_file_name(self):
        create_date = datetime.today()
        date = create_date.strftime('%d%m')
        file_name = 'UGBI' + date + '.txt'
        return file_name

    name = fields.Char('Name', size=64, default=_get_file_name)
    cpf_txt_file = fields.Binary('Click On Download Link To Download Text File', readonly=True)

    @api.multi
    def get_back_action(self):
        return {
            'name': 'UOB Text File',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'uob.bank.specification',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

BinaryUobBankFileWizard()

class UobBankSpecification(models.TransientModel):
    _name = 'uob.bank.specification'

    service_type = fields.Selection([('express', 'GIRO Express Service'),('normal', 'GIRO Normal Service')], string='Service Type', required=True)
    payment_type = fields.Selection([('P', 'Payments'),('R', 'Payroll'),('C', 'Collection')], string='Payment Type', required=True)
    originating_bic_code = fields.Char('Originating BIC Code', size=11, required=True)
    account_number = fields.Char('Originating Account Number', size=34, required=True)
    originator_name = fields.Char("Originator's Name", size=140, required=True)
    value_date = fields.Date("Value Date", required=True, default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    ultimate_originating_customer = fields.Char("Ultimate Originating Customer", size=140)
    bulk_customer_ref = fields.Char("Bulk Customer Reference", size=16, required=True)
    software_label = fields.Char("Software Label", size=10)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    msg_seq_no = fields.Char('Sequence Number',size=2, required=True, default='01')
    processing_mode = fields.Selection([('I', 'Immediate (FAST)'),('B', 'Batch (GIRO)')], string='Processing Mode')
    
    @api.multi
    def get_text_file(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        context = dict(context)
        tgz_tmp_filename = tempfile.mktemp('.' + "txt")
        tmp_file = open(tgz_tmp_filename, "wb")
        try:
            start_date = self.start_date
            end_date = self.end_date
            if not start_date and end_date:
                return False
            # Batch Header Record
            header2_record = '1'
            create_date = datetime.today()
            date = create_date.strftime('%d%m')
            file_name = 'UGBI' + date + '.txt'
            header2_record += file_name.ljust(10)
            header2_record += self.payment_type
            header2_record += self.service_type.ljust(10)
            header2_record += self.processing_mode or ''
            header2_record += ''.ljust(12)
            header2_record += self.originating_bic_code.ljust(11)
            header2_record += 'SGD'.ljust(3)
            header2_record += self.account_number.ljust(34)
            header2_record += self.originator_name.ljust(140)
            value_date = datetime.strptime(self.value_date, "%Y-%m-%d")
            header2_record += value_date.strftime('%Y%m%d').ljust(8)
            header2_record += self.ultimate_originating_customer or ('').ljust(140)
            header2_record += self.bulk_customer_ref or ('').ljust(16)
            header2_record += self.software_label or ('').ljust(10)
            tmp_file.write(header2_record)

            emp_ids = self.env['hr.employee'].search([('bank_account_id','!=',False)], order="name")
            total_credit_trans = 0
            summary_amount = 0
            hash_total = 0
            for employee in emp_ids:
                total_amount = 0
                payment_detail = '2'
                if employee.bank_account_id.bank_bic:
                    payment_detail += employee.bank_account_id.bank_bic.ljust(11)
                if employee.bank_account_id.acc_number:
                    payment_detail += employee.bank_account_id.acc_number.ljust(34)
                if employee.bank_account_id.partner_id and employee.bank_account_id.partner_id.name:
                    payment_detail += employee.bank_account_id.partner_id.name.ljust(140)
                payment_detail += 'SGD'.ljust(3)
                payslip_id = self.env['hr.payslip'].search([
                    ('employee_id', '=', employee.id),
                    ('date_from', '>=', start_date),
                    ('date_to', '<=', end_date),
                    ('state', 'in', ['done'])
                ])
                if payslip_id:
                    total_credit_trans += 1
                    for payslip in self.env['hr.payslip'].browse(payslip_id.ids):
                        for line in payslip.line_ids:
                            if line.code == "NET" and line.amount != 0:
                                total_amount += line.amount
                    payment_detail += ("".join((str(total_amount)).split("."))).rjust(18,'0')
                    summary_amount += total_amount
                    # End to End ID
                    msg = 'salary payment'
                    payment_detail += msg or ''.ljust(35)
                    # Mandate ID
                    payment_detail += 'DDA Ref'.ljust(35)
                    # Purpose Code
                    payment_detail += 'SALA'.ljust(4)
                    # Remittance Information
                    payment_detail += ''.ljust(140)
                    # Ultimate Payer/Beneficiary Name
                    payment_detail += ''.ljust(140)
                    # Customer Reference
                    payment_detail += ''.ljust(16)
                    # Filler
                    payment_detail += ''.ljust(38)

                    tmp_file.write(payment_detail)

                    # Record of Batch Trailer (Hash Code Computation)
                    sum1 = sum2 = sum3 = hash_total1 = 0
                    # Originating BIC Code
                    sum1_org_bic_code = self.originating_bic_code
                    if sum1_org_bic_code:
                        sum1_org_bic_code_up = sum1_org_bic_code.upper()
                        sum1 = 0
                        counter1 = 1
                        for bic_code in sum1_org_bic_code_up.ljust(11, ' '):
                             sum1 += (counter1) * (ord(bic_code))
                             counter1 += 1

                    # Originating Account No.
                    sum1_org_acc_number = self.account_number
                    if sum1_org_acc_number:
                        sum1_org_acc_number_up = sum1_org_acc_number.ljust(34, ' ')
                        sum2 = 0
                        counter2 = 1
                        for acc_num in str(sum1_org_acc_number_up):
                             sum2 += (counter2) * (ord(acc_num))
                             counter2 += 1

                    # Originating Account Name
                    sum1_org_acc_name = self.originator_name
                    if sum1_org_acc_name:
                        sum3 = 0
                        counter3 = 1
                        sum1_org_acc_name = sum1_org_acc_name.ljust(140, ' ')
                        for acc_name in sum1_org_acc_name:
                             sum3 += (counter3) * (ord(acc_name))
                             counter3 += 1

                    # First Total For Hash Code
                    hash_total1 = sum1 + sum2 + sum3
                    # Set Hash Code to Zero
                    hash_code_set = 0
                    # Payment Type
                    if self.payment_type == 'P':
                        payment_code = 20
                    elif self.payment_type == 'R':
                        payment_code = 22
                    elif self.payment_type == 'C':
                        payment_code = 30

                    # For Each Detail Records
                    if hash_code_set == 9:
                        hash_code_set = 1
                    else:
                        hash_code_set += 1

                    rcv_sum1 = rcv_sum2 = rcv_sum3 = rcv_sum4 = rcv_sum5 = rcv_sum6 = rcv_sum7 = hash_total2 = 0
    
                    # Receiving BIC Code
                    if employee.bank_account_id and employee.bank_account_id.bank_bic:
                        sum1_rcv_bic_code = employee.bank_account_id.bank_bic
                        if sum1_rcv_bic_code:
                            sum1_rcv_bic_code_up = sum1_rcv_bic_code.upper()
                            rcv_sum1 = 0
                            rcv_counter1 = 1
                            for r_bic_code in sum1_rcv_bic_code_up.ljust(11,' '):
                                 rcv_sum1 += (rcv_counter1) * (ord(r_bic_code))
                                 rcv_counter1 += 1

                    # Receiving Account Number
                    if employee.bank_account_id and employee.bank_account_id.acc_number:
                        sum1_rcv_acc_number = employee.bank_account_id.acc_number.ljust(34,' ')
                        if sum1_rcv_acc_number:
                            rcv_sum2 = 0
                            rcv_counter2 = 1
                            for r_acc_number in sum1_rcv_acc_number:
                                 rcv_sum2 += (rcv_counter2) * (ord(r_acc_number))
                                 rcv_counter2 += 1
                            rcv_sum2 = (rcv_sum2 * hash_code_set)

                    # Receiving Account Name
                    if employee.bank_account_id and employee.bank_account_id.partner_id and employee.bank_account_id.partner_id.name:
                        sum1_rcv_acc_name = employee.bank_account_id.partner_id.name.ljust(140,' ')
                        if sum1_rcv_acc_name:
                            rcv_sum3 = 0
                            rcv_counter3 = 1
                            for r_acc_name in sum1_rcv_acc_name:
                                 rcv_sum3 += (rcv_counter3) * (ord(r_acc_name))
                                 rcv_counter3 += 1
                            rcv_sum3 = (rcv_sum3 * hash_code_set)

                    # Currency
                    rcv_crncy = 'SGD'.ljust(3)
                    rcv_sum4 = 0
                    rcv_counter4 = 1
                    for r_cur in rcv_crncy:
                         rcv_sum4 += (rcv_counter4) * (ord(r_cur))
                         rcv_counter4 += 1

                    # Amount
                    if total_amount:
                        rcv_total_amount_detail = ("".join((str(total_amount)).split("."))).ljust(18,' ')
                        if rcv_total_amount_detail:
                            rcv_sum5 = 0
                            rcv_counter5 = 1
                            for rcv_amt in rcv_total_amount_detail:
                                 rcv_sum5 += (rcv_counter5) * (ord(rcv_amt))
                                 rcv_counter5 += 1

                    # Purpose Code
                    rcv_p_code = 'SALA'.ljust(4)
                    rcv_sum6 = 0
                    rcv_counter6 = 1
                    for p_code in rcv_p_code:
                         rcv_sum6 += (rcv_counter6) * (ord(p_code))
                         rcv_counter6 += 1

                    rcv_sum7 = rcv_sum1 + rcv_sum2 + rcv_sum3 + rcv_sum4 + rcv_sum5 + rcv_sum6 + (payment_code*hash_code_set)

                    # Second Total For Hash Code
                    hash_total2 = hash_total2 + rcv_sum7
                    # Final Total For Hash Code
                    hash_total = hash_total1 + hash_total2

            # Record Type
            summary_details = '9'
            # Total  Amount
            summary_details += ("".join((str(summary_amount)).split("."))).rjust(18,'0')
            # Total Number of Transactions
            summary_details += ("".join(str(total_credit_trans))).rjust(7,'0')
            # Hash Total
            if hash_total:
                summary_details += ("".join(str(hash_total))).rjust(16,'0')
            # Filler
            summary_details += ''.ljust(1013)
            summary_details += '\r\n'
            tmp_file.write(summary_details)
        finally:
            tmp_file.close()
        file = open(tgz_tmp_filename, "rb")
        out = file.read()
        file.close()
        res_base = base64.b64encode(out) 
        binary_dbs_txt_obj = self.env['binary.uob.bank.file.wizard']
        file_name = binary_dbs_txt_obj.with_context(context)._get_file_name()
        dbs_rec = binary_dbs_txt_obj.create({'name': file_name, 'cpf_txt_file': res_base})
        return {
              'name': 'Bank Specification File',
              'res_id': dbs_rec.id,
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'binary.uob.bank.file.wizard',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': context
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: