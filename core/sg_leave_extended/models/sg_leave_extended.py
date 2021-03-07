import datetime
import time
from datetime import date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class hr_holidays_status(models.Model):
    _inherit = "holiday.group.config"
    
    status_history_ids = fields.One2many('hr.leave.history', 'history_id', 'Holiday Status History')
    
class holiday_group_config_line(models.Model):
    _inherit = 'holiday.group.config.line'

    @api.constrains('increment_count','increment_number')
    def _check_increment_count(self):
        """
            This Method is restrict the system that not configure negative 
            values for Interval Number and  Number of Calls.
        """
        if self._context is None:
            self._context = {}
        for rec in self:
            if rec.increment_count < 0 or rec.increment_number < 0:
                raise ValidationError(_('Please set Interval Number or Number of Calls properly.!'))

    increment_count = fields.Integer('Interval Number',help="Repeat every x.")
    status_history_ids = fields.One2many('hr.leave.history', 'history_id', 'Holiday Status History')
    increment_number = fields.Integer('Number of Calls', help='How many times the allocation is schedule.')
    execution_date =fields.Date("Execution Date", help="A start date from where the leave allocation is schedule.", default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT))
    last_execution_date = fields.Date("Last Execution Date", help="Last date from where the leave allocation is stable.")
    inc_leave_per_freq = fields.Integer("Increment Leave Per Frequency", help='Increase Number of leave for every Interval Unit.')
    last_increment_number = fields.Integer('Last Interval Number',
                                             help="Last leave amount from where the leave allocation is stable.")
    increment_frequency = fields.Selection([('month','Month'),('year','Year')], string="Interval Unit",
                                             help='Unit of Interval.', default="year")

    @api.multi
    def validate_leaves(self):
        """
            This Method is used to create Leave History on a
            Given leave allocation Configurations.
        """
        if not self._context:
            self._context= {}
        job_history_obj = self.env['hr.leave.history']
        status_obj = self.env["hr.leave.history"]
        for leave_rec in self:
            if leave_rec.execution_date:
                curr_date = datetime.datetime.strptime(leave_rec.execution_date, DEFAULT_SERVER_DATE_FORMAT)
            else:
                raise ValidationError('Please Configure Execution Date.')
            default_leave = leave_rec.default_leave_allocation
            if leave_rec.status_history_ids and leave_rec.status_history_ids.ids:
                leave_rec.status_history_ids.unlink()
            for incr in range(leave_rec.increment_number + 1):
                if leave_rec.increment_frequency == 'year':
                    if incr == 0:
                        history_detail = {
                                 'increment_count':leave_rec.increment_count,
                                 'increment_number':default_leave,
                                 'history_id':leave_rec.id,
                                 'start_date':curr_date,
                                 }
                        leave_detail = job_history_obj.create(history_detail)
                    else:
                        default_leave = leave_rec.default_leave_allocation + (incr * leave_rec.inc_leave_per_freq)
                        curr_date = curr_date + relativedelta(years=leave_rec.increment_count)
                        history_detail = {
                                 'increment_count':leave_rec.increment_count,
                                 'increment_number':default_leave,
                                 'history_id':leave_rec.id,
                                 'start_date':curr_date,
                                 }
                        leave_detail = job_history_obj.create(history_detail)
                if leave_rec.increment_frequency == 'month':
                    if incr==0:
                        history_detail = {
                                 'increment_count':leave_rec.increment_count,
                                 'increment_number':leave_rec.default_leave_allocation,
                                 'history_id':leave_rec.id,
                                 'start_date':curr_date,
                                 }
                        leave_detail = job_history_obj.create(history_detail)
                    else:
                        default_leave = leave_rec.default_leave_allocation + (incr * leave_rec.inc_leave_per_freq)
                        curr_date = curr_date + relativedelta(months=leave_rec.increment_count)
                        history_detail = {
                                 'increment_count':leave_rec.increment_count,
                                 'increment_number':default_leave,
                                 'history_id':leave_rec.id,
                                 'start_date':curr_date,
                                 }
                        leave_detail = job_history_obj.create(history_detail)
            leave_rec.write({'last_execution_date':curr_date,
                              'last_increment_number':default_leave,
                          })
        return True


