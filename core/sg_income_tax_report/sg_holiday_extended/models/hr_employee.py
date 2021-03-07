# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import time
import datetime
from datetime import date
from odoo import fields, api, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class hr_employee(models.Model):

    _inherit="hr.employee"

    dependent_ids = fields.One2many('dependents', 'employee_id', 'Dependents')
    leave_config_id = fields.Many2one('holiday.group.config','Leave Structure',help="Structure of Leaves")
    depends_singaporean = fields.Boolean('Depends are Singaporean',help='Checked if depends are Singaporean')
    leave_all_bool = fields.Boolean('For Invisible Allocate Leave Button')

    @api.multi
    def allocate_leaves_mannualy(self):
        '''
        This Allocate Leaves button method will assign annual leaves from 
        employee form view.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param context : Standard Dictionary
        @return: Return the True
        ----------------------------------------------------------
        '''
        holiday_obj = self.env['hr.holidays']
        date_today = datetime.datetime.today()
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = datetime.datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).year
        curr_year_date = str(date_today.year) + '-01-01'
        curr_year_date = datetime.datetime.strptime(curr_year_date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
        curr_hr_year_id = holiday_obj.fetch_hryear(today)
        emp_leave_ids = []
        for employee in self:
            if employee.leave_config_id.holiday_group_config_line_ids and employee.leave_config_id.holiday_group_config_line_ids.ids:
#                for leave in employee.leave_config_id.holiday_group_config_line_ids:
#                    emp_leave_ids.append(leave.leave_type_id.id)
                if employee.leave_config_id.holiday_group_config_line_ids:
                    for holiday in employee.leave_config_id.holiday_group_config_line_ids:
                        tot_allocation_leave = holiday.default_leave_allocation
                        if tot_allocation_leave == 0.0:
                            continue
                        if employee.user_id and employee.user_id.id == 1:
                            continue
                        add = 0.0
                        self.env.cr.execute("SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='add' and hr_year_id=%d" % (employee.id, holiday.leave_type_id.id, curr_hr_year_id))
                        all_datas = self.env.cr.fetchone()
                        if all_datas and all_datas[0]:
                            add += all_datas[0]
                        if add > 0.0:
                            continue
                        if holiday.leave_type_id.name == 'AL' and employee.join_date > curr_year_date:
                            join_month = datetime.datetime.strptime(employee.join_date, DEFAULT_SERVER_DATE_FORMAT).month
                            remaining_months = 12 - int(join_month)
                            if remaining_months:
                                tot_allocation_leave = (float(tot_allocation_leave) /12) * remaining_months
                                tot_allocation_leave = round(tot_allocation_leave)
                        if holiday.leave_type_id.name in ['PL','SPL'] and employee.gender != 'male':
                            continue
                        if holiday.leave_type_id.name == 'PCL' and employee.singaporean != True:
                            continue
                        if employee.leave_config_id.holiday_group_config_line_ids and employee.leave_config_id.holiday_group_config_line_ids.ids:
                            for leave in employee.leave_config_id.holiday_group_config_line_ids:
                                emp_leave_ids.append(leave.leave_type_id.id)
                            if employee.leave_config_id.holiday_group_config_line_ids:
                                if holiday.leave_type_id.name == 'AL' and employee.join_date < curr_year_date:
                                    join_year = datetime.datetime.strptime(employee.join_date, DEFAULT_SERVER_DATE_FORMAT).year
                                    tot_year = year - join_year
                                    if holiday.incr_leave_per_year != 0 and tot_year != 0:
                                        tot_allocation_leave += (holiday.incr_leave_per_year * tot_year)
                                if holiday.max_leave_kept != 0 and tot_allocation_leave > holiday.max_leave_kept:
                                    tot_allocation_leave = holiday.max_leave_kept
                                leave_dict = {
                                    'name' : 'Assign Default ' + str(holiday.leave_type_id.name2),
                                    'employee_id': employee.id,
                                    'holiday_type' : 'employee',
                                    'holiday_status_id' : holiday.leave_type_id.id,
                                    'number_of_days_temp' :tot_allocation_leave,
                                    'hr_year_id' : curr_hr_year_id,
                                    'type' : 'add',
                                    }
                                leave_id = holiday_obj.create(leave_dict)
                    employee.write({'leave_all_bool':True})
        return True


    @api.model
    def cessation_date_deadline(self):
        today =  date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
        employee_ids = self.search([('cessation_date', '<' ,today),('emp_status','in',['terminated','in_notice'])])
        if employee_ids and employee_ids.ids:
            employee_ids.write({'emp_status': 'inactive'})
        return True


class dependents(models.Model):

    _name = 'dependents'

    employee_id =fields.Many2one('hr.employee', 'Employee ID')
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    birth_date = fields.Date('Birth Date')
    relation_ship = fields.Selection([('son', 'Son'),('daughter', 'Daughter'), ('father', 'Father') , ('mother', 'Mother')], string='Relationship')
    email = fields.Char('Email')
    identification_number = fields.Integer('Identification Number')
    contact_number = fields.Integer('Contact Number')


class resource_calendar_attendance(models.Model):

    _inherit = 'resource.calendar.attendance'

    half_day =  fields.Boolean('Half Day')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: