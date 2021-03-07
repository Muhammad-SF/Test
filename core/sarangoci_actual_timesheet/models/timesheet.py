from odoo import models, fields, api
import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError

class ActualTimesheet(models.Model):
    _name = "actual.timesheet"
    _inherit = ['mail.thread','ir.needaction_mixin']

    @api.model
    def get_clock_in(self,data):
        result = []
        for item in data:
            employee_id = item.get('employee')
            for day in item.get('days'):
                day_data = day.get('lines')[0].get('date')
                dt = datetime.strptime(day_data, DEFAULT_SERVER_DATE_FORMAT)
                dt = datetime(dt.year, dt.month, dt.day)
                end_dt = datetime(dt.year, dt.month, dt.day, 23, 59)
                attendances = self.env['hr.attendance'].search([
                    ('employee_id','=',employee_id),
                    ('check_in', '>=', dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                    ('check_in', '<=',end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])
                last_check_in = None
                if attendances and attendances[0]:
                    last_check_in = attendances[0].check_in
                for attendance in attendances:
                    if attendance.check_in < last_check_in:
                        last_check_in = attendance.check_in
                result.append({
                    'employee_id':employee_id,
                    'check_in':last_check_in or '',
                    'date': day_data
                })
        return result

    @api.model
    def create(self, vals):
        if 'employee_id' in vals:
            if not self.env['hr.employee'].browse(vals['employee_id']).user_id:
                raise UserError(_('In order to create a timesheet for this employee, you must link him/her to a user.'))
        res = super(ActualTimesheet, self).create(vals)
        res.write({'state': 'draft'})
        return res

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.branch_id.name))
        return res

    @api.multi
    def compute_overtime(self):
        for timesheet in self:
            workingtime_range = self.env['hr.leave.config.settings'].default_get(['overtime'])['overtime']
            employees = list(set(ts.employee_id.id for ts in timesheet.timesheet_ids))
            for employee in employees:
                start_date = datetime.strptime(timesheet.date_from, DEFAULT_SERVER_DATE_FORMAT).date()
                # start_date = datetime.Date(start_date.)
                end_date = datetime.strptime(timesheet.date_to, DEFAULT_SERVER_DATE_FORMAT).date()
                while start_date <= end_date:
                    lines = timesheet.timesheet_ids.filtered(lambda t: t.employee_id.id==employee and \
                        t.date==start_date.strftime(DEFAULT_SERVER_DATE_FORMAT))
                    if not lines:
                        lines = self.env['actual.timesheet.line'].create({
                            'employee_id':employee,
                            'branch_sheet_id':timesheet.id,
                            'name': '/',
                            'date': start_date,
                            })
                    for line in lines.filtered(lambda l:not l.ot_edited):
                        dt = datetime.strptime(line.date, DEFAULT_SERVER_DATE_FORMAT)
                        dt = datetime(dt.year, dt.month, dt.day)
                        end_dt = datetime(dt.year, dt.month, dt.day, 23, 59)

                        attendances = self.env['hr.attendance'].search([('employee_id', '=', employee), 
                            ('check_in', '>=', dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), 
                            ('check_in', '<=', end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                            ('check_out', '!=', False)])
                        hours = 0.0
                        minutes = 0.0
                        for attendance in attendances:
                            check_in = datetime.strptime(attendance.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                            check_out = datetime.strptime(attendance.check_out, DEFAULT_SERVER_DATETIME_FORMAT)
                            diff = check_out - check_in
                            hours += int(diff.seconds/3600)
                            minutes += int((diff.seconds/60)%60)

                        overtime = hours + (minutes/60) - workingtime_range
                        line.with_context(from_cron=True).write({'overtime_hours': overtime, 'attendance_ids': [(6, 0 , attendances.ids)]})
                    start_date +=  relativedelta(days=1)

    def _default_date_from(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return time.strftime('%Y-%m-01')
        elif r == 'week':
            return (datetime.today() + relativedelta(days=-7)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-01-01')
        return fields.Date.context_today(self)

    def _default_date_to(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return (datetime.today() + relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
        elif r == 'week':
            return (datetime.today() + relativedelta(days=-1)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-12-31')
        return fields.Date.context_today(self)

    @api.model
    def check_date_to(self, date_to):
        if date_to >= fields.Date.today():
            raise ValidationError(_('Date To should be before today!'))

    @api.model
    def create(self,vals):
        if vals.get('date_to',False):
            self.check_date_to(vals.get('date_to',False))
        res = super(ActualTimesheet, self).create(vals)
        return res

    @api.multi
    def write(self,vals):
        res = super(ActualTimesheet, self).write(vals)
        return res

    def _check_approve_ability(self):
        user = self.env.user
        supervisor_group = self.env.ref('sarangoci_access_right.supervisor_group')
        if supervisor_group in user.groups_id:
            return True
        return False

    @api.onchange('date_to')
    def onchange_date_to(self):
        if self.date_to >= fields.Date.today():
            self.date_to = date.today() - timedelta(1)
            return { 'warning': {
                    'title': _('Invalid Date'),
                    'message': _('You have to select the day before today!'),
                }}

    branch_id   = fields.Many2one('res.branch',string="Branch",required=True)
    date_from   = fields.Date(string='Date From', default=_default_date_from, required=True,
                            index=True, readonly=True, states={'new': [('readonly', False)]})
    date_to     = fields.Date(string='Date To', default=_default_date_to, required=True,
                          index=True, readonly=True, states={'new': [('readonly', False)]})

    timesheet_ids = fields.One2many('actual.timesheet.line', 'branch_sheet_id',string='Timesheet lines',states={'draft': [('readonly', False)],'new': [('readonly', False)]})
    state       = fields.Selection([
                                    ('new', 'New'),
                                    ('draft', 'Open'),
                                    ('confirm', 'Waiting Approval'),
                                    ('done', 'Approved')], default='new', track_visibility='onchange',
                                    string='Status', required=True, readonly=True, index=True,
                                    help=' * The \'Open\' status is used when a user is encoding a new and unconfirmed timesheet. '
                                         '\n* The \'Waiting Approval\' status is used to confirm the timesheet by user. '
                                         '\n* The \'Approved\' status is used when the users timesheet is accepted by his/her senior.')
    canBeApproved = fields.Boolean(compute=_check_approve_ability)
    # type = fields.Selection([('p', 'P'), ('m', 'M'), ('s', 'S'), ('off', 'OFF'), ('sakit', 'SAKIT'), ('ijin', 'IJIN')])
    # start_time = fields.Many2one('branch.timesheet',string='Start time')
    # first_clock_in = fields.Date('First clock in')
    # overtime_hours = fields.Integer('Overtime hours')
    #
    # @api.multi
    # def action_cancel(self):
    #     True
    #
    # @api.multi
    # def action_approve(self):
    #     True

    @api.multi
    def action_timesheet_draft(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse timesheets or reset them to draft.'))
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_timesheet_confirm(self):
        # for sheet in self:
        #     if sheet.employee_id and sheet.employee_id.parent_id and sheet.employee_id.parent_id.user_id:
        #         self.message_subscribe_users(user_ids=[sheet.employee_id.parent_id.user_id.id])
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_timesheet_done(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can approve timesheets.'))
        if self.filtered(lambda sheet: sheet.state != 'confirm'):
            raise UserError(_("Cannot approve a non-submitted timesheet."))
        self.write({'state': 'done'})

class ActualTimesheetLine(models.Model):
    _name = "actual.timesheet.line"



    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    def _check_approve_ability(self):
        user = self.env.user
        supervisor_group = self.env.ref('sarangoci_access_right.supervisor_group')
        if supervisor_group in user.groups_id:
            return True
        return False

    @api.multi
    def write(self, vals):
        print "VALS ",vals
        for record in self:
            if self._context.get('from_cron'):
                if record.ot_edited:
                    del vals['overtime_hours']
            elif 'overtime_hours' in vals.keys():
                vals['ot_edited'] = True
            if not self._context.get('from_cron') and 'attendance_ids' in vals:
                del vals['attendance_ids']

            super(ActualTimesheetLine, record).write(vals)
        return True

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        res = super(ActualTimesheetLine, self).search_read(domain=domain, fields=fields, offset=offset,
                                                      limit=limit, order=order)
        employee_id = date = 0
        for sub_domain in domain:
            if 'employee_id' == sub_domain[0]:
                employee_id = sub_domain[2]
            if 'date' == sub_domain[0]:
                date = sub_domain[2]
        res = res or [{}]
        def datetime_to_hour(ip_datetime):
            if not ip_datetime:
                return 0.0
            ip_datetime = datetime.strptime(ip_datetime, DEFAULT_SERVER_DATETIME_FORMAT)
            return round(ip_datetime.hour + ip_datetime.minute/60.0, 2)

        for result in res:
            if date and employee_id:
                to_date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
                dt = datetime(to_date.year, to_date.month, to_date.day)
                end_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59)
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee_id),
                    ('check_in', '>=', dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                    ('check_in', '<=', end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])

                result['aft_clock_in'] = datetime_to_hour(attendances and attendances[-1].check_in) or 0
                result['aft_clock_out'] = datetime_to_hour(attendances and attendances[-1].check_out) or 0

                result['alt_clock_in'] = datetime_to_hour(attendances and attendances[0].check_in) or 0
                result['alt_clock_out'] = datetime_to_hour(attendances and attendances[0].check_out) or 0

        return res

    @api.model
    def update_overtime(self):
        timesheets = self.env['actual.timesheet'].search([('state', 'in', ['new', 'draft']), ('date_from', '<=', datetime.today()), ('date_to', '>=', datetime.today())])
        print "Timeshetss   ",timesheets
        for timesheet in timesheets:
            employees = list(set(ts.employee_id.id for ts in timesheet.timesheet_ids))
            for employee in employees:
                lines = timesheet.timesheet_ids.filtered(lambda t: t.employee_id.id==employee and \
                    t.date == datetime.today().date().strftime(DEFAULT_SERVER_DATE_FORMAT))
                print "LINES   ",lines
                if not lines:
                    lines = self.create({
                        'employee_id':employee,
                        'branch_sheet_id':timesheet.id,
                        'name': '/',
                        'date': datetime.today(),
                        })
                for line in lines.filtered(lambda l:not l.ot_edited):
                    dt = datetime.strptime(line.date, DEFAULT_SERVER_DATE_FORMAT)
                    dt = datetime(dt.year, dt.month, dt.day)
                    end_dt = datetime(dt.year, dt.month, dt.day, 23, 59)
                    attendances = self.env['hr.attendance'].search([('employee_id', '=', employee), 
                        ('check_in', '>=', dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), 
                        ('check_in', '<=', end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])
                    hours = 0.0
                    minutes = 0.0
                    for attendance in attendances:
                        check_in = datetime.strptime(attendance.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                        check_out = datetime.strptime(attendance.check_out, DEFAULT_SERVER_DATETIME_FORMAT)
                        diff = check_out - check_in
                        hours += int(diff.seconds/3600)
                        minutes += int((diff.seconds/60)%60)
                    overtime = hours + (minutes/60) > 8 and hours + (minutes/60) -8 or 0.0
                    line.with_context(from_cron=True).write({'overtime_hours': overtime, 'attendance_ids': [(6, 0 , attendances.ids)]})

    user_id = fields.Many2one('res.users', string='User', default=_default_user)
    approver_id = fields.Many2one('res.users', string='User')
    employee_id = fields.Many2one('hr.employee','Employee')
    branch_sheet_id = fields.Many2one('actual.timesheet')
    option = fields.Selection([('P', 'P'),
                                ('M', 'M'),
                                ('F', 'F'),
                                ('S', 'S'),
                                ('Off', 'Off'),
                                ('Ijin', 'Ijin'),
                                ('Sakit', 'Sakit'),
                                ('Cuti', 'Cuti'),
                                ('Alpha', 'Alpha'),])

    start_time = fields.Float('Start Time', default=0)
    aft_clock_in = fields.Float('Actual First Time Clock In', compute='_get_actual_timesheet', readonly=True)
    aft_clock_out = fields.Float('Actual First Time Clock Out', compute='_get_actual_timesheet', readonly=True)
    alt_clock_in = fields.Float('Actual Last Time Clock In', compute='_get_actual_timesheet', readonly=True)
    alt_clock_out = fields.Float('Actual Last Time Clock Out', compute='_get_actual_timesheet', readonly=True)
    canBeApproved = fields.Boolean(compute=_check_approve_ability)

    from_hours = fields.Float('From')
    first_clock_in = fields.Float('First Clock In')
    to_hours = fields.Float('To')

    overtime_hours = fields.Float('Overtime')
    overtime_input = fields.Float('Overtime Input')
    date = fields.Date('Date', required=True, index=True, default=fields.Date.context_today)
    name = fields.Char('Name')
    ot_edited = fields.Boolean('Edited?')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    attendance_ids = fields.Many2many('hr.attendance')

    @api.model
    def default_get(self, fields):
        result = super(ActualTimesheetLine, self).default_get(fields)
        user = self.env.user
        supervisor_group = self.env.ref('sarangoci_access_right.supervisor_group')
        result['canBeApproved'] = supervisor_group in user.groups_id
        return result

    @api.model
    def approve_timesheet(self, employee_id, date):
        records = self.search([('date', '=', date), ('employee_id', '=', employee_id)])
        for record in records:
            if not record.approver_id:
                record.approver_id = self.env.context.get('user_id', self.env.user.id)

    @api.multi
    def _get_actual_timesheet(self):
        def datetime_to_hour(ip_datetime):
            if not ip_datetime:
                return 0.0
            ip_datetime = datetime.strptime(ip_datetime, DEFAULT_SERVER_DATETIME_FORMAT)
            return round(ip_datetime.hour + ip_datetime.minute/60.0, 2)
        for sheet in self:
            to_date = datetime.strptime(sheet.date, DEFAULT_SERVER_DATE_FORMAT)
            dt = datetime(to_date.year, to_date.month, to_date.day)
            end_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59)
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', sheet.employee_id.id),
                ('check_in', '>=', dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                ('check_in', '<=', end_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])

            sheet.aft_clock_in = datetime_to_hour(attendances and attendances[-1].check_in) or 0
            sheet.aft_clock_out = datetime_to_hour(attendances and attendances[-1].check_out) or 0

            sheet.alt_clock_in = datetime_to_hour(attendances and attendances[0].check_in) or 0
            sheet.alt_clock_out = datetime_to_hour(attendances and attendances[0].check_out) or 0

class HrLeaveConfigSettings(models.TransientModel):
    _inherit = 'hr.leave.config.settings'

    overtime = fields.Float(string='Overtime')

    @api.model
    def default_get(self, fields):
        res = super(HrLeaveConfigSettings, self).default_get(fields)
        overtime_pole = self.env['hr.leave.config.settings'].search([], limit=1, order='id DESC')
        workingtime_range = overtime_pole and overtime_pole.overtime or 8
        if 'overtime' in fields:
            res['overtime'] = workingtime_range
        return res