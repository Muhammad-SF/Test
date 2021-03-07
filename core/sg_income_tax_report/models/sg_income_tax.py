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
from datetime import datetime,date
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    hr_contract_income_tax_ids = fields.One2many('hr.contract.income.tax', 'contract_id', 'Income Tax')

#    @api.constrains('hr_contract_income_tax_ids')
#    def _check_incomtax_year(self):
#        for contract in self:
#            if contract.hr_contract_income_tax_ids and contract.hr_contract_income_tax_ids.ids:
#                for incmtax in contract.hr_contract_income_tax_ids:
#                    domain = [('start_date', '<=', incmtax.end_date),
#                              ('end_date','>=', incmtax.start_date),
#                              ('contract_id', '=', contract.id),
#                              ]
#                    contract_ids = self.env['hr.contract.income.tax'].search(domain)
#                    if len(contract_ids) > 1:
#                        raise ValidationError('You can not configure multiple income tax that overlap on same date!')


class hr_contract_income_tax(models.Model):

    _name = 'hr.contract.income.tax'
    _rec_name = 'contract_id'


    @api.multi
    @api.depends('start_date', 'end_date', 'contract_id.employee_id')
    def _get_payroll_computational_data(self):
        for data in self:
            mbf = donation = CPF_designated_pension_provident_fund = payslip_net_amount = bonus_amount = gross_commission = transport_allowance = gross_amt = 0.00
            start_date = datetime.strptime(data.start_date, DEFAULT_SERVER_DATE_FORMAT)
            fiscal_year = start_date.year
            start_date = datetime.strptime(str(start_date.day) + "-" + str(start_date.month) + "-" + str(fiscal_year -1), '%d-%m-%Y')
            start_date = start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = datetime.strptime(data.end_date, DEFAULT_SERVER_DATE_FORMAT)
            end_date = datetime.strptime(str(end_date.day) + "-" + str(end_date.month) + "-" + str(fiscal_year -1), '%d-%m-%Y')
            end_date = end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            payslip_ids = self.env['hr.payslip'].search([('date_from', '>=', start_date), 
                                                         ('date_from', '<=', end_date),
                                                         ('employee_id', '=', data.contract_id.employee_id.id),
                                                         ('state', 'in', ['draft','done', 'verify'])])
            for payslip in payslip_ids:
                for line in payslip.line_ids:
                    if line.code == 'CPFMBMF':
                        mbf += line.total
                    if line.code in ['CPFSINDA', 'CPFCDAC', 'CPFECF']:
                        donation += line.total
                    if line.category_id.code == 'CAT_CPF_EMPLOYEE':
                        CPF_designated_pension_provident_fund += line.total
                    if line.code == 'GROSS':
                        payslip_net_amount += line.total
                    if line.code == 'SC121':
                        bonus_amount += line.total
                    if line.category_id.code == 'GROSS':
                        gross_amt += line.total
                    if line.code in ['SC102', 'SC103']:
                        gross_amt += line.total
                    if line.code in ['SC104', 'SC105']:
                        gross_commission += line.total
                    if line.code == 'TA':
                        transport_allowance += line.total
            for income_tax_line_rec in self:
                income_tax_line_rec.mbf = mbf or 0.0
                income_tax_line_rec.donation = donation or 0.0
                income_tax_line_rec.CPF_designated_pension_provident_fund = CPF_designated_pension_provident_fund or 0.0
                income_tax_line_rec.payslip_net_amount = payslip_net_amount or 0.0
                income_tax_line_rec.bonus_amount = bonus_amount or 0.0
                income_tax_line_rec.gross_commission = gross_commission or 0.0
                income_tax_line_rec.transport = transport_allowance or 0.0

