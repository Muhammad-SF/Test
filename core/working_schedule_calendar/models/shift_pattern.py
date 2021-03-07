
from datetime import date, datetime, timedelta
from odoo import fields, api, models, _



class resource_calendar_shift_pattern(models.Model):
    _name = 'resource.calendar.shift.pattern'

    name = fields.Char(string='Name', required=1)
    no_of_work_days = fields.Integer(string='No. of Work Days', required=1)
    no_of_days = fields.Integer(string='No. of Off days', required=1)
    company_id = fields.Many2one('res.company', string='Company', required=1)
    active = fields.Boolean(string='Active', default=lambda *a: True)


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """

        def was_on_leave(employee_id, datetime_day):
            res1 = {'name': False, 'days': 0.0, 'half_work': False}
            day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.env['hr.holidays'].search(
                [('state', '=', 'validate'), ('employee_id', '=', employee_id), ('type', '=', 'remove'),
                 ('date_from', '<=', day), ('date_to', '>=', day)])
            if holiday_ids:
                res = holiday_ids[0].holiday_status_id.name
                res1['name'] = res
                num_days = 1.0
                if holiday_ids[0].half_day == True:
                    num_days = 0.5
                    res1['half_work'] = True
                res1['days'] = num_days
            return res1

        res = []
        for contract in self.env['hr.contract'].browse(contract_ids):
            if not contract.working_hours:
                # fill only if the contract as a working schedule linked
                continue
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }
            leaves = {}
            day_from = datetime.strptime(date_from, "%Y-%m-%d")
            day_to = datetime.strptime(date_to, "%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            working_schedule = contract.working_hours
            if working_schedule.schedule == 'fixed_schedule':
                for day in range(0, nb_of_days):
                    #                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                    working_hours_on_day = contract.working_hours.working_hours_on_day(day_from + timedelta(days=day))
                    if working_hours_on_day:
                        # the employee had to work
                        leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day))
                        if leave_type and leave_type['name']:
                            # if he was on leave, fill the leaves dict
                            if leave_type['name'] in leaves:
                                leaves[leave_type['name']]['number_of_days'] += leave_type['days']
                                if leave_type['half_work'] == True:
                                    leaves[leave_type['name']]['number_of_hours'] += working_hours_on_day / 2
                                else:
                                    leaves[leave_type['name']]['number_of_hours'] += working_hours_on_day
                            else:
                                if leave_type['half_work'] == True:
                                    working_hours_on_day = working_hours_on_day / 2
                                leaves[leave_type['name']] = {
                                    'name': leave_type['name'],
                                    'sequence': 5,
                                    'code': leave_type['name'],
                                    'number_of_days': leave_type['days'],
                                    'number_of_hours': working_hours_on_day,
                                    'contract_id': contract.id,
                                }
                        else:
                            # add the input vals to tmp (increment if existing)
                            attendances['number_of_days'] += 1.0
                            attendances['number_of_hours'] += working_hours_on_day

            else:
                number_of_variation = working_schedule.number_of_variation
                number_of_variation_count = 1
                if working_schedule.shift_pattern_line_ids:
                    for day in range(0, nb_of_days):
                        variation_x = working_schedule.shift_pattern_line_ids[number_of_variation_count - 1]
                        if variation_x.shift_daily_id:
                            # the employee had to work
                            leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day))
                            if leave_type and leave_type['name']:
                                # if he was on leave, fill the leaves dict
                                if leave_type['name'] in leaves:
                                    leaves[leave_type['name']]['number_of_days'] += leave_type['days']
                                    if leave_type['half_work'] == True:
                                        leaves[leave_type['name']]['number_of_hours'] += working_hours_on_day / 2
                                    else:
                                        leaves[leave_type['name']]['number_of_hours'] += working_hours_on_day
                                else:
                                    if leave_type['half_work'] == True:
                                        working_hours_on_day = working_hours_on_day / 2
                                    leaves[leave_type['name']] = {
                                        'name': leave_type['name'],
                                        'sequence': 5,
                                        'code': leave_type['name'],
                                        'number_of_days': leave_type['days'],
                                        'number_of_hours': working_hours_on_day,
                                        'contract_id': contract.id,
                                    }
                            else:
                                # add the input vals to tmp (increment if existing)
                                shift_hour_from = variation_x.shift_daily_id.start_shift_daily
                                shift_hour_to = variation_x.shift_daily_id.end_shift_daily
                                attendances['number_of_days'] += 1.0
                                attendances['number_of_hours'] += (shift_hour_to - shift_hour_from)
                        number_of_variation_count += 1
                        if number_of_variation_count > number_of_variation:
                            number_of_variation_count = 1
            leaves = [value for key, value in leaves.items()]
            res += [attendances] + leaves
        return res
