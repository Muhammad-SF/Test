# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from odoo.exceptions import Warning
_logger = logging.getLogger(__name__)


class StudentPayslip(models.Model):
    _inherit = 'student.payslip'

    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('pending', 'Pending'), ('paid', 'Paid'), ('cancel', 'Cancelled')],
                             'State', readonly=True, default='draft')

    @api.multi
    def cancel_state(self):
        if self.state != 'draft':
            raise Warning(_('You can cancel payslip only in draft'))
        self.state = 'cancel'

class StudentStudent(models.Model):
    ''' Defining School Information '''
    _inherit = 'student.student'


    @api.multi
    def reset_to_draft(self):
        payslip_ids = self.env['student.payslip'].search([('student_id','=',self.id)])
        self.state = 'draft'
        for payslip in payslip_ids:
            for line in payslip.line_ids:
                if line.type in ['enrollment_fee', 'month'] and payslip.state == 'draft':
                    payslip.state = 'cancel'
        # self.history_ids.unlink()