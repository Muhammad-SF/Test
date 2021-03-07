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
import math
from datetime import datetime
from odoo import tools
from datetime import date
from dateutil import parser, rrule
from odoo import fields, models, api, _
from odoo.report import render_report
from odoo.exceptions import Warning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta



class hr_holidays(models.Model):
    _inherit = "hr.holidays"

    start_date = fields.Datetime('Start Date', default=lambda *d: time.strftime('%Y-01-01'))
    end_date = fields.Datetime('End Date', default=lambda *d: time.strftime('%Y-12-31'))
    notes = fields.Text('Reasons', readonly=False, states={'validate': [('readonly', True)]})
    state = fields.Selection([('draft', 'New'), ('confirm', 'Waiting Pre-Approval'), ('refuse', 'Refused'),
                              ('validate1', 'Waiting Final Approval'), ('validate', 'Approved'),
                              ('cancel', 'Cancelled')],
                             'State', readonly=True, help='The state is set to \'Draft\', when a holiday request is created.\
        \nThe state is \'Waiting Approval\', when holiday request is confirmed by user.\
        \nThe state is \'Refused\', when holiday request is refused by manager.\
        \nThe state is \'Approved\', when holiday request is approved by manager.')
    rejection = fields.Text('Reason')
    create_date = fields.Datetime('Create Date', readonly=True)
    write_date = fields.Datetime('Write Date', readonly=True)
    day = fields.Char(string='Day')
    carry_forward = fields.Boolean('Carry Forward Leave')

    #    leave_type = fields.Selection([('am', 'AM'), ('pm', 'PM'), ('full', 'FULL')], 'Duration')

    @api.multi
    def get_date(self, date=False):
        '''
        The method used to get the start and end date
        @self : Current Record Set
        @api.multi : The decorator of multi
        @param date: get the date
        @return: Returns the start and end date in dictionary 
        '''
        date_dict = {}
        year = start_date = end_date = False
        if date:
            year = datetime.datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT).year
        start_date = '%s-01-01' % tools.ustr(int(year))
        end_date = '%s-12-31' % tools.ustr(int(year))
        date_dict.update({'start_date': start_date, 'end_date': end_date})
        return date_dict

    @api.multi
    def send_email(self, holiday_id, temp_id, force_send=False):
        '''
           This method sends mail using information given in message
           @self : Current Record Set
           @api.multi : The decorator of multi
           @param int holiday_id : The current object of id
           @param int temp_id: The Email Template of id
           @param bool force_send : if True, the generated mail.
                message is immediately sent after being created,
                as if the scheduler was executed for this message
                only
           -----------------------------------------------------------
        '''
        send_mail = self.env['mail.template'].browse(temp_id).send_mail(holiday_id, force_send=force_send)

    @api.multi
    def get_date_from_range(self, from_date, to_date):
        '''
            Returns list of dates from from_date to to_date
            @self : Current Record Set
            @api.multi : The decorator of multi
            @param from_date: Starting date for range
            @param to_date: Ending date for range
            @return : Returns list of dates from from_date to to_date
            -----------------------------------------------------------
        '''
        dates = []
        if from_date and to_date:
            dates = list(rrule.rrule(rrule.DAILY,
                                     dtstart=parser.parse(from_date),
                                     until=parser.parse(to_date)))
        return dates

    @api.multi
    def _check_holiday_carryforward(self, holiday_id, start_date, end_date):
        '''
        Checks that there is a public holiday,Saturday and Sunday on date of leave
        @self: Current Record Set
        @api.multi: The decorator of multi
        @param int holiday_id: The current object of id
        @param start_date: Starting date for range
        @param end_date: Ending date for range
        @return: Numbers of day
        -----------------------------------------------------------
        '''
        no_of_day = 0.0
        for holiday_rec in self.browse(holiday_id):
            dates = holiday_rec.get_date_from_range(holiday_rec.date_from,
                                                    holiday_rec.date_to)
            dates = [x.strftime('%Y-%m-%d') for x in dates]
            remove_date = []
            data = []
            contract_ids = self.env['hr.contract'].search(
                [('employee_id', '=', self.employee_id.id), ('date_start', '<=', start_date),
                 ('date_end', '>=', end_date)])
            for contract in contract_ids:
                if contract.working_hours and contract.working_hours.attendance_ids:
                    for hol in contract.working_hours.attendance_ids:
                        if hol.dayofweek == '0':
                            data.append(1)
                        if hol.dayofweek == '1':
                            data.append(2)
                        if hol.dayofweek == '2':
                            data.append(3)
                        if hol.dayofweek == '3':
                            data.append(4)
                        if hol.dayofweek == '4':
                            data.append(5)
                        if hol.dayofweek == '5':
                            data.append(6)
                        if hol.dayofweek == '6':
                            data.append(7)
            if contract_ids and contract_ids.ids:
                for day in dates:
                    date = datetime.datetime.strptime(day, DEFAULT_SERVER_DATE_FORMAT).date()
                    if date.isoweekday() not in data:
                        remove_date.append(day)
                for remov in remove_date:
                    if remov in dates:
                        dates.remove(remov)
            public_holiday_ids = self.env['hr.holiday.public'].search([('state', '=', 'validated')])
            for public_holiday_record in public_holiday_ids:
                for holidays in public_holiday_record.holiday_line_ids:
                    if holidays.holiday_date in dates:
                        dates.remove(holidays.holiday_date)
            for day in dates:
                if day >= start_date and day <= end_date:
                    no_of_day += 1
        return no_of_day

    @api.model
    def assign_carry_forward_leave(self):
        '''
        This method will be called by scheduler which will assign 
        carry forward leave on end of the year i.e YYYY/12/31 23:59:59
        @self: Current Record Set
        @api.model: The decorator of model
        @return: True
        -----------------------------------------------------------
        '''
        cr, uid, context = self.env.args
        holiday_ids_lst = []
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = datetime.datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).year
        #        next_year_date = str(year + 1) + '-01-01'
        #        next_yr_date = self.get_date(next_year_date)
        empl_ids = self.env['hr.employee'].search([('active', '=', True)])
        holiday_status_ids = self.env['hr.holidays.status'].search([('cry_frd_leave', '>', 0)])
        current_yr_date = self.get_date(today)
        start_date = current_yr_date.get('start_date', False)
        end_date = current_yr_date.get('end_date', False)
        for holiday in holiday_status_ids:
            for employee in empl_ids:
                if employee.user_id and employee.user_id.id == 1:
                    continue
                add = remove = 0.0
                cr.execute(
                    "SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='add' and start_date >= '%s' and end_date <= '%s'" % (
                    employee.id, holiday.id, start_date, end_date))
                all_datas = cr.fetchone()
                if all_datas and all_datas[0]:
                    add += all_datas[0]
                cr.execute(
                    "SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='remove' and date_from >= '%s' and date_to <= '%s'" % (
                    employee.id, holiday.id, start_date, end_date))
                leave_datas = cr.fetchone()
                if leave_datas and leave_datas[0]:
                    remove += leave_datas[0]
                cr.execute(
                    "SELECT id FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='remove' and date_from >= '%s' and date_to <= '%s'" % (
                    employee.id, holiday.id, start_date, end_date))
                leave_datas = cr.fetchall()
                if leave_datas:
                    for data in leave_datas:
                        if data[0]:
                            remove += self._check_holiday_carryforward(data[0], start_date, end_date)
                final = add - remove
                final = final > holiday.cry_frd_leave and holiday.cry_frd_leave or final
                if final > 0.0:
                    cleave_dict = {
                        'name': 'Default Carry Forward Leave Allocation',
                        'employee_id': employee.id,
                        'holiday_type': 'employee',
                        'holiday_status_id': holiday.id,
                        'number_of_days_temp': final,
                        'type': 'add',
                        'carry_forward': True
                    }
                    new_leave = self.create(cleave_dict)
                    holiday_ids_lst.append(new_leave.id)
        mail_server_ids = self.env['ir.mail_server'].search([])
        if not mail_server_ids:
            raise Warning(_('Mail Error \n No mail outgoing mail server specified!'))
        temp_id = self.env['ir.model.data'].get_object_reference('sg_hr_holiday', 'sg10_email_temp_hr_holiday')[1]
        for holiday_id in holiday_ids_lst:
            res = self.send_email(holiday_id, temp_id, force_send=True)
        return True

    @api.model
    def assign_annual_other_leaves(self):
        '''
        This method will be called by scheduler which will assign
        Annual leave at end of the year i.e YYYY/12/01 00:01:01
        @self: Current Record Set
        @api.model: The decorator of model
        @return: True
        '''
        for holiday in self.env['hr.holidays.status'].search([('default_leave_allocation', '>', 0)]):
            for employee in self.env['hr.employee'].search([('active', '=', True)]):
                if employee.user_id and employee.user_id.id == 1:
                    continue
                leave_dict = {
                    'name': 'Assign Default Allocation.',
                    'employee_id': employee.id,
                    'holiday_type': 'employee',
                    'holiday_status_id': holiday.id,
                    'number_of_days_temp': holiday.default_leave_allocation,
                    'type': 'add',
                }
                rec_holiday = self.create(leave_dict)
        return True

    @api.multi
    def get_work_email(self):
        '''
        The method used to get the employee of work email either user login,
        Which used in carry forward leave email template.
        @self : Current Record Set
        @api.multi : The decorator of multi
        @return : Return the employee of work email either user login
        --------------------------------------------------------------------
        '''
        data_obj = self.env['ir.model.data']
        result_data = data_obj._get_id('hr', 'group_hr_manager')
        model_data = data_obj.browse(result_data)
        group_data = self.env['res.groups'].browse(model_data.res_id)
        user_ids = [user.id for user in group_data.users]
        work_email = []
        for emp in self.env['hr.employee'].search([('user_id', 'in', user_ids)]):
            if not emp.work_email:
                if emp.user_id.login and emp.user_id.login not in work_email:
                    work_email.append(str(user.login))
                else:
                    raise Warning(_(' Warning \n Email must be configured in %s HR manager !') % (emp.name))
            elif emp.work_email not in work_email:
                work_email.append(str(emp.work_email))
        email = ''
        for employee_email in work_email:
            email += employee_email + ','
        return email

    @api.multi
    def get_from_mail(self):
        '''
        The method used to get the from email,Which used in
        carry forward leave email template.
        @self : Current Record Set
        @api.multi : The decorator of model
        @return : Return the from email
        ------------------------------------------------------
        '''
        mail_server_ids = self.env['ir.mail_server'].search([], order="id desc", limit=1)
        if not mail_server_ids:
            raise Warning(_('Mail Error \n No mail outgoing mail server specified!'))
        if mail_server_ids.ids:
            return mail_server_ids.smtp_user or ''

    @api.model
    def get_current_year(self):
        '''
        The method used to get current year,Which used in
        carry forward leave email template.
        @self : Current Record Set
        @api.model : The decorator of model
        @return : Return current year
        ------------------------------------------------------
        '''
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = datetime.datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).year
        return str(year + 1)

    @api.model
    def get_dbname(self):
        '''
        The method used to get the database name
        ------------------------------------------------------
        @self : Current Record Set
        @api.model : The decorator of model
        @return : Return the database name
        '''
        return self._cr.dbname or ''


