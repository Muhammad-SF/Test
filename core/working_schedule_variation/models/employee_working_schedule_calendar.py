from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import pytz
import logging
_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _auto_create_employee_working_calendar2(self):
        _logger.info('>>>>>>>>>>>_auto_create_employee_working_calendar2>>>>>>>>>> %s')
        cr = self.env.cr
        cr.execute("DELETE from employee_working_schedule_calendar where schedule='shift_pattern'")
        cr.execute("DELETE from employee_working_schedule_calendar where is_holiday=TRUE")

        end_year = datetime.now().strftime('%Y')
        hr_year_id = self.env['hr.year'].search(['|', ('code', '=', end_year), ('name', '=', end_year)])
        year_end_date = hr_year_id.date_stop

        public_holidays = False
        public_holidays_obj = self.env['hr.holiday.public'].search([('state','in',('confirmed','validated'))],order='id desc')
        if public_holidays_obj:
            public_holidays = public_holidays_obj[0]

        for contract in self.search([('state', 'in', ('open', 'pending'))]):
            _logger.info('contract>>>>>>>>>>>>>>>>>>>>> %s' % contract)

            # Retrieve contract related information
            working_hours = contract.working_hours.id
            start_date = contract.date_start
            _logger.info('contract start date>>>>>>>>>>>>>>>>>>>>> %s' % start_date)
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
    
            # Check if working schedule for this contract already available or not.
            # If available then first remove it to get the fresh information
            # existing_schedule = working_schdule_obj.search([('contract_id', '=', contract.id)])
            # if existing_schedule:
            #     existing_schedule.unlink()
            # find last working schedule of contract
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
                    if working_schedule.schedule == 'shift_pattern':
                        week_day_list = []
                        _logger.info('week_day_lisst>>>>>>>>>>>>>>>>>>>>> %s' % week_day_list)
                        week_start_day = int(working_schedule.week_start_day)
                        for day in range(0, working_schedule.number_of_variation):
                            for days in working_schedule.shift_pattern_line_ids:
                                if days.variation_name and days.name:
                                    if week_start_day == 7:
                                        week_start_day = 0
                                        week_day_list.append(str(days.variation_name))
                                    else:
                                        week_day_list.append(str(days.variation_name))
                                        week_start_day += 1
                        last_week_number = start.strftime('%U')    
                        last_month_number = start.strftime('%m')
                        loop_start = False
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
                            if str(date_to_store.strftime('%w')) in week_day_list:
                                month_number = self.get_month_number_from_date(date_to_store)
                                if working_schedule.interval == 'daily':
                                    variation_x = working_schedule.shift_pattern_line_ids[number_of_variation_count - 1]
                                    if working_schedule.number_of_variation:
                                        _logger.info('working_schedule.number_of_variation>>>>>>>>>>>>>>>>>>>>> %s' % working_schedule.number_of_variation)
                                        shift_hour_from = variation_x.start_time
                                        _logger.info('shift_hour_from>>>>>>>>>>>>>>>>>>>>> %s' % shift_hour_from)
                                        shift_hour_to = variation_x.end_time
                                        _logger.info('shift_hour_to>>>>>>>>>>>>>>>>>>>>> %s' % shift_hour_to)
                                        self.add_shift_patter_time_to_working_calendar_schedule(date_to_store, shift_hour_from, shift_hour_to, department, employee, contract, month_number, working_hours)
                                    number_of_variation_count += 1
                                    if number_of_variation_count > number_of_variation:
                                        number_of_variation_count = 1
                                if working_schedule.interval == 'weekly':
                                    if last_week_number != date_to_store.strftime('%U'):
                                        if loop_start:
                                            number_of_variation_count += 1
                                    if number_of_variation_count > number_of_variation:
                                        number_of_variation_count = 1
                                    variation_x = working_schedule.shift_pattern_line_ids[number_of_variation_count - 1]
                                    if working_schedule.number_of_variation:
                                        shift_hour_from = variation_x.start_time
                                        shift_hour_to = variation_x.end_time
                                        self.add_shift_patter_time_to_working_calendar_schedule(date_to_store, shift_hour_from, shift_hour_to, department, employee, contract, month_number, working_hours)
                                last_week_number = date_to_store.strftime('%U')
                                if working_schedule.interval == 'monthly':
                                    if last_month_number != date_to_store.strftime('%m'):
                                        if loop_start:
                                            number_of_variation_count += 1
                                    if number_of_variation_count > number_of_variation:
                                        number_of_variation_count = 1
                                    variation_x = working_schedule.shift_pattern_line_ids[number_of_variation_count - 1]
                                    if working_schedule.number_of_variation:
                                        shift_hour_from = variation_x.start_time
                                        shift_hour_to = variation_x.end_time
                                        self.add_shift_patter_time_to_working_calendar_schedule(date_to_store, shift_hour_from, shift_hour_to, department, employee, contract, month_number, working_hours)
                                last_month_number = date_to_store.strftime('%m')
                                loop_start = True
        holiday_lines = self.env['hr.holiday.lines'].search([])
        holiday_lines.remove_all_current_holiday()
        holiday_lines.public_holiday_working_calendar()                        
        return True

        
