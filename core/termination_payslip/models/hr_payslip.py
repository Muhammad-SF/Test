# -*- coding: utf-8 -*-

from odoo import models, api, _, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    cessation_date = fields.Date('Cessation Date', related="employee_id.cessation_date")
    emp_status = fields.Selection(
        related='employee_id.emp_status',
        string='Employment Status', help='Technical field.')
