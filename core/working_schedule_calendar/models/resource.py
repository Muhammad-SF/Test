from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShiftPatternLine(models.Model):
    _name = 'shift.pattern.line'

    name = fields.Boolean('Variation')
    # variation_name = fields.Char('Day')
    variation_name = fields.Selection([
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
        ('7', 'Sunday')
    ], string='Day')
    shift_daily_id = fields.Many2one('shift.daily', "Shift")
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    break_from = fields.Float('Break From')
    break_to = fields.Float('Break To')
    resource_calendar_id = fields.Many2one('resource.calendar', ondelete='cascade')
    is_cross_day = fields.Boolean('Cross Day?')
    half_day = fields.Boolean('Half Day')
    time_to = fields.Float(string='')
    time_end = fields.Float(string='')
    grace_time_for_late = fields.Float('Grace Time for Late')

    @api.onchange('time_to')
    def check_time_to(self):
        if self.time_to < self.start_time or self.time_to > self.end_time:
            raise UserError(_('The Half Day should be between start time and end time.'),)

    @api.onchange('time_end')
    def check_time_to(self):
        if self.time_end < self.start_time or self.time_end > self.end_time:
            raise UserError(_('The Half Day should be between start time and end time.'),)

    @api.onchange('break_from')
    def check_break_from(self):
        if self.break_from < self.start_time or self.break_from > self.end_time:
            raise UserError(_('The Break From Time Is Not Valid.'),)
        

    @api.onchange('break_to')
    def check_break_to(self):
        if self.break_to < self.start_time or self.break_to > self.end_time:
            raise UserError(_('The Break To Time Is Not Valid.'),)   


