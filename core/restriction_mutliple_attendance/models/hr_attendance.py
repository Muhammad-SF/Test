# -*- coding: utf-8 -*
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, vals):
        attendance = super(HrAttendance, self).create(vals)
        if not self.env.user.company_id.allow_multiple_attendance:
            if vals.get('check_in'):
                start_date = vals.get('check_in')[:11] + '00:00:00'
                end_date = vals.get('check_in')[:11] + '23:59:59'
                total_attendance = self.search([('check_in','>=',start_date),('check_in','<=',end_date),('employee_id','=',attendance.employee_id.id)])
                if len(total_attendance) > 1:
                    raise UserError('Error!\nCan not create multiple attendance for a day.')
        return attendance

HrAttendance()