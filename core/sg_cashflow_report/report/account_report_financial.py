import time
from odoo import api, models, _
from odoo.exceptions import UserError

class ReportFinancial(models.AbstractModel):
    _inherit = 'report.account.report_financial'

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']
        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * report.sign,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type or False, #used to underline the financial report balances
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * report.sign

            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.00,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                    }
                    report_name_obj = self.env['account.financial.report'].search([('id','=',data['account_report_id'][0])])
                    for cash_report in report_name_obj:
                        if cash_report.name == 'Statement Of Cash Flow':
                            year_from = data['date_from'][:4]
                            year_to = data['date_to'][:4]

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-01-01'),('date','<=',year_to+'-01-31'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['jan_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            if data['date_to'] == year_to+'-02-29':
                                move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-02-01'),('date','<=',year_to+'-02-29'),('account_id','=',account.id)])
                            else:
                                move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-02-01'),('date','<=',year_to+'-02-28'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['feb_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-03-01'),('date','<=',year_to+'-03-31'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['mar_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-04-01'),('date','<=',year_to+'-04-30'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['apr_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-05-01'),('date','<=',year_to+'-05-31'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['may_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-06-01'),('date','<=',year_to+'-06-30'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['jun_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-07-01'),('date','<=',year_to+'-07-31'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['july_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-08-01'),('date','<=',year_to+'-08-31'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['aug_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-09-01'),('date','<=',year_to+'-09-30'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['sep_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-10-01'),('date','<=',year_to+'-10-31'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['oct_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-11-01'),('date','<=',year_to+'-11-30'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['nov_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                            debit_bal,credit_bal=0.00,0.00
                            move_line_ids = self.env['account.move.line'].search([('date','>=',year_from+'-12-01'),('date','<=',year_to+'-12-31'),('account_id','=',account.id)])
                            for line in move_line_ids:
                                debit_bal += line.debit
                                credit_bal += line.credit
                            vals['dec_bal'] = '{0:,.2f}'.format(debit_bal - credit_bal)

                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * report.sign
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        return lines

ReportFinancial()