class resource_calendar(models.Model):
    _inherit = 'resource.calendar'

    schedule = fields.Selection([('fixed_schedule', 'Fixed Schedule'),
                                 ('shift_pattern', 'Shift Pattern'),
                                 ], string='Schedule', default='fixed_schedule')
    shift_start_date = fields.Date(string='Starting Date')
    shift_end_date = fields.Date(string='Ending Date')
    shift_hour_from = fields.Float(string='Work From')
    shift_hour_to = fields.Float(string='Work To')
    shift_pattern_id = fields.Many2one('resource.calendar.shift.pattern', domain="[('company_id', '=', company_id),('active', '=', True)]", string='Shift Pattern')
    no_of_work_days = fields.Integer('No Of Work Days')
    no_of_off_days = fields.Integer('No Of Off Days')
    name = fields.Char(string='Working Time Name')
    number_of_variation = fields.Integer('Number of Variation')
    variation_1 = fields.Many2one('shift.daily')
    display_variation_1 = fields.Boolean(default=False)
    variation_2 = fields.Many2one('shift.daily')
    display_variation_2 = fields.Boolean(default=False)
    variation_3 = fields.Many2one('shift.daily')
    display_variation_3 = fields.Boolean(default=False)
    variation_4 = fields.Many2one('shift.daily')
    display_variation_4 = fields.Boolean(default=False)
    variation_5 = fields.Many2one('shift.daily')
    display_variation_5 = fields.Boolean(default=False)
    variation_6 = fields.Many2one('shift.daily')
    display_variation_6 = fields.Boolean(default=False)
    variation_7 = fields.Many2one('shift.daily')
    display_variation_7 = fields.Boolean(default=False)
    variation_8 = fields.Many2one('shift.daily')
    display_variation_8 = fields.Boolean(default=False)
    variation_9 = fields.Many2one('shift.daily')
    display_variation_9 = fields.Boolean(default=False)
    variation_10 = fields.Many2one('shift.daily')
    display_variation_10 = fields.Boolean(default=False)
    variation_11 = fields.Many2one('shift.daily')
    display_variation_11 = fields.Boolean(default=False)
    variation_12 = fields.Many2one('shift.daily')
    display_variation_12 = fields.Boolean(default=False)
    variation_13 = fields.Many2one('shift.daily')
    display_variation_13 = fields.Boolean(default=False)
    variation_14 = fields.Many2one('shift.daily')
    display_variation_14 = fields.Boolean(default=False)
    variation_15 = fields.Many2one('shift.daily')
    display_variation_15 = fields.Boolean(default=False)
    variation_16 = fields.Many2one('shift.daily')
    display_variation_16 = fields.Boolean(default=False)
    variation_17 = fields.Many2one('shift.daily')
    display_variation_17 = fields.Boolean(default=False)
    variation_18 = fields.Many2one('shift.daily')
    display_variation_18 = fields.Boolean(default=False)
    variation_19 = fields.Many2one('shift.daily')
    display_variation_19 = fields.Boolean(default=False)
    variation_20 = fields.Many2one('shift.daily')
    display_variation_20 = fields.Boolean(default=False)
    variation_21 = fields.Many2one('shift.daily')
    display_variation_21 = fields.Boolean(default=False)
    variation_22 = fields.Many2one('shift.daily')
    display_variation_22 = fields.Boolean(default=False)
    variation_23 = fields.Many2one('shift.daily')
    display_variation_23 = fields.Boolean(default=False)
    variation_24 = fields.Many2one('shift.daily')
    display_variation_24 = fields.Boolean(default=False)
    variation_25 = fields.Many2one('shift.daily')
    display_variation_25 = fields.Boolean(default=False)
    variation_26 = fields.Many2one('shift.daily')
    display_variation_26 = fields.Boolean(default=False)
    variation_27 = fields.Many2one('shift.daily')
    display_variation_27 = fields.Boolean(default=False)
    variation_28 = fields.Many2one('shift.daily')
    display_variation_28 = fields.Boolean(default=False)
    shift_pattern_line_ids = fields.One2many('shift.pattern.line', 'resource_calendar_id', 'Variations')
    absence = fields.Boolean(string='Absence/HalfDay')
    absence_start_time = fields.Float()
    absence_end_time = fields.Float()
    halfday_start_time = fields.Float()
    halfday_end_time = fields.Float()
    absence_shift = fields.Boolean(string='Absence/HalfDay')
    absence_start_time_shift = fields.Float()
    absence_end_time_shift = fields.Float()
    halfday_start_time_shift = fields.Float()
    halfday_end_time_shift = fields.Float()


    @api.constrains('absence_start_time', 'absence_end_time', 'halfday_start_time', 'halfday_end_time',
     'absence_start_time_shift', 'absence_end_time_shift', 'halfday_start_time_shift', 'halfday_end_time_shift')
    def onchange_percent(self):
        if self.absence_start_time > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        if self.absence_end_time > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        if self.halfday_start_time > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        if self.halfday_end_time > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        if self.absence_start_time_shift > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        if self.absence_end_time_shift > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        if self.halfday_start_time_shift > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        if self.halfday_end_time_shift > 100:
            raise ValidationError(_('Maximize value is 100%.'),)
        # if self.absence_start_time >= self.absence_end_time:
        #     raise ValidationError(_('Lower parameter value should be grater then upper parameter.'),)
        # if self.halfday_start_time >= self.halfday_end_time:
        #     raise ValidationError(_('Lower parameter value should be grater then upper parameter.'),)
        # if self.absence_start_time_shift >= self.absence_end_time_shift:
        #     raise ValidationError(_('Lower parameter value should be grater then upper parameter.'),)
        # if self.halfday_start_time_shift >= self.halfday_end_time_shift:
        #     raise ValidationError(_('Lower parameter value should be grater then upper parameter.'),)



    @api.onchange('number_of_variation')
    def _compute_variation_number(self):
        for rec in self:
            new_dict = {}
            for i in range(28):
                new_dict.update({
                    'display_variation_' + str(i + 1): False
                })
            if rec.number_of_variation:
                for i in range(rec.number_of_variation):
                    new_dict.update({
                        'display_variation_' + str(i + 1) : True
                    })
            return {
                'value' : new_dict
            }

    @api.onchange('number_of_variation')
    def onchange_number_of_variation(self):
        if self.number_of_variation >= 8:
            raise UserError('Please add Number of Variation between 1 to 7')

        if self.number_of_variation:
            list_days = ['0', '1', '2', '3', '4', '5', '6', '7']
            vals = []
            for line in range(self.number_of_variation):
                vals.append((0, 0, {'name': "Variation ", 'variation_name': list_days[line + 1]}))
            return {
                'value' : {'shift_pattern_line_ids': vals}
            }
        else:
            return {
                'value': {'shift_pattern_line_ids': False}
            }

    @api.onchange('shift_hour_from', 'shift_hour_to')
    def onchange_shift_working_hours(self):
        warning = {}
        if self.shift_hour_from:
            if self.shift_hour_from < 0 or self.shift_hour_from > 24:
                warning = {'title': 'Value Error', 'message': "Please input a valid time."}
        if self.shift_hour_to:
            if self.shift_hour_to < 0 or self.shift_hour_to > 24:
                warning = {'title': 'Value Error', 'message': "Please input a valid time."}
        return {'warning': warning}

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.shift_pattern_id = False

    @api.multi
    def write(self, values):
        previous_schedule = ''
        for sch in self:
            previous_schedule = sch.schedule
        if not 'schedule' in values:
            values['schedule'] = previous_schedule
        else:
            if not values.get('schedule'):
                values['schedule'] = previous_schedule

        contract = super(resource_calendar, self).write(values)
        if values.get('shift_pattern_line_ids'):
            employee_ids = self.env['hr.employee'].search([('calendar_id', '=', self.id)])
            for employee in employee_ids:
                contract_id = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', 'in', ('open', 'pending'))], limit=1)
                if contract_id:
                    contract_id._auto_create_employee_working_calendar2()

                if not employee.shift_pattern_history_line_ids:
                    if employee.calendar_id.schedule == 'shift_pattern':
                        for working_hours in employee.calendar_id.shift_pattern_line_ids:
                            self.env['shift.pattern.history.line'].create({
                                'employee_id': employee.id,
                                'variation_name': working_hours.variation_name,
                                'start_time': working_hours.start_time,
                                'end_time': working_hours.end_time,
                            })
                else:
                    if employee.calendar_id.schedule == 'shift_pattern':
                        for working_hours in employee.calendar_id.shift_pattern_line_ids:     
                            if not any([shift_pattern_history.variation_name == working_hours.variation_name and shift_pattern_history.start_time == working_hours.start_time and shift_pattern_history.end_time == working_hours.end_time for shift_pattern_history in employee.shift_pattern_history_line_ids]):
                                self.env['shift.pattern.history.line'].create({
                                    'employee_id': employee.id,
                                    'variation_name': working_hours.variation_name,
                                    'start_time': working_hours.start_time,
                                    'end_time': working_hours.end_time,
                                })
        return contract

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        args += [('company_id', '=', self.env.user.company_id.id)]
        return super(resource_calendar, self).name_search(
            name=name, args=args, operator=operator, limit=limit,
        )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = domain or []
        domain.append(('company_id', '=', self.env.user.company_id.id))
        res = super(resource_calendar, self).search_read(domain=domain, fields=fields, offset=offset,
                                                    limit=limit, order=order)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = domain or []
        domain.append(('company_id', '=', self.env.user.company_id.id))
        res = super(resource_calendar, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                                   lazy=lazy)
        return res

    @api.model
    def search(self, args, offset=0, limit=0, order=None, count=False):
        args.append(('company_id', '=', self.env.user.company_id.id))
        res = super(resource_calendar, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
        return res


class resource_calendar_attendance(models.Model):
    _inherit = 'resource.calendar.attendance'
    _order = 'id asc'

    alternate_week = fields.Boolean('Alternate Week')
    schedule = fields.Selection(related="calendar_id.schedule", string='Schedule', store=True)
    working_hours = fields.Float('Working Hours')
    entitle_public_holiday = fields.Boolean('Entitle Public Holiday')
    name = fields.Char(string='Shift Name')
    grace_time_for_late = fields.Float('Grace Time for Late')
    break_from = fields.Float('Break From')
    break_to = fields.Float('Break To')
    time_to = fields.Float(string='')
    time_end = fields.Float(string='')


    @api.onchange('time_to')
    def check_time_from(self):
        if self.time_to < self.hour_from or self.time_to > self.hour_to:
            raise UserError(_('The Half Day should be between work from and work to.'),)

    @api.onchange('time_end')
    def check_time_from(self):
        if self.time_end < self.hour_from or self.time_end > self.hour_to:
            raise UserError(_('The Half Day should be between work from and work to.'),)

    @api.onchange('break_from')
    def check_break_from(self):
        if self.break_from < self.hour_from or self.break_from > self.hour_to:
            raise UserError(_('The Break From Time Is Not Valid.'),)

    @api.onchange('break_to')
    def check_break_to(self):
        if self.break_to < self.hour_from or self.break_to > self.hour_to:
            raise UserError(_('The Break To Time Is Not Valid.'),)   


    @api.onchange('hour_from', 'hour_to')
    def onchange_working_hours(self):
        warning = {}
        if self.hour_from:
            if self.hour_from < 0 or self.hour_from > 24:
                warning = {'title': 'Value Error', 'message': "Please input a valid time."}
        if self.hour_to:
            if self.hour_to < 0 or self.hour_to > 24:
                warning = {'title': 'Value Error', 'message': "Please input a valid time."}
        return {'warning': warning}


class ShiftDaily(models.Model):
    _name = 'shift.daily'
    
    name = fields.Char('Shift Daily Name')
    start_shift_daily = fields.Float('Start Shift Time')
    end_shift_daily = fields.Float('End Shift Time')
