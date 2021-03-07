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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class allocate_leave(models.TransientModel):

    _name = 'allocate.leaves'

    employee_ids = fields.Many2many('hr.employee', 'wiz_emp_rel', 'wiz_al_id',
                                    'emp_id', 'Employees')
    holiday_status_id = fields.Many2one('hr.holidays.status', 'Leave Type')
#    start_date=fields.Date("Start Date")
#    end_date=fields.Date("End Date")
    fiscal_year_id = fields.Many2one('hr.year', "Fiscal Year")
    type = fields.Selection([('add', 'Add'), ('remove', 'Remove')], 'Type',  default='add', readonly=True)
    no_of_days = fields.Float('No of Days')
    
#    @api.constrains('start_date', 'end_date')
#    def _check_start_date(self):
#        if self.start_date > self.end_date:
#            raise ValidationError(_('The start date must be anterior to the end date.'))
#        return True


    @api.onchange('holiday_status_id')
    def onchange_holiday_status(self):
        result={}
        if self.holiday_status_id and self.holiday_status_id.id:
            employees_ids = self.env['hr.employee'].search([('leave_config_id','!=',False)])
            emp_rec = []
            leave_rec = []
            if employees_ids and employees_ids.ids:
                for emp in employees_ids:
                    if emp.leave_config_id.holiday_group_config_line_ids and emp.leave_config_id.holiday_group_config_line_ids.ids:
                        for leave in emp.leave_config_id.holiday_group_config_line_ids:
                            leave_rec.append(leave.leave_type_id.id)
                            if self.holiday_status_id.id in leave_rec:
                                emp_rec.append(emp.id)
            result.update({'domain':{'employee_ids':[('id', 'in', emp_rec)]}})
        return result


    @api.multi
    def allocate_leaves(self):
        for emp in self.employee_ids:
            leave_rec = []
            if emp.leave_config_id and emp.leave_config_id.holiday_group_config_line_ids:
                for leave in emp.leave_config_id.holiday_group_config_line_ids:
                    leave_rec.append(leave.leave_type_id.id)
                if self.holiday_status_id.id in leave_rec:
                    vals = {
                        'name' : 'Assign Default ' + str(self.holiday_status_id.name2),
                        'holiday_status_id': self.holiday_status_id.id, 
                        'type': self.type,
                        'employee_id': emp.id,
                        'number_of_days_temp': self.no_of_days,
                        'state': 'confirm',
                        'holiday_type' : 'employee',
                        'hr_year_id':self.fiscal_year_id.id
#                        'start_date':self.start_date,
#                        'end_date':self.end_date,
                        }
                    self.env['hr.holidays'].create(vals)
        return True
    
