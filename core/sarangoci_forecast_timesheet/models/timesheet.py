from odoo import models, fields, api
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError

class BranchTimesheet(models.Model):
    _name = "branch.timesheet"
    _inherit = ['mail.thread','ir.needaction_mixin']

    @api.model
    def create(self, vals):
        if 'employee_id' in vals:
            if not self.env['hr.employee'].browse(vals['employee_id']).user_id:
                raise UserError(_('In order to create a timesheet for this employee, you must link him/her to a user.'))
        res = super(BranchTimesheet, self).create(vals)
        # res.write({'state': 'draft'})
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
            employees = list(set(ts.employee_id.id for ts in timesheet.timesheet_ids))
            for employee in employees:
                start_date = datetime.strptime(timesheet.date_from, DEFAULT_SERVER_DATE_FORMAT).date()
                # start_date = datetime.Date(start_date.)
                end_date = datetime.strptime(timesheet.date_to, DEFAULT_SERVER_DATE_FORMAT).date()
                while start_date <= end_date:
                    lines = timesheet.timesheet_ids.filtered(lambda t: t.employee_id.id==employee and \
                        t.date==start_date.strftime(DEFAULT_SERVER_DATE_FORMAT))
                    if not lines:
                        lines = self.env['branch.timesheet.line'].create({
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

                        overtime = hours + (minutes/60) > 8 and hours + (minutes/60) -8 or 0.0
                        line.with_context(from_cron=True).write({'overtime_hours': overtime, 'attendance_ids': [(6, 0 , attendances.ids)]})
                    start_date +=  relativedelta(days=1)

    def _default_date_from(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        return time.strftime('%Y-%m-%d')
        # if r == 'month':
        #     return time.strftime('%Y-%m-%d')
        # elif r == 'week':
        #     return (datetime.today() + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
        # elif r == 'year':
        #     return time.strftime('%Y-01-01')
        # return fields.Date.context_today(self)

    def _default_date_to(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return (datetime.today() + relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=6)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-12-31')
        return fields.Date.context_today(self)
    #
    # @api.model
    # def check_date_from(self,date_from):
    #     if date_from < fields.Date.today():
    #         raise ValidationError(_('Date From should be from today to after today!'))
    #
    # @api.model
    # def create(self, vals):
    #     if vals.get('date_from',False):
    #         self.check_date_from(vals.get('date_from',False))
    #     res = super(BranchTimesheet, self).create(vals)
    #     return res

    @api.multi
    def write(self,vals):
        res = super(BranchTimesheet, self).write(vals)
        return res

    branch_id   = fields.Many2one('res.branch',string="Branch",required=True)
    date_from   = fields.Date(string='Date From', default=_default_date_from, required=True,
                            index=True, readonly=True, states={'new': [('readonly', False)]})
    date_to     = fields.Date(string='Date To', default=_default_date_to, required=True,
                          index=True, readonly=True, states={'new': [('readonly', False)]})
    timesheet_ids = fields.One2many('branch.timesheet.line', 'branch_sheet_id',string='Timesheet lines',states={'draft': [('readonly', False)],'new': [('readonly', False)]})
    state       = fields.Selection([
                                    ('new', 'New'),
                                    ('draft', 'Open'),
                                    ('confirm', 'Waiting Approval'),
                                    ('done', 'Approved')], default='new', track_visibility='onchange',
                                    string='Status', required=True, readonly=True, index=True,
                                    help=' * The \'Open\' status is used when a user is encoding a new and unconfirmed timesheet. '
                                         '\n* The \'Waiting Approval\' status is used to confirm the timesheet by user. '
                                         '\n* The \'Approved\' status is used when the users timesheet is accepted by his/her senior.')

    @api.multi
    def action_timesheet_draft(self):
        if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
            raise UserError(_('Only an HR Officer or Manager can refuse timesheets or reset them to draft.'))
        # self.write({'state': 'draft'})
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

class BranchTimesheetLine(models.Model):
    _name = "branch.timesheet.line"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

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

            super(BranchTimesheetLine, record).write(vals)
        return True


    @api.model
    def update_overtime(self):
        timesheets = self.env['branch.timesheet'].search([('state', 'in', ['new', 'draft']), ('date_from', '<=', datetime.today()), ('date_to', '>=', datetime.today())])
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
    employee_id = fields.Many2one('hr.employee','Employee')
    branch_sheet_id = fields.Many2one('branch.timesheet')
    option = fields.Selection([('P', 'P'),
                                ('M', 'M'),
                                ('F', 'F'),
                                ('S', 'S'),
                                ('Off', 'Off'),
                                ('Ijin', 'Ijin'),
                                ('Sakit', 'Sakit'),
                                ('Cuti', 'Cuti'),
                                ('Alpha', 'Alpha'),])
    from_hours = fields.Float('From')
    to_hours = fields.Float('To')
    overtime_hours = fields.Float('Overtime')
    date = fields.Date('Date', required=True, index=True, default=fields.Date.context_today)
    name = fields.Char('Name')
    ot_edited = fields.Boolean('Edited?')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    attendance_ids = fields.Many2many('hr.attendance')


class res_branch(models.Model):
    _inherit = 'res.branch'

    def get_list_employee_ids(self):
        users = self.env['res.users'].search([('branch_id', '=', self.id)])
        employees = self.env['hr.employee'].search([('user_id', 'in', users._ids)])
        return employees._ids