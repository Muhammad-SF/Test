# -*- coding: utf-8 -*-
import math
import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging

_logger = logging.getLogger(__name__)


class hr_holidays(models.Model):
    _inherit = 'hr.holidays'

    number_of_days_temp = fields.Float('Allocation', readonly=True, copy=False,
                                       states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, digits=(5,1))
    number_of_days = fields.Float('Number of Days', compute='_compute_number_of_days', store=True, digits=(5,1))

    @api.multi
    def _check_holiday_to_from_dates(self, start_date, end_date, employee_id):
        '''
        Checks that there is a public holiday,Saturday and Sunday on date of leave
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : The current object of id
        @param from_date: Starting date for range
        @param to_date: Ending date for range
        @return : Returns the numbers of days
        --------------------------------------------------------------------------
        '''
        dates = self.get_date_from_range(start_date, end_date)
        dates = [x.strftime(DEFAULT_SERVER_DATE_FORMAT) for x in dates]
        remove_date = []
        data = []
        half_day_data = []
        contract_ids = self.env['hr.contract'].search(
            [('employee_id', '=', employee_id), ('date_start', '<=', start_date), ('date_end', '>=', end_date)])
        for contract in contract_ids:
            if contract.working_hours and contract.working_hours.attendance_ids and contract.working_hours.schedule=='fixed_schedule':
                for hol in contract.working_hours.attendance_ids:
                    if hol.dayofweek == '0':
                        data.append(1)
                        if hol.half_day:
                            half_day_data.append(1)
                    if hol.dayofweek == '1':
                        data.append(2)
                        if hol.half_day:
                            half_day_data.append(2)
                    if hol.dayofweek == '2':
                        data.append(3)
                        if hol.half_day:
                            half_day_data.append(3)
                    if hol.dayofweek == '3':
                        data.append(4)
                        if hol.half_day:
                            half_day_data.append(4)
                    if hol.dayofweek == '4':
                        data.append(5)
                        if hol.half_day:
                            half_day_data.append(5)
                    if hol.dayofweek == '5':
                        data.append(6)
                        if hol.half_day:
                            half_day_data.append(6)
                    if hol.dayofweek == '6':
                        data.append(7)
                        if hol.half_day:
                            half_day_data.append(7)
        for day in dates:
            date = datetime.datetime.strptime(day, DEFAULT_SERVER_DATE_FORMAT).date()
            in_working_schedule = self.check_in_working_schedule(employee_id, day)
            if contract_ids and contract_ids.ids:
                if date.isoweekday() in [6,7] and not in_working_schedule:
                    remove_date.append(day)
            else:
                if date.isoweekday() in [6, 7] and not in_working_schedule:
                    remove_date.append(day)
        for remov in remove_date:
            if remov in dates:
                dates.remove(remov)
        date_f = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).date()
        calendar = date_f.isocalendar()
        public_holiday_ids = self.env['hr.holiday.public'].search([('state', '=', 'validated'),
                                                                   ('name', '=', calendar[0])])
        if public_holiday_ids and public_holiday_ids.ids:
            for public_holiday_record in public_holiday_ids:
                for holidays in public_holiday_record.holiday_line_ids:
                    if holidays.holiday_date in dates:
                        dates.remove(holidays.holiday_date)
        no_of_day = 0.0
        start_date1 = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).date().strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        end_date1 = datetime.datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT).date().strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        for day in dates:
            if day >= start_date1 and day <= end_date1:
                # Consider date if its available in Working Schedule Calendar table
                inside_working_schedule = self.check_in_working_schedule(employee_id, day)
                if inside_working_schedule:
                    half_day_date = datetime.datetime.strptime(day, DEFAULT_SERVER_DATE_FORMAT).date()
                    if half_day_date.isoweekday() in half_day_data:
                        no_of_day += 0.5
                    else:
                        no_of_day += 1
                else:
                    no_of_day += 1
        return no_of_day


    def check_in_working_schedule(self, employee_id, day):
        query_working_schedule = _(
            "select * from employee_working_schedule_calendar where employee_id=%s and date_start::timestamp::date='%s'") % (
                                 str(employee_id), str(day))
        self._cr.execute(query_working_schedule)
        vals = self._cr.fetchall()
        if vals:
            return True
        else:
            return False

    @api.onchange('half_day', 'date_from', 'date_to', 'holiday_status_id', 'employee_id')
    def onchange_date_from(self, date_from=False, date_to=False, half_day=False, holiday_status_id=False,
                           employee_id=False):
        '''
        when you change from date, this method will set
        leave type and numbers of leave days accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        ------------------------------------------------------
        @return: Dictionary of values.
        '''
        for rec in self:
            result = {'value': {}}

            if date_from == False:
                date_from = self.date_from
            if date_to == False:
                date_to = self.date_to
            if holiday_status_id == False:
                holiday_status_id = self.holiday_status_id.id
            if employee_id == False:
                employee_id = self.employee_id.id
            if half_day == False:
                half_day == False
            else:
                half_day = self.half_day
            leave_day_count = False
            if holiday_status_id and holiday_status_id != False:
                leave_day_count = self.env['hr.holidays.status'].browse(holiday_status_id).count_days_by
            if (date_from and date_to) and (date_from > date_to) and half_day == False:
                #raise UserError(_('Warning!\nThe start date must be anterior to the end date.'))
                date_to_with_delta = datetime.datetime.strptime(date_from,
                                                                DEFAULT_SERVER_DATE_FORMAT) + datetime.timedelta(
                    hours=8)
                result['value']['date_to'] = str(date_to_with_delta)
            elif (date_from and date_to) and half_day == True:
                date_to = date_from
            if date_from and not date_to:
                date_to_with_delta = datetime.datetime.strptime(date_from,
                                                                DEFAULT_SERVER_DATE_FORMAT) + datetime.timedelta(
                    hours=8)
                result['value']['date_to'] = str(date_to_with_delta)
            if (date_to and date_from) and (date_from <= date_to):
                if leave_day_count != False and leave_day_count == 'working_days_only':
                    diff_day = self._check_holiday_to_from_dates(date_from, date_to, employee_id)
                    #result['value']['number_of_days_temp'] = round(math.floor(diff_day))
                    result['value']['number_of_days_temp'] = float(diff_day)
                    _logger.info(">>>>>>>>>>>>>>>>>>>>> %s" % str(result['value']['number_of_days_temp']))
                else:
                    diff_day = self._get_number_of_daystmp(date_from, date_to)
                    result['value']['number_of_days_temp'] = round(math.floor(diff_day)) + 1
            else:
                result['value']['number_of_days_temp'] = 0
            if date_from and date_to and half_day == True:
                date_to_with_delta = datetime.datetime.strptime(date_from,
                                                                DEFAULT_SERVER_DATE_FORMAT) + datetime.timedelta(
                    hours=4)
                result['value']['date_to'] = str(date_to_with_delta)
            if half_day == True:
                result['value']['number_of_days_temp'] = 0.5
            if self.date_from:
                self.hr_year_id = self.fetch_hryear(date_from)
            if rec.holiday_status_id:
                rec.holiday_status_id.write({'hr_year_id': self.fetch_hryear(date_from)})
            return result

    @api.onchange('half_day', 'date_from', 'date_to', 'holiday_status_id', 'employee_id')
    def onchange_date_to(self, date_from=False, date_to=False, half_day=False, holiday_status_id=False,
                         employee_id=False):
        '''
        when you change to date, this method will set
        leave type and numbers of leave days accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        ------------------------------------------------------
        @return: Dictionary of values.
        '''
        if date_from == False:
            date_from = self.date_from
        if date_to == False:
            date_to = self.date_to
        if holiday_status_id == False:
            holiday_status_id = self.holiday_status_id.id
        if employee_id == False:
            employee_id = self.employee_id.id
        if half_day == False:
            half_day == False
        else:
            half_day = self.half_day
        leave_day_count = False
        if holiday_status_id and holiday_status_id != False:
            leave_day_count = self.env['hr.holidays.status'].browse(holiday_status_id).count_days_by
        result = {'value': {}}
        if (date_to and date_from) and (date_from <= date_to):
            if leave_day_count != False and leave_day_count == 'working_days_only':
                diff_day = self._check_holiday_to_from_dates(date_from, date_to, employee_id)
                #result['value']['number_of_days_temp'] = round(math.floor(diff_day))
                #result['value']['number_of_days_temp'] = diff_day
                result['value']['number_of_days_temp'] = float(diff_day)
                _logger.info(">>>>>>>>>>>>>>>>>>>>> %s" % str(result['value']['number_of_days_temp']))
            else:
                diff_day = self._get_number_of_daystmp(date_from, date_to)
                result['value']['number_of_days_temp'] = round(math.floor(diff_day)) + 1
        else:
            result['value']['number_of_days_temp'] = 0
        if half_day == True:
            result['value']['number_of_days_temp'] = 0.5
        return result
