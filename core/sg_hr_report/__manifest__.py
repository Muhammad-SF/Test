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

{
    "name": "Singapore HR Reports",
    "version": "1.1.1",
    "depends": ["l10n_sg_hr_payroll"],
    "author" :"Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    "category": "Human Resources",
    "description": """
Singapore Payroll Salary Rules.
============================

    -Configuration of hr_payroll for Singapore localization
    -All main contributions rules for Singapore payslip.
    * New payslip report
    * Employee Contracts
    * Allow to configure Basic / Gross / Net Salary
    * CPF for Employee and Employer salary rules
    * Employee and Employer Contribution Registers
    * Employee PaySlip
    * Allowance / Deduction
    * Integrated with Holiday Management
    * Medical Allowance, Travel Allowance, Child Allowance, ...
    
    - Payroll Advice and Report
    - Yearly Salary by Head and Yearly Salary by Employee Report
    - IR8A and IR8S esubmission txt file reports
    """,
    'data': [
#       'security/ir.model.access.csv',
       'views/payslip_report.xml',
       'views/payslip_voucher_template.xml',
       'views/hr_bank_summary_template.xml',
       'views/cheque_summary_report_temp.xml',
       'views/payment_advice_report_template.xml',
       'views/hr_payroll_summary_temp.xml',
       'views/sg_hr_report_menu.xml',
       'wizard/upload_xls_wizard_view.xml',
       'wizard/payroll_summary_wizard_view.xml',
       'wizard/cpf_payment_wizard_view.xml',
       'wizard/bank_summary_wizard_view.xml',
       'wizard/cheque_summary_report_view.xml',
#       'wizard/ocbc_bank_specification_view.xml',
       "wizard/export_employee_summary_wiz_view.xml",
#       'wizard/cimb_bank_text_file_view.xml',
       'wizard/cpf_rule_text_file_view.xml',
       'wizard/payroll_generic_summary_wiz.xml'
    ],
    'installable': True,
    'auto_install':False,
    'application':True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