#---------------------------------------------------# 
#                IR8A Fields
#---------------------------------------------------#

    contract_id = fields.Many2one('hr.contract', 'Contract')
    start_date = fields.Date('Assessment Start Date', default=date(date.today().year, 1, 1))
    end_date = fields.Date('Assessment End Date', default=date(date.today().year, 12, 31))
    cessation_date = fields.Date('Cessation Date')
    director_fee = fields.Float('18. Directors fee')
    gain_profit = fields.Float('19(a). Gains & Profit from Share Options For S10 (1) (g)')
    exempt_income = fields.Float('20. Exempt Income/ Income subject to Tax Remission', help='Cannot be blank if item 30 (Exempt/ Remission income indicator) is equal to:'
                                                                                            '\n1 = Tax Remission on Overseas Cost of Living Allowance (OCLA)'
                                                                                            '\n3 = Seaman'
                                                                                            '\n4 = Exemption'
                                                                                            '\n5 = Overseas Pension Fund with Tax Concession'
                                                                                            '\n7 = Income from Overseas Employment and Overseas Pension Fund with Tax Concession')
    employment_income = fields.Float('21. Amount of employment income for which tax is borne by employer', help='1. Cannot be blank if item 25 (Employee’s Income Tax borne by employer) is P.'
                                                                                                                '\n2. Must be blank if item 25 (Employee’s Income Tax borne by employer) is F or H.')
    benefits_kind = fields.Selection(selection=[('Y', "Benefits-in-kind rec'd"), 
                                                ('N', "Benefits-in-kind not rec'd")], string='23. Benefits-in-kind')
    section_applicable = fields.Selection(selection=[('Y', 'S45 applicable'), 
                                                     ('N', 'S45 not applicable')], string='24. Section 45 applicable', help='Section 45 applicable only applies to Non-resident Directors. Cannot be blank for non–resident director where withholding of tax on director’s fees may be applicable.')
    employee_income_tax = fields.Selection(selection=[('F', 'Tax fully borne by employer on employment income only'), 
                                                      ('P', 'Tax partially borne by employer on certain employment income items'),
                                                      ('H', 'A fixed amount of income tax liability borne by employee. Not applicable if income tax is fully paid by employee'),
                                                      ('N', 'Not Applicable')], string='25. Employees Income Tax borne by employer', help='F = Tax fully borne by employer'
                                                                                                                                          '\nP = Tax partially borne by employer'
                                                                                                                                          '\nH = A fixed amount of income tax is borne by employee. Not applicable if income tax is fully paid by employee'
                                                                                                                                          '\n1. Must be P if item 21 (Amount of employment income for which tax is borne by employer) is not blank'
                                                                                                                                          '\n2. Must be H if item 22 (Fixed Amount of income tax liability for which tax borne by employee) is not blank.')
    gratuity_payment = fields.Selection(selection=[('Y', 'Gratuity/ payment in lieu of notice/ex-gratia paid'),
                                                   ('N', 'No Gratuity/ payment in lieu of notice/ex-gratia paid')], string='26. Gratuity/ Notice Pay/ Ex-gratia payment/ Others')
    compensation = fields.Selection(selection=[('Y', ' Compensation / Retrenchment benefits paid'),
                                               ('N', 'No Compensation / Retrenchment benefits paid')], string='27. Compensation for loss of office')
    approve_obtain_iras = fields.Selection(selection=[('Y', 'Approval obtained from IRAS'),
                                                      ('N', 'No approval obtained from IRAS ')], string='27(a). Approval obtained from IRAS')
    approval_date = fields.Date('27(b). Date of approval')
    from_ir8s = fields.Selection(selection=[('Y', 'IR8S is applicable'), 
                                            ('N', 'IR8S is not applicable')], string='29. Form IR8S', help='Leave the field blank if IR8S is not applicable for the employee.')
    exempt_remission = fields.Selection(selection=[('1', 'Tax Remission on Overseas Cost of Living Allowance (OCLA)'),
                                                   ('3', 'Seaman'), 
                                                   ('4', 'Exemption'),
                                                   ('5', 'Overseas Pension Fund with Tax Concession'),
                                                   ('6', 'Income from Overseas Employment'),
                                                   ('7', 'Income from Overseas Employment and Overseas Pension Fund with Tax Concession'),
                                                   ], string='30. Exempt/ Remission income Indicator')
    gross_commission = fields.Float(compute='_get_payroll_computational_data', string='31. Gross Commission', multi="payroll_data_all")
    fromdate = fields.Date('32(a). From Date')
    todate = fields.Date('32(b). To Date')
    gross_commission_indicator = fields.Selection(selection=[('M', ' Monthly'), 
                                                             ('O', 'Other than monthly'),
                                                             ('B', 'Both')], string='33. Gross Commission Indicator')
    pension = fields.Float('34. Pension')
    entertainment_allowance = fields.Float('36. Entertainment Allowance')
    other_allowance = fields.Float('37. Other Allowance')
    gratuity_payment_amt = fields.Float('38(b)(1). Gratuity')
    compensation_loss_office = fields.Float('38(a). Compensation for loss of office')
    retirement_benifit_up = fields.Float('39. Retirement benefits accrued up to 31.12.92')
    retirement_benifit_from = fields.Float('40. Retirement benefits accrued from 1993')
    contribution_employer = fields.Float('41. Contributions made by employer to any pension / provident fund constituted outside Singapore')
    excess_voluntary_contribution_cpf_employer = fields.Float('42. Excess / voluntary contribution to CPF by employer')
    gains_profit_share_option = fields.Float('43. Gains and profits from share options for S10 (1) (b)')
    benifits_in_kinds = fields.Float('44. Value of benefits-in- kinds', help='This value must be equal to item 9 of Appendix 8A record.')
    emp_voluntary_contribution_cpf = fields.Float("45. E'yees voluntary contribution to CPF obligatory by contract of employment (overseas posting)", help='This item is not applicable with effect from Year of Assessment 2006.')
    bonus_declaration_date = fields.Date('49. Date of declaration of bonus')
    director_fee_approval_date = fields.Date('50. Date of approval of directors fees')
    fund_name = fields.Char('51. Name of fund for Retirement benefits', size=32)
    deginated_pension = fields.Char("52. Name of Designated Pension or Provident Fund for which e'yee made compulsory contribution", size=32)
    mbf = fields.Float(compute='_get_payroll_computational_data', string='12. MBF', type='float', multi="payroll_data_all", help='Contributions deducted through salaries for Mosque Building Fund.')
    donation = fields.Float(compute='_get_payroll_computational_data', string='13. Donation', type='float', multi="payroll_data_all", help='Donations deducted through salaries for Yayasan Mendaki Fund/Community Chest of Singapore/SINDA/CDAC/ECF/Other Tax Exempt donations.')
    CPF_designated_pension_provident_fund = fields.Float(compute='_get_payroll_computational_data', string='14. CPF/Designated Pension or Provident Fund', type='float', multi="payroll_data_all", help='Employee’s contribution to CPF/Designated Pension/Provident Fund (less amount refunded/to be refunded).')
    indicator_for_CPF_contributions = fields.Selection(selection=[('Y','Obligatory'), 
                                                                  ('N','Not obligatory')], string='84. Indicator for CPF contributions in respect of overseas posting which is obligatory by contract of employment', help='This item is not applicable with effect from Year of Assessment 2013, leave field blank.')
    CPF_capping_indicator = fields.Selection(selection=[('Y','Capping has been applied'), 
                                                        ('N','Capping has been not applied')], string='85. CPF capping indicator', help='This item is not applicable with effect from Year of Assessment 2013, leave field blank.')
    singapore_permanent_resident_status = fields.Selection(selection=[('Y','Singapore Permanent Resident Status is approved'),
                                                                      ('N','Singapore Permanent Resident Status is not approved')], string='86. Singapore Permanent Resident Status is approved')
    approval_has_been_obtained_CPF_board = fields.Selection(selection=[('Y',' Approval has been obtained from CPF Board to make full contribution'),
                                                                       ('N',' Approval has NOT been obtained from CPF Board to make full contribution')], string='87. Approval has been obtained from CPF Board to make full contribution')
    eyer_contibution = fields.Float('88. Employer’s Contribution')
    eyee_contibution = fields.Float('89. Employee’s Contribution')
    additional_wage = fields.Float('99. Additional wages')
    add_wage_pay_date = fields.Date('101. Date of payment for additional wages')
    refund_eyers_contribution = fields.Float('102. Amount of refund applicable to Employer contribution')
    refund_eyees_contribution = fields.Float('105. Amount of refund applicable to Employee contribution')
    refund_eyers_date = fields.Date('104. Date of refund given to employer')
    refund_eyees_date = fields.Date('107. Date of refund given to employee')
    refund_eyers_interest_contribution = fields.Float('103. Amount of refund applicable to Employer Interest on contribution')
    refund_eyees_interest_contribution = fields.Float('106. Amount of refund applicable to Employee Interest on contribution')
    insurance = fields.Float(string='Insurance', help='Life insurance Premiums deducted through salaries.')
    payslip_net_amount = fields.Float(compute='_get_payroll_computational_data', string='16. Gross Salary, Fees, Leave Pay, Wages and Overtime Pay', type='float', multi="payroll_data_all")
    bonus_amount = fields.Float(compute='_get_payroll_computational_data', string='17. Bonus', type='float', multi="payroll_data_all")
       
    #---------------------------
    #    Additional Fields
    #---------------------------