class hr_holidays_status(models.Model):
    _inherit = "hr.holidays.status"
    _rec_name = 'name2'
    _order = 'name2'

    cry_frd_leave = fields.Float('Carry Forward Leave', help='Maximum number of Leaves to be carry forwarded!')
    name2 = fields.Char('Leave Type', size=64)
    default_leave_allocation = fields.Integer('Default Leave Allocation', default=0.0)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        hr_holiday_rec = self.search([('name2', operator, name)] + args, limit=limit)
        return hr_holiday_rec.name_get()

    @api.multi
    def name_get(self):
        res = []
        if not self._context.get('employee_id'):
            for record in self:
                res.append((record.id, record.name2))
            return res
        for record in self:
            name = record and record.name2 or ''
            if not record.limit:
                name = name + (
                '  (%g remaining out of %g)' % (record.virtual_remaining_leaves or 0.0, record.max_leaves or 0.0))
            res.append((record.id, name))
        return res


class hr_holiday_public(models.Model):
    '''
        This class stores a list of public holidays
    '''
    _name = 'hr.holiday.public'
    _description = 'Public holidays'

    #    @api.constrains('holiday_line_ids')
    #    def _check_holiday_line_year(self):
    #        '''
    #        The method used to Validate duplicate public holidays.
    #        @param self : Object Pointer
    #        @param cr : Database Cursor
    #        @param uid : Current User Id
    #        @param ids : Current object Id
    #        @param context : Standard Dictionary
    #        @return : True or False
    #        ------------------------------------------------------
    #        '''
    #        for holiday in self:
    #            if holiday:
    #                for line in holiday.holiday_line_ids:
    #                    holiday_year=datetime.datetime.strptime(line.holiday_date, DEFAULT_SERVER_DATE_FORMAT).year
    #                    if holiday.name != str(holiday_year):
    #                        raise ValidationError(_('You can not create holidays for different year!'))

    #    @api.constrains('name')
    #    def _check_public_holiday(self):
    #        for rec in self:
    #            pub_holiday_ids = rec.search([('name','=',rec.name)])
    #            if pub_holiday_ids and len(pub_holiday_ids) > 1:
    #                raise ValidationError(_('You can not have multiple public holiday for same year!'))

    name = fields.Char('Holiday', size=128, required=True, help='Name of holiday list',
                       default=lambda *a: time.strftime('%Y'))
    holiday_line_ids = fields.One2many('hr.holiday.lines', 'holiday_id', 'Holidays')
    email_body = fields.Text('Email Body',
                             default='Dear Manager,\n\nKindly find attached \
pdf document containing Public Holiday List.\n\nThanks,')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('validated', 'Validated'), ('refused', 'Refused'), ('cancelled', 'Cancelled'),
                              ], 'State', index=True, readonly=True, default='draft')

    @api.multi
    def setstate_draft(self):
        '''
            Sets state to draft
        '''
        self.write({'state': 'draft'})
        return True

    @api.multi
    def setstate_cancel(self):
        '''
            Sets state to cancelled
        '''
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def setstate_validate(self):
        '''
            Sets state to validated
        '''
        file_name = 'HolidayList'  # Name of report file
        attachments = []
        email_body = ''  # To store email body text specified for each employee
        mail_obj = self.env["ir.mail_server"]
        data_obj = self.env['ir.model.data']
        for self_rec in self:
            mail_server_ids = self.env['ir.mail_server'].search([])
            if mail_server_ids and mail_server_ids.ids:
                mail_server_id = mail_server_ids[0]
                if not self_rec.email_body:
                    raise ValidationError(_('Please specify email body!'))
                result_data = data_obj._get_id('hr', 'group_hr_manager')
                model_data = data_obj.browse(result_data)
                group_data = self.env['res.groups'].browse(model_data.res_id)
                work_email = []
                user_ids = [user.id for user in group_data.users]
                if 1 in user_ids:
                    user_ids.remove(1)
                emp_ids = self.env['hr.employee'
                ].search([('user_id', 'in', user_ids)])
                for emp in emp_ids:
                    if not emp.work_email:
                        if emp.user_id.email and \
                                        emp.user_id.email not in work_email:
                            work_email.append(str(user.email))
                        else:
                            raise ValidationError(_('Email must be configured \
                                    in %s HR manager !') % (emp.name))
                    elif emp.work_email not in work_email:
                        work_email.append(str(emp.work_email))
                if not work_email:
                    raise ValidationError(_('No Hr Manager found!'))
                # Create report. Returns tuple (True,filename) if successfuly
                # executed otherwise (False,exception)
                report_name = 'sg_hr_holiday.employee_public_holiday_report'
                report = self.create_report(report_name, file_name)
                if report[0]:
                    # Inserting file_data into dictionary with file_name as a key
                    attachments.append((file_name, report[1]))
                    email_body = self_rec.email_body
                    specific_email_body = email_body
                    message_app = mail_obj.build_email(
                        email_from=mail_server_id.smtp_user,
                        email_to=work_email,
                        subject='Holiday list',
                        body=specific_email_body or '',
                        body_alternative=specific_email_body or '',
                        email_cc=None,
                        email_bcc=None,
                        reply_to=None,
                        attachments=attachments,
                        references=None,
                        object_id=None,
                        subtype='html',
                        subtype_alternative=None,
                        headers=None)
                    mail_obj.send_email(message=message_app,
                                        mail_server_id=mail_server_id.id)
            self_rec.write({'state': 'validated'})
        return True

    def create_report(self, report_name=False, file_name=False):
        '''
        Creates report from report_name that contains records of res_ids 
        and saves in report directory of module as 
        file_name.
        @param res_ids : List of record ids
        @param report_name : Report name defined in .py file of report
        @param file_name : Name of temporary file to store data
        @return: On success returns tuple (True,filename) 
                 otherwise tuple (False,execeotion)
        '''
        if not report_name or not self._ids:
            return (False, Exception('Report name and Resources \
            ids are required !'))
        try:
            result, format = render_report(self.env.cr, self.env.uid,
                                           self._ids, report_name, {}, {})
        except Exception, e:
            return (False, str(e))
        return (True, result)

    @api.multi
    def setstate_refuse(self):
        '''
            Sets state to refused
        '''
        self.write({'state': 'refused'})
        return True

    @api.multi
    def setstate_confirm(self):
        '''
            Sets state to confirmed
        '''
        if not self.holiday_line_ids:
            raise ValidationError(_('Please add holidays.'))
        self.write({'state': 'confirmed'})
        return True

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state <> 'draft':
                raise Warning(_('Warning! \n You cannot delete a public holiday which is not in draft state !'))
        return super(hr_holiday_public, self).unlink()


