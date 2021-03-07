from odoo import api, fields, models, _
import datetime
from datetime import datetime
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import pytz
import logging
_logger = logging.getLogger(__name__)


class PublicHolidaysLine(models.Model):
    _inherit = 'hr.holiday.lines'

    @api.multi
    def remove_all_current_holiday(self):
        current_calendar = self.env['employee.working.schedule.calendar'].search([('holiday_line_id', 'in', self.ids)])
        if current_calendar:
            current_calendar.unlink()

    @api.model
    def create(self, value):
        holidays = super(PublicHolidaysLine, self).create(value)
        holidays.public_holiday_working_calendar()
        return holidays

    @api.multi
    def write(self, values):
        holidays = super(PublicHolidaysLine, self).write(values)
        self.remove_all_current_holiday()
        self.public_holiday_working_calendar()
        return holidays

    @api.multi
    def public_holiday_working_calendar(self):
        for line in self:
            if line.holiday_date:
                date_start = datetime.strptime(line.holiday_date + " 08:00:00", "%Y-%m-%d %H:%M:%S")
                date_end = datetime.strptime(line.holiday_date + " 17:59:59", "%Y-%m-%d %H:%M:%S")
                user_pool = line.env['res.users']
                user = user_pool.browse(line.env.uid)
                tz = pytz.timezone(user.partner_id.tz or 'Asia/Jakarta') or pytz.utc
                date_start = tz.localize(
                    datetime.strptime(date_start.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')).astimezone(
                    pytz.utc)
                date_end = tz.localize(
                    datetime.strptime(date_end.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')).astimezone(
                    pytz.utc)
                schedule_values = {
                    'name': "Public Holidays",
                    'date_start': date_start,
                    'holiday_line_id': line.id,
                    'date_end': date_end,
                    'is_holiday' : True
                }
                res = line.env['employee.working.schedule.calendar'].create(schedule_values)


class EmployeeWorkingScheduleCalendar(models.Model):
    _name = 'employee.working.schedule.calendar'
    _description = "Calendar to display employees working schedule"
    _order = 'employee_id'

    WEEKDAYS = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ]
    
    name = fields.Char(string='Name', size=256, required=0, compute='_compute_name')
    is_holiday = fields.Boolean(default=False)
    holiday_line_id = fields.Many2one('hr.holiday.lines', ondelete="cascade")
    allday = fields.Boolean(default=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=0)
    contract_id = fields.Many2one('hr.contract', string="Contract", required=0)
    date_start = fields.Datetime(string='Working Start Date & Time')
    date_end = fields.Datetime(string='Working End Date & Time')
    hour_from = fields.Float(string='Work Hours From', required=0)
    hour_to = fields.Float(string='Work Hours To', required=0)
    dayofweek = fields.Selection(WEEKDAYS, string='Day', required=0)
    working_hours = fields.Many2one('resource.calendar', string='Working Schedule')
    department_id = fields.Many2one('hr.department', string='Department')
    active = fields.Boolean('Active', default=True)
    schedule = fields.Selection([
        ('fixed_schedule', 'Fixed Schedule'),
        ('shift_pattern', 'Shift Pattern'), ], string='Schedule')
    checkin = fields.Datetime('Check In', compute='get_checkin_and_checkout')
    checkout = fields.Datetime('Check Out', compute='get_checkin_and_checkout')
    total_working_time = fields.Char('Total Working Time', compute='_total_hours')
    break_from = fields.Float('Break From', compute='get_break_from_and_to')
    break_to = fields.Float('Break To', compute='get_break_from_and_to')
    state = fields.Selection(string="Status", compute='_compute_attendance_state', selection=[('checked_in', "Checked In"), ('not_checked_in', "Not Checked in")])
    

    def _compute_attendance_state(self):
        for rec in self:
            if rec.checkin:
                rec.state = 'checked_in'
            if not rec.checkin:
                rec.state = 'not_checked_in'


    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = domain or []
        domain = domain + ["|", ('is_holiday', '=', True), ('employee_id.company_id.id', '=', self.env.user.company_id.id)]
        res = super(EmployeeWorkingScheduleCalendar, self).search_read(domain=domain, fields=fields, offset=offset,
                                                   limit=limit, order=order)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = domain or []
        domain = domain + ["|", ('is_holiday', '=', True),
                           ('employee_id.company_id.id', '=', self.env.user.company_id.id)]
        res = super(EmployeeWorkingScheduleCalendar, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                                  lazy=lazy)
        return res

    @api.multi
    @api.depends('date_start', 'date_end')
    def _compute_name(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                user_pool = self.env['res.users']
                user = user_pool.browse(self.env.uid)
                tz = pytz.timezone(user.partner_id.tz or 'Asia/Jakarta') or pytz.utc
                date_start = pytz.utc.localize(
                    datetime.strptime(rec.date_start, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                date_end = pytz.utc.localize(
                    datetime.strptime(rec.date_end, '%Y-%m-%d %H:%M:%S')).astimezone(tz)
                rec.name = date_start.strftime("%H:%M") + ' - ' + date_end.strftime("%H:%M")
                if rec.is_holiday:
                    rec.name = 'Public Holidays: ' + (rec.holiday_line_id and rec.holiday_line_id.name or '')

    def get_checkin_and_checkout(self):
        attendance = self.env['hr.attendance']
        for rec in self:
            for att in attendance.search([('employee_id', '=', rec.employee_id.id)]):
                if rec.date_start[:10] == att.check_in[:10]:
                    # dt_check_in = datetime.strptime(att.check_in,'%Y-%m-%d %H:%M:%S')
                    # dt_check_out = datetime.strptime(att.check_out,'%Y-%m-%d %H:%M:%S')
                    # user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
                    # check_in = pytz.utc.localize(dt_check_in).astimezone(user_tz)
                    # check_out = pytz.utc.localize(dt_check_out).astimezone(user_tz)
                    rec.checkin = att.check_in
                    rec.checkout = att.check_out

    def _total_hours(self):
        for rec in self:
            if rec.checkin and rec.checkout:
                checkin = datetime.strptime(rec.checkin, '%Y-%m-%d %H:%M:%S')
                checkout = datetime.strptime(rec.checkout, '%Y-%m-%d %H:%M:%S')
                total_working_time = datetime.strptime(str(checkout.time()),'%H:%M:%S') - datetime.strptime(str(checkin.time()),'%H:%M:%S')
                rec.total_working_time = str(total_working_time)
            else:
                rec.total_working_time = False

    def get_break_from_and_to(self):
        resource_calendar = self.env['resource.calendar']
        for rec in self:
            for res in resource_calendar.search([]):
                if rec.employee_id.calendar_id == res:
                    for fix_pattern in res.attendance_ids:
                        check_date = datetime.strptime(rec.date_start[:10], '%Y-%m-%d')
                        weekday = check_date.weekday()
                        if int(fix_pattern.dayofweek) == weekday:
                            rec.break_from = fix_pattern.break_from
                            rec.break_to = fix_pattern.break_to
                    for shift_pattern in res.shift_pattern_line_ids:
                        check_date = datetime.strptime(rec.date_start[:10], '%Y-%m-%d')
                        weekday = check_date.weekday()
                        weekday +=1
                        if int(shift_pattern.variation_name) == weekday:
                            rec.break_from = shift_pattern.break_from
                            rec.break_to = shift_pattern.break_to
                    
class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _auto_create_employee_working_calendar(self):
        cr = self.env.cr
        cr.execute("DELETE from employee_working_schedule_calendar where schedule='fixed_schedule'")
        cr.execute("DELETE from employee_working_schedule_calendar where is_holiday=TRUE")

        end_year = datetime.now().strftime('%Y')
        hr_year_id = self.env['hr.year'].search(['|', ('code', '=', end_year), ('name', '=', end_year)])
        year_end_date = hr_year_id.date_stop

        public_holidays = False
        public_holidays_obj = self.env['hr.holiday.public'].search([('state','in',('confirmed','validated'))],order='id desc')
        if public_holidays_obj:
            public_holidays = public_holidays_obj[0]

        for contract in self.env['hr.contract'].search([('state', 'in', ('open', 'pending'))]):
            working_hours = contract.working_hours.id
            start_date = contract.date_start
            cessation_date = False
            for history in contract.employee_id.history_ids.filtered(lambda r: r.contract_status in ('running', 'to_renew')):
                cessation_date = history.cessation_date
                if cessation_date:
                    cessation_date_obj = datetime.strptime(cessation_date, "%Y-%m-%d")
            if contract.date_end:
                end_date = contract.date_end
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                if cessation_date:
                    if cessation_date_obj < end_date_obj:
                        end_date = cessation_date
            else:
                end_date = year_end_date
                if cessation_date:
                    end_date = cessation_date
            department = contract.department_id and contract.department_id.id or False
            employee = contract.employee_id.id
            working_schdule_obj = self.env['employee.working.schedule.calendar']
            alternateweek_temp_obj = self.env['working.schedule.alternateweek.temp']
            shiftpatterskip_obj = self.env['working.schedule.shiftpatternskipdate.temp']
    
            last_schedule = working_schdule_obj.search([('contract_id', '=', contract.id), ('date_start', '!=', False), ('date_end', '!=', False)], order='date_start desc,date_end desc', limit=1)
            # Make alternate week working schedule temp table empty before start processing.
            existing_temp_alternateweek_info = alternateweek_temp_obj.search([('contract_id', '=', contract.id)])
            if existing_temp_alternateweek_info:
                existing_temp_alternateweek_info.unlink()
    
            # Make shift pattern week working schedule temp table empty before start processing.
            existing_temp_shiftpatternskip_info = shiftpatterskip_obj.search([('contract_id', '=', contract.id)])
            if existing_temp_shiftpatternskip_info:
                existing_temp_shiftpatternskip_info.unlink()
    
            # Create new next working schedules from last working schedule
            working_schedule = self.env['resource.calendar'].browse(int(working_hours))
            if working_schedule.schedule == 'shift_pattern':
                number_of_variation = working_schedule.number_of_variation
    
            if working_schedule:
                DATETIME_FORMAT = '%Y-%m-%d'
                # replace start date by last scheduler if have
                if last_schedule:
                    start_day = datetime.strptime(last_schedule.date_start, DEFAULT_SERVER_DATETIME_FORMAT).date()
                    start = datetime.strptime(start_day.strftime('%Y-%m-%d'), DATETIME_FORMAT)
                else:
                    start = datetime.strptime(start_date, DATETIME_FORMAT)
                if end_date:   
                    end = datetime.strptime(end_date, DATETIME_FORMAT)
        
                    date_diff = end - start
                    number_of_variation_count = 1
                    for i in range(date_diff.days + 1):
                        flag = False                        
                        date_to_store = start + timedelta(i)
                        
                        date_store = datetime.strftime(date_to_store,'%Y-%m-%d')
                        if public_holidays:
                            for rec in public_holidays.holiday_line_ids:
                                if rec.holiday_date == date_store:
                                    flag = True                                    
                            if flag:
                                continue

                        month_number = self.get_month_number_from_date(date_to_store)
                        # _logger.info("i: %s  ===  start : %s === end:  %s === contract %s", i,start, end, contract.name)
                        if working_schedule.schedule == 'fixed_schedule':
                            if working_schedule.attendance_ids:
                                for attendance in working_schedule.attendance_ids:
                                    if int(month_number) == int(attendance.dayofweek):
        
                                        # Setup of Working Schedule in normal way if employee is NOT working on Alternate Week
                                        if not attendance.alternate_week:
                                            if str(date_to_store.date()) >= attendance.date_from and not attendance.date_to:
                                                self.add_to_working_calendar_schedule(date_to_store, attendance, department, employee, contract, month_number, working_hours)
                                                break
                                            elif (str(date_to_store.date()) >= attendance.date_from) and (attendance.date_to and str(date_to_store.date()) <= attendance.date_to):
                                                self.add_to_working_calendar_schedule(date_to_store, attendance, department, employee, contract, month_number, working_hours)
                                                break
                                        # Setup of Working Schedule if employee is working on Alternate Week
                                        if attendance.alternate_week:
                                            if attendance.date_from:
                                                if str(date_to_store.date()) >= attendance.date_from and not attendance.date_to:
                                                    # Check if date is stored in temp table to use
                                                    check_date = alternateweek_temp_obj.search([('name', '=', date_to_store), ('contract_id', '=', contract.id)])
                                                    if check_date:
                                                        self.add_to_working_calendar_schedule(date_to_store, attendance, department, employee, contract, month_number, working_hours)
        
                                                        new_date_to_store = date_to_store + timedelta(weeks=2)
        
                                                        alternateweek_temp_obj.create({'name': new_date_to_store, 'contract_id': contract.id})
                                                    else:
                                                        # Find difference of date with starting date
                                                        starting_date = datetime.strptime(attendance.date_from, DATETIME_FORMAT)
                                                        first_date_check = date_to_store - starting_date
        
                                                        # If the difference is less than 7 then add date in working schedule
                                                        if first_date_check.days <= 7:
                                                            self.add_to_working_calendar_schedule(date_to_store, attendance, department, employee, contract, month_number, working_hours)
        
                                                            new_date_to_store = date_to_store + timedelta(weeks=2)
        
                                                            alternateweek_temp_obj.create({'name': new_date_to_store, 'contract_id': contract.id})
        
                                                if (str(date_to_store.date()) >= attendance.date_from) and (attendance.date_to and str(date_to_store.date()) <= attendance.date_to):
                                                    # Check if date is stored in temp table to use
                                                    check_date = alternateweek_temp_obj.search([('name', '=', date_to_store), ('contract_id', '=', contract.id)])
                                                    if check_date:
                                                        self.add_to_working_calendar_schedule(date_to_store, attendance, department, employee, contract, month_number, working_hours)
        
                                                        new_date_to_store = date_to_store + timedelta(weeks=2)
        
                                                        alternateweek_temp_obj.create({'name': new_date_to_store, 'contract_id': contract.id})
                                                    else:
                                                        # Find difference of date with starting date
                                                        starting_date = datetime.strptime(attendance.date_from, DATETIME_FORMAT)
                                                        first_date_check = date_to_store - starting_date
        
                                                        # If the difference is less than 7 then add date in working schedule
                                                        if first_date_check.days <= 7:
                                                            self.add_to_working_calendar_schedule(date_to_store, attendance, department, employee, contract, month_number, working_hours)
        
                                                            new_date_to_store = date_to_store + timedelta(weeks=2)
        
                                                            alternateweek_temp_obj.create({'name': new_date_to_store, 'contract_id': contract.id})
                                            else:
                                                raise UserError(_("Please specify 'Starting Date' to calculate alternate week schedule for %s") % (str(attendance.name)))
        
        holiday_lines = self.env['hr.holiday.lines'].search([])
        holiday_lines.remove_all_current_holiday()
        holiday_lines.public_holiday_working_calendar()
        return True

    
    def add_to_working_calendar_schedule(self, date_to_store, attendance, department, employee, contract, month_number, working_hours):
        schedule_values = {}
        att_start_time_string = str(attendance.hour_from)
        att_end_time_string = str(attendance.hour_to)
        att_start_time = att_start_time_string.split('.')
        att_end_time = att_end_time_string.split('.')

        date_start_end_temp = date_to_store
        if attendance.hour_from != 0.0:
            date_start = date_start_end_temp.replace(hour=int(att_start_time[0]), minute=int(att_start_time[1] + '0' if len(att_start_time[1]) == 1 else att_start_time[1]))
        else:
            date_start = date_start_end_temp.replace(hour=17, minute=00)
        if attendance.hour_to != 0.0:
            date_end = date_start_end_temp.replace(hour=int(att_end_time[0]), minute=int(att_end_time[1] + '0' if len(att_end_time[1]) == 1 else att_end_time[1]))
        else:
            date_end = date_start_end_temp.replace(hour=17, minute=00)
        user_pool = self.env['res.users']
        user = user_pool.browse(self.env.uid)
        tz = pytz.timezone(user.partner_id.tz or 'Asia/Jakarta') or pytz.utc
        
        if attendance.hour_from != 0.0:
            date_start = tz.localize(
                datetime.strptime(date_start.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc)
        if attendance.hour_to != 0.0:
            date_end = tz.localize(
                datetime.strptime(date_end.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc)
        schedule_values = {
            'name': att_start_time_string + " - " + att_end_time_string,
            'department_id': department,
            'employee_id': employee,
            'contract_id': contract.id,
            'date_start': date_start,
            'date_end': date_end,
            'dayofweek': str(month_number),
            'hour_from': attendance.hour_from,
            'hour_to': attendance.hour_to,
            'working_hours': working_hours,
            'schedule' :'fixed_schedule',
        }

        res = self.env['employee.working.schedule.calendar'].create(schedule_values)
        return res

    def add_shift_patter_time_to_working_calendar_schedule(self, date_to_store, hour_from, hour_to, department, employee, contract, month_number, working_hours):
        att_start_time_string = self.get_time_string(hour_from)
        att_end_time_string = self.get_time_string(hour_to)

        att_start_time = att_start_time_string.split(':')
        att_end_time = att_end_time_string.split(':')
        
        date_start_end_temp = date_to_store
        date_start = date_start_end_temp.replace(hour=int(att_start_time[0]), minute=int(att_start_time[1]))
        date_end = date_start_end_temp.replace(hour=int(att_end_time[0]), minute=int(att_end_time[1]))
        
        user_pool = self.env['res.users']
        user = user_pool.browse(self.env.uid)
        tz = pytz.timezone(user.partner_id.tz or 'Asia/Jakarta') or pytz.utc
 
        date_start = tz.localize(
            datetime.strptime(date_start.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc)
        date_end = tz.localize(
            datetime.strptime(date_end.strftime("%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc)
        
        date_to_store_month = date_to_store.strftime("%m")
        date_to_store_day = date_to_store.strftime("%d")
        date_to_store_year = date_to_store.strftime("%Y")
        date_start = date_start.replace(month=int(date_to_store_month), day=int(date_to_store_day), year=int(date_to_store_year))
        date_end = date_end.replace(month=int(date_to_store_month), day=int(date_to_store_day), year=int(date_to_store_year))
        
        schedule_values = {
            'name': att_start_time_string + " - " + att_end_time_string,
            'department_id': department,
            'employee_id': employee,
            'contract_id': contract.id,
            'date_start': date_start,
            'date_end': date_end,
            'dayofweek': str(month_number),
            'hour_from': hour_from,
            'hour_to': hour_to,
            'working_hours': working_hours,
            'schedule' : 'shift_pattern',
        }

        res = self.env['employee.working.schedule.calendar'].create(schedule_values)

        return res

    def get_month_number_from_date(self, date):
        day_of_month = date.strftime('%A')
        month_number = 0
        if day_of_month == 'Monday':
            month_number = 0
        elif day_of_month == 'Tuesday':
            month_number = 1
        elif day_of_month == 'Wednesday':
            month_number = 2
        elif day_of_month == 'Thursday':
            month_number = 3
        elif day_of_month == 'Friday':
            month_number = 4
        elif day_of_month == 'Saturday':
            month_number = 5
        elif day_of_month == 'Sunday':
            month_number = 6
        return month_number

    def get_time_string(self, duration):
        result = ''
        currentHours = int(duration // 1)
        currentMinutes = int(round(duration % 1 * 60))
        if(currentHours <= 9):
            currentHours = "0" + str(currentHours)
        if(currentMinutes <= 9):
            currentMinutes = "0" + str(currentMinutes)
        result = str(currentHours) + ":" + str(currentMinutes)
        return result


class HrWorkingAlternateWeek(models.Model):
    _name = 'working.schedule.alternateweek.temp'

    name = fields.Date('Date to check')
    contract_id = fields.Many2one('hr.contract', string="Contract")


class HrWorkingShiftPatternSkipDate(models.Model):
    _name = 'working.schedule.shiftpatternskipdate.temp'

    name = fields.Date('Date to skip')
    shift_start_date = fields.Date('Shift start date')
    contract_id = fields.Many2one('hr.contract', string="Contract")


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    work_from = fields.Char('Work From', compute='get_work_hour_from')
    work_to = fields.Char('Work To', compute='get_work_hour_to')

    def get_employee_calendar(self):
        employee_calendar = self.env['employee.working.schedule.calendar'].search([('employee_id', '=', self.employee_id.id),
                                                                      ('date_start', '>=', self.check_in.split(' ')[0] + ' 00:00:00'),
                                                                      ('date_start', '<=', self.check_in.split(' ')[0] + ' 23:59:59')], limit=1)
        if employee_calendar:
            return employee_calendar.name
        else:
            return False

    def get_employee_calendar2(self, checkin, employee):
        employee_calendar = self.env['employee.working.schedule.calendar'].search([('employee_id', '=', employee.id),
                                                                      ('date_start', '>=', checkin.split(' ')[0] + ' 00:00:00'),
                                                                      ('date_start', '<=', checkin.split(' ')[0] + ' 23:59:59')], limit=1)
        if employee_calendar:
            return employee_calendar.name
        else:
            return False

    @api.depends('employee_id', 'check_in')
    @api.multi
    def get_work_hour_from(self):
        for rec in self:
            date_range = rec.get_employee_calendar()
            if date_range:
                rec.work_from = date_range.split('-')[0]

    @api.depends('employee_id', 'check_in')
    def get_work_hour_to(self):
        for rec in self:
            date_range = rec.get_employee_calendar()
            if date_range:
                rec.work_to = date_range.split('-')[1]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.employee_code = self.employee_id.emp_id

    @api.multi
    def write(self, vals):
        for rec in self:
            if 'employee_id' in vals:
                vals.update({
                    'employee_code' : rec.env['hr.employee'].browse(vals['employee_id']).emp_id,

                })
        return super(HrAttendance, self).write(vals)

    @api.model
    def create(self, vals):
        if 'employee_id' in vals:
            vals.update({
                'employee_code': self.env['hr.employee'].browse(vals['employee_id']).emp_id
            })
        return super(HrAttendance, self).create(vals)

    def _auto_closed_attendance(self):
        day = int(fields.datetime.now().weekday()) + 1
        time = fields.datetime.now().time()
        time_float = time.hour + time.minute / 60.0
        attendance_ids = self.env['hr.attendance'].search([('check_out', '=', False)])
        for attendance in attendance_ids:
            if attendance.employee_id.calendar_id.schedule == 'shift_pattern':
                for working_hours in attendance.employee_id.calendar_id.shift_pattern_line_ids:
                    if not working_hours.is_cross_day:
                        if int(working_hours.variation_name) == day and time_float > working_hours.end_time:
                            date = datetime.combine(fields.datetime.now().today(), datetime.min.time())
                            from_delta = timedelta(hours=working_hours.end_time)
                            checkout_date = date + from_delta
                            attendance.check_out = checkout_date
                    else:
                        day = day - 1
                        if int(working_hours.variation_name) == day and (time_float - working_hours.end_time) > 0.9 and (time_float - working_hours.end_time) < 0.6:
                            date = datetime.combine(fields.datetime.now().today() + timedelta(days=1), datetime.min.time())
                            from_delta = timedelta(hours=working_hours.end_time)
                            checkout_date = date + from_delta
                            attendance.check_out = checkout_date


class Employee(models.Model):
    _inherit = 'hr.employee'

    shift_pattern_history_line_ids = fields.One2many('shift.pattern.history.line', 'employee_id', 'Shift Pattern History')
    working_time_history_line_ids = fields.One2many('working.time.history.line', 'employee_id', 'Working Time History')

    @api.multi
    def write(self, vals):
        res = super(Employee, self).write(vals)
        if vals.get('calendar_id'):
            if not self.working_time_history_line_ids:
                contract_id = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1)
                if contract_id:
                    self.env['working.time.history.line'].create({
                        'employee_id': self.id,
                        'calendar_id': contract_id.working_hours.id,
                        'start_date': contract_id.date_start,
                        'end_date': fields.datetime.now().today(),
                        'contract_id': contract_id.id,
                    })
                self.env['working.time.history.line'].create({
                    'employee_id': self.id,
                    'calendar_id': self.calendar_id.id,
                    'start_date': fields.datetime.now().today(),
                    'contract_id': contract_id.id,
                })
            else:
                contract_id = self.env['hr.contract'].search([('employee_id', '=', self.id), ('state', '=', 'open')], limit=1)
                self.working_time_history_line_ids[-1].end_date = fields.datetime.now().today()
                self.env['working.time.history.line'].create({
                    'employee_id': self.id,
                    'calendar_id': self.calendar_id.id,
                    'start_date': fields.datetime.now().today(),
                    'contract_id': contract_id.id,
                })
        return res


class ShiftPatternHistoryLine(models.Model):
    _name = 'shift.pattern.history.line'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    variation_name = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday')
    ], string='Day')
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')


class WorkingTimeHistoryLine(models.Model):
    _name = 'working.time.history.line'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    calendar_id = fields.Many2one('resource.calendar', 'Working Time')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    contract_id = fields.Many2one('hr.contract', 'Contract')