#    salary_total= fields.Integer(compute='_get_payroll_computational_data', string='16. Gross Salary, Fees, Leave Pay, Wages and Overtime Pay ', type='integer', multi="payroll_data_all")
    transport = fields.Float(compute='_get_payroll_computational_data', string='35. Transport Allowance', multi="payroll_data_all")
    notice_pay = fields.Float('38(b)(2). Notice Pay')
    ex_gratia = fields.Float('38(b)(3). Ex-Gratia')
    others = fields.Float('38(b)(4). Others')
    reason = fields.Char('38(b)(4)(a). Reason', size = 32)
    employee_income = fields.Float("22. Fixed Amount of income tax liability for which tax borne by employee", help='1. Cannot be blank if item 25 (Employee’s Income Tax borne by employer) is H.'
                                                                                                                    '\n2. Must be blank if item 25 (Employee’s Income Tax borne by employer) is F or P.')
    contribution_mandetory = fields.Selection([('Yes','Yes'),('No','No')], string="Are Contribution Mandatory?")
    contribution_amount = fields.Float("Full Amount of the contributions")
    contribution_charged = fields.Selection([('Yes','Yes'),('No','No')], string="Were contribution charged / deductions claimed by a Singapore permanent establishment?")


#    @api.constrains('director_fee_approval_date')
#    def _check_director_fee_approval_date(self):
#        for rec in self:
#            if rec.director_fee_approval_date and rec.end_date:
#                dir_year=datetime.strptime(rec.director_fee_approval_date, DEFAULT_SERVER_DATE_FORMAT).year
#                year_id=datetime.strptime(rec.end_date, DEFAULT_SERVER_DATE_FORMAT).year 
#                if dir_year >= year_id:
#                    raise ValidationError(_("\n\nWrong IR8A Configuration: (50).Date of approval of directors fees is accepted up to previous income years!"))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    address_type = fields.Selection(selection=[('L', 'Local residential address'), ('F', 'Foreign address'),
                                               ('C', 'Local C/O address'),
                                               ('N', 'Not Available')], default='L', string='Address Type',
                                    help='L = Local residential address'
                                         '\nF = Foreign address'
                                         '\nC = Local C/O address'
                                         '\nIf Address Type is L, F, C, address fields cannot be blank and vice versa. If all address fields are blank, address type must be blank.'
                                         '\nIf Address Type = L: - Formatted address and Postal Code cannot be blank'
                                         '\n- Unformatted address must be blank'
                                         '\nIf Address Type = F:'
                                         '\n- Formatted address must be blank'
                                         '\n- Unformatted address cannot be blank. Country Code cannot be 301 (Singapore), 999 (Others) and blank'
                                         '\nIf Address Type = C:'
                                         '\n- Formatted address must be blank'
                                         '\n- Unformatted address and Postal Code for Unformatted address cannot be blank.'
                                         '\nIf Address Type is blank, Address must be blank.')

    cessation_provisions = fields.Selection(selection=[('Y', 'Cessation Provisions applicable'),
                                                       ('N', 'Cessation Provisions not applicable')], default='N',
                                            string='28. Cessation Provisions',
                                            help='By default, it is Cessation Provisions not applicable.'
                                                 '\nY = Cessation Provisions applicable'
                                                 '\nCannot be blank if item 47 (Date of commencement) is before 01/01/1969 and item 48 (Date of cessation) is not blank and is within the Income Year in the Header Record.')