class hr_holiday_lines(models.Model):
    '''
       This model stores holiday lines
    '''
    _name = 'hr.holiday.lines'
    _description = 'Holiday Lines'

    name = fields.Char('Reason', size=128, help='Reason for holiday')
    day = fields.Char('Day', size=16, help='Day')
    holiday_id = fields.Many2one('hr.holiday.public', 'Holiday List', help='Holiday list')
    holiday_date = fields.Date('Date', help='Holiday date', required=True)
    value = fields.Char('No of Days')

    @api.model_cr
    def init(self):
        self._cr.execute("SELECT conname FROM pg_constraint where conname = 'hr_holiday_lines_date_uniq'")
        if self._cr.fetchall():
            self._cr.execute('ALTER TABLE hr_holiday_lines DROP CONSTRAINT hr_holiday_lines_date_uniq')
            self._cr.commit()
        return True

    @api.multi
    @api.onchange('holiday_date')
    def onchange_holiday_date(self):
        '''
            This methods returns name of day of holiday_date  
        '''
        for holiday_rec in self:
            holiday_dt = holiday_rec.holiday_date or False
            if holiday_dt:
                daylist = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                parsed_date = parser.parse(holiday_dt)
                day = parsed_date.weekday()
                self.day = daylist[day]

                # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: