# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
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
import time
import datetime
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError


class hr_holidays(models.Model):
    _inherit = 'hr.holidays'

    @api.constrains('date_from','date_to')
    def _check_date(self):
        '''
        The method used to Validate leave request on same day.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        @return : True or False
        ------------------------------------------------------
        '''
        for holiday in self:
            domain = [
                ('date_from', '<=', holiday.date_to),
                ('date_to', '>=', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse']),
                ('holiday_status_id.name', '!=', 'MOL'),
                ('leave_expire', '=', False),
            ]
            nholidays = self.search(domain)
            if nholidays and nholidays.ids:
                if holiday.half_day == True and holiday.type == 'remove':
                    for new_holiday in nholidays:
                        if new_holiday.half_day == True:
                            if new_holiday.am_or_pm == holiday.am_or_pm:
                                raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))
                        else:
                            raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))
                else:
                    raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))
            if holiday.date_to and holiday.date_from:
                year_to = datetime.datetime.strptime(holiday.date_to, DEFAULT_SERVER_DATE_FORMAT).year
                year_from = datetime.datetime.strptime(holiday.date_from, DEFAULT_SERVER_DATE_FORMAT).year
                if year_from!=year_to:
                    raise ValidationError(_('Leave date from year and Leave date to year should be same!'))

    @api.multi
    def expire_annual_leave_allocation(self):
        '''
        This method will be called by scheduler which will extra annual leave expire and 
        current year of annual leave approved on end of the year i.e YYYY/04/01 00:00:00.
        @self : Object Pointer
        @cr : Database Cursor
        @uid : Current User Id
        @context : Standard Dictionary
        @return: Return the True
        --------------------------------------------------------------------------
        '''
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        current_year = datetime.datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).year
        current_hr_year_id = self.fetch_hryear(today)
        current_start_date = str(current_year) + '-01-01' or ''
        carry_end_date1 = str(current_year) + '-04-01' or ''
        carry_start_date = str(current_year - 1) + '-04-01' or ''
        carry_end_date = str(current_year) + '-03-31' or ''
        carry_forward_end_date = ' '

        user_brw = self.env['res.users'].browse(self._uid)
        if user_brw and user_brw.id and user_brw.company_id and user_brw.company_id.carry_forward_end_date:
            carry_forward_end_date = user_brw.company_id.carry_forward_end_date
            if carry_forward_end_date:
                carry_f_end_date = datetime.datetime.strptime(carry_forward_end_date, DEFAULT_SERVER_DATE_FORMAT)
                carry_end_date12 = carry_f_end_date + relativedelta(days=1)
                carry_end_date1 = carry_end_date12.strftime(DEFAULT_SERVER_DATE_FORMAT)
                end_day = carry_f_end_date.day
                carry_end_date = carry_f_end_date + relativedelta(year=current_year)
                carry_start_date = carry_f_end_date + relativedelta(year=current_year - 1, days=1)
                carry_end_date = carry_end_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                carry_f_end_date1 = carry_end_date + ' 08:00:00'
                carry_f_end_date1 = datetime.datetime.strptime(carry_f_end_date1, DEFAULT_SERVER_DATETIME_FORMAT)
                carry_start_date = carry_start_date.date().strftime(DEFAULT_SERVER_DATE_FORMAT)

        empl_ids = self.env['hr.employee'].search([('active', '=', True), ('leave_config_id', '!=', False)])
#        for employee in emp_obj.browse(empl_ids):
        for employee in empl_ids:
            holiday_status_ids = []
            if employee.leave_config_id and employee.leave_config_id.holiday_group_config_line_ids and employee.leave_config_id.holiday_group_config_line_ids.ids:
                for leave_type in employee.leave_config_id.holiday_group_config_line_ids:
                    if leave_type.carryover and leave_type.carryover in ('up_to', 'unlimited'):
                        holiday_status_ids.append(leave_type.leave_type_id.id)
            for holiday_status_rec in self.env['hr.holidays.status'].browse(holiday_status_ids):
######                if employee.user_id and employee.user_id.id == 1:
######                    continue

                holiday_ids = self.search([('employee_id', '=', employee.id), ('state', '=', 'validate'),
                                           ('holiday_status_id', '=', holiday_status_rec.id),
                                           ('type', '=', 'add'),('hr_year_id', '=', current_hr_year_id),
                                           ],
                                          )
                add_number_of_days = crf_number_of_days = 0.0
                for holiday_rec in holiday_ids:
                    add_number_of_days = holiday_rec and holiday_rec.number_of_days_temp or 0.0

                crf_holiday_ids = self.search([('employee_id', '=', employee.id), ('state', '=', 'validate'),
                                               ('holiday_status_id', '=', holiday_status_rec.id),
                                               ('type', '=', 'add'), ('carry_forward', '=', True),
                                               ('hr_year_id', '=', current_hr_year_id),
                                               ]
                                              )
                if crf_holiday_ids:
                    for holiday_crf_rec in crf_holiday_ids:
                        crf_number_of_days = holiday_crf_rec and holiday_crf_rec.number_of_days_temp or 0.0

                total_add_number_of_days = add_number_of_days + crf_number_of_days

                #===============================================================
                # Remove Type Leaves
                #===============================================================

                rmv_number_of_days = prtl_rmv_number_of_days = 0.0
                rmv_holiday_ids = self.search([('employee_id', '=', employee.id),('type', '=', 'remove'),
                                               ('holiday_status_id', '=', holiday_status_rec.id),
                                               ('state', '=', 'validate'),
                                               ('hr_year_id', '=', current_hr_year_id),
                                               ('date_from', '>=', current_start_date),
                                               ('date_to', '<=', carry_end_date),
                                               ]
                                              )
                if rmv_holiday_ids:
                    for holiday_rmv_rec in rmv_holiday_ids:
                        rmv_number_of_days = holiday_rmv_rec and holiday_rmv_rec.number_of_days_temp or 0.0
                rmv_prtl_holiday_ids = self.search([('employee_id', '=', employee.id),('type', '=', 'remove'),
                                                    ('holiday_status_id', '=', holiday_status_rec.id),
                                                    ('state', '=', 'validate'),
                                                    ('hr_year_id', '=', current_hr_year_id),
                                                    ('date_from', '<=', carry_end_date),
                                                    ('date_to', '>=', carry_end_date),
                                                    ]
                                                   )
                if rmv_prtl_holiday_ids:
                    for holiday_prtl_rmv_rec in rmv_prtl_holiday_ids:
                        total_amount = holiday_prtl_rmv_rec.number_of_days_temp
                        carry_f_end_date2 = carry_f_end_date1 + relativedelta(days=1)
                        carry_f_end_date2 = carry_f_end_date2.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        carry_f_end_date1 = carry_f_end_date1.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        total_amount_before = self._check_holiday_to_from_dates(holiday_prtl_rmv_rec.id, holiday_prtl_rmv_rec.date_from, carry_f_end_date1, holiday_prtl_rmv_rec.leave_company_id.id)
                        if total_amount_before == holiday_prtl_rmv_rec.number_of_days_temp:
                            holiday_prtl_rmv_rec.write({'leave_expire': True})
                        elif total_amount_before < holiday_prtl_rmv_rec.number_of_days_temp:
                            total_amount_days = total_amount - total_amount_before
                            leave_dict = {'name' : holiday_prtl_rmv_rec.name or False,
                                          'employee_id': employee.id,
                                          'holiday_type' : 'employee',
                                          'holiday_status_id' : holiday_status_rec.id,
                                          'number_of_days_temp' : total_amount_days or 0.0,
                                          'type' : 'remove',
                                          'hr_year_id' : current_hr_year_id or False,
                                          'state':'validate',
                                          'date_from':carry_f_end_date2,
                                          'date_to':holiday_prtl_rmv_rec.date_to,
                                          'leave_config_id':holiday_prtl_rmv_rec.leave_config_id.id or False,
                                          'leave_expire': False,
                                          }
                            holiday_prtl_rmv_rec.write({'state':'validate', 'leave_expire': True})
                            new_holiday_create = self.create(leave_dict)
                            new_holiday_create.action_approve()

                exp_holiday_ids = []
                if crf_holiday_ids and crf_holiday_ids.ids:
                    exp_holiday_ids += crf_holiday_ids.ids
                if rmv_holiday_ids and rmv_holiday_ids.ids:
                    exp_holiday_ids += rmv_holiday_ids.ids
                if len(exp_holiday_ids) > 0:
                    exp_holiday_ids = list(set(exp_holiday_ids))
                    for last_holiday_brw in self.browse(exp_holiday_ids):
                        last_holiday_brw.write({'leave_expire': True})
        return True


class hr_holidays_status(models.Model):
    _inherit = "hr.holidays.status"
    _rec_name='name2'
    _order='name2'

    @api.multi
    def get_days(self, employee_id):
#         for self in self:
        status = self.browse(self.ids)
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = self.env['hr.holidays'].fetch_hryear(today)
        # need to use `dict` constructor to create a dict per id
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        hr_year_id = self.env['hr.holidays'].fetch_hryear(today)
        result = dict((id, dict(max_leaves=0, leaves_taken=0, remaining_leaves=0,
                                virtual_remaining_leaves=0)) for id in self.ids)
        holidays = self.env['hr.holidays'].search([('employee_id', '=', employee_id),
                                                   ('state', 'in', ['confirm', 'validate1', 'validate']),
                                                   ('holiday_status_id', 'in', self.ids),
#                                                    ('leave_expire', '!=', True),
                                                   ('hr_year_id','=',year),
                                                   ])
        for holiday in holidays:
            status_dict = result[holiday.holiday_status_id.id]
            if holiday.type == 'add':
                if holiday.state == 'validate':
                    status_dict['virtual_remaining_leaves'] += holiday.number_of_days_temp
                    status_dict['max_leaves'] += holiday.number_of_days_temp
                    status_dict['remaining_leaves'] += holiday.number_of_days_temp
            elif holiday.type == 'remove':  # number of days is negative
                status_dict['virtual_remaining_leaves'] -= holiday.number_of_days_temp
                if holiday.state == 'validate':
                    status_dict['leaves_taken'] += holiday.number_of_days_temp
                    status_dict['remaining_leaves'] -= holiday.number_of_days_temp
        return result


class res_company(models.Model):
    _inherit = 'res.company'
    
    carry_forward_end_date = fields.Date('Carry Forwrd End Date')

