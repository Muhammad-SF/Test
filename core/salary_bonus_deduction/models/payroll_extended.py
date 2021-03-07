from odoo import models, fields

class hr_payslip(models.Model):
    _inherit= 'hr.payslip'

    bonus_amount = fields.Integer('Bonus')
    deduction_amount = fields.Integer('Deduction')

hr_payslip()