class hr_leave_history(models.Model):
    _name='hr.leave.history'
    
    @api.constrains('start_date')
    def _check_leave_history_date(self):
        for leave_status in self:
            domain = [('start_date','=',leave_status.start_date)]
            nholidays = self.search_count(domain)
            if nholidays > 1:
                raise ValidationError('You can not generate same holiday status history for leave type "%s".'%(leave_status.history_id.leave_type_id.name2))
        return True

    history_id = fields.Many2one('holiday.group.config.line', 'History')
    start_date = fields.Date("Date", help="Start Date Of leave History.")
    increment_count = fields.Integer("Increment Count", help="Number of allocation leaves.")
    increment_number = fields.Integer("Increment Leave", help="Total number of allocation leaves.")
    done_bol = fields.Boolean("Complete", help="It's True when allocation is completed on given date.")


class hr_holidays(models.Model):

    _inherit = "hr.holidays"

    @api.model
    def assign_annual_other_leaves(self):
        '''
        This method will be called by scheduler which will assign 
        Annual Marriage,Compassionate,Infant care,Child care,
        Extended child care,Paternity leaves at end of the year.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param context : Standard Dictionary
        @return: Return the True
        ----------------------------------------------------------
        '''
        emp_obj = self.env['hr.employee']
        holiday_status_obj = self.env['hr.holidays.status']
        date_today = datetime.datetime.today()
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = datetime.datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).year
        month = datetime.datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).month
        curr_year_date = str(date_today.year) + '-01-01'
        curr_year_date = datetime.datetime.strptime(curr_year_date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
        curr_hr_year_id = self.fetch_hryear(today)
#        all_aloc_leaves = ['MLC','ML','CLO','CL','UICL','CCL','ECL','PL','AL','SPL','PCL','ML16','ML15','ML8','ML4','MOL','HOL']
        all_leave_ids = holiday_status_obj.search([('active','=', True),('default_leave_allocation','>',0)
                                                            ])

        empl_ids = emp_obj.search([('active','=', True),('leave_config_id','!=', False)
                                            ])

#        for holiday in all_leave_ids:
        for employee in empl_ids:
            if employee.leave_config_id.holiday_group_config_line_ids:
                for holiday in employee.leave_config_id.holiday_group_config_line_ids:
                    tot_allocation_leave = holiday.default_leave_allocation
                    if employee.user_id and employee.user_id.id == 1:
                        continue
                    add = 0.0
                    self._cr.execute("SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='add' and hr_year_id=%d" % (employee.id, holiday.leave_type_id.id, curr_hr_year_id))
                    all_datas = self._cr.fetchone()
                    if all_datas and all_datas[0]:
                        add += all_datas[0]
                    if add > 0.0:
                        continue
#                    if holiday.leave_type_id.name == 'AL' and employee.join_date > curr_year_date:
#                        join_month = datetime.datetime.strptime(employee.join_date, DEFAULT_SERVER_DATE_FORMAT).month
#                        remaining_months = 12 - int(join_month)
#                        if remaining_months:
#                            tot_allocation_leave = (float(tot_allocation_leave) /12) * remaining_months
#                            tot_allocation_leave = round(tot_allocation_leave)
                    if holiday.leave_type_id.name in ['PL','SPL'] and employee.gender != 'male':
                        continue
                    if holiday.leave_type_id.name == 'PCL' and employee.singaporean != True:
                        continue
                    if holiday.status_history_ids and holiday.status_history_ids.ids:
                        for holiday_status in holiday.status_history_ids:
                            if today == holiday_status.start_date and holiday_status.done_bol == False:
                                tot_allocation_leave = (holiday_status.increment_number)
                                leave_dict = {
                                    'name' : 'Assign Default ' + str(holiday.leave_type_id.name2),
                                    'employee_id': employee.id,
                                    'holiday_type' : 'employee',
                                    'holiday_status_id' : holiday.leave_type_id.id,
                                    'number_of_days_temp' :tot_allocation_leave,
                                    'type' : 'add',
                                    'hr_year_id' : curr_hr_year_id,
                                    }
                                leave_id = self.create(leave_dict)
                                holiday_status.write({'done_bol':True})
                    else:
                        leave_dict = {
                                    'name' : 'Assign Default ' + str(holiday.leave_type_id.name2),
                                    'employee_id': employee.id,
                                    'holiday_type' : 'employee',
                                    'holiday_status_id' : holiday.leave_type_id.id,
                                    'number_of_days_temp' :tot_allocation_leave,
                                    'type' : 'add',
                                    'hr_year_id' : curr_hr_year_id,
                                    }
                        leave_id = self.create(leave_dict)
        return True
