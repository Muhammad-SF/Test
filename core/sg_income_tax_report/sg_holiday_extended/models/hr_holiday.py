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
import pytz
import time
import math
from datetime import datetime
from openerp.tools import float_compare
from datetime import date, timedelta
from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning, ValidationError, UserError
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
WEB_LINK_URL = "db=%s&uid=%s&pwd=%s&id=%s&state=%s&action_id=%s"


class hr_holidays(models.Model):

    _inherit = "hr.holidays"
    
    @api.model
    def _get_hr_year(self):
        '''
        The method used to get HR year value.
        @param self : Object Pointer
        @return : id of HR year
        ------------------------------------------------------
        '''
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return self.fetch_hryear(today)
    
    @api.multi
    def fetch_hryear(self, date=False):
        '''
        The method used to fetch HR year value.
        @param self : Object Pointer
        @return : id of HR year
        ------------------------------------------------------
        '''
        if not date:
            date = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        hr_year_obj = self.env['hr.year']
        args = [('date_start', '<=' , date), ('date_stop', '>=', date)]
        hr_year_brw = hr_year_obj.search(args)
        if hr_year_brw and hr_year_brw.ids:
            hr_year_ids = hr_year_brw
        else:
            year = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT).year
            end_date = str(year) + '-12-31'
            start_date = str(year) + '-01-01'
            hr_year_ids = hr_year_obj.create({'date_start': start_date, 'date_stop' : end_date, 'code': str(year), 'name': str(year)})
        return hr_year_ids[0].id

#    unallocated =  fields.Boolean('Unallocation')
    leave_config_id = fields.Many2one('holiday.group.config', related='employee_id.leave_config_id', string='Leave Structure',readonly=True)
    half_day =  fields.Boolean('Half Day')
    am_or_pm = fields.Selection([('AM','AM'),('PM','PM')],'Time')
    leave_type_code = fields.Char("code")
    child_birthdate = fields.Date('Child DOB')
    compassionate_other = fields.Selection([('cr_ill_sib','Critical Illness of Siblings'),('dth_sib','Death of Siblings')], string="Reasons for leave")
    gender =  fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    off_in_lieu_detail = fields.Selection([('gt4','> 4 hrs on weekends /public holidays'),('lt4','< 4 hrs on weekends /public holidays'),('others','Others')], string="Off-in Lieu")
    half_day_related =  fields.Boolean('Half Leave Or Not')
    compassionate_immidiate = fields.Selection([('cr_ill','Critical Illness'),('cr_ill_sc','Critical Illness of spouse/Children'),
                                              ('cr_ill_prn','Critical Illness of parents, Gp,PI-Law'),('dth_sc','Death of spouse/Children'),
                                              ('dth_prn','Death of parents, Gp,PI-Law'),], string="Reasons for leave")
#    earn_date = fields.Date('Leave Date',default=lambda *a: time.strftime('%Y-%m-%d'))
    remainig_days = fields.Float('Remaining Leave Days')
    hr_year_id = fields.Many2one('hr.year','HR Year', default=_get_hr_year)
    leave_expire = fields.Boolean('Leave Expire',help='Leave Expire')
    
    @api.constrains('date_from', 'date_to', 'holiday_status_id')
    def _check_public_holiday_leave(self):
        for rec in self:
            if rec.type == 'remove':
                if rec.holiday_status_id and rec.holiday_status_id.id and rec.holiday_status_id.count_days_by:
                    if rec.holiday_status_id.count_days_by == 'working_days_only':
                        diff_day = rec._check_holiday_to_from_dates(rec.date_from, rec.date_to, rec.employee_id.id)
                        if diff_day == 0:
                            raise ValidationError(_('You are not able to apply leave Request on Holiday.!'))
    
    @api.constrains('state', 'number_of_days_temp','holiday_status_id')
    def _check_holidays(self):
        for holiday in self:
            if holiday.holiday_type != 'employee' or holiday.type != 'remove' or not holiday.employee_id or holiday.holiday_status_id.limit:
                continue
            leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
            if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
              float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                        'Please verify also the leaves waiting for validation.'))

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
                ('holiday_status_id.name','!=','MOL'),
            ]
            nholidays = self.search(domain)
            if nholidays and nholidays.ids:
                if holiday.half_day == True and holiday.type=='remove':
                    for new_holiday in nholidays:
                        if new_holiday.half_day == True:
                            if new_holiday.am_or_pm == holiday.am_or_pm:
                                raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))
                        else:
                            raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))
                else:
                    raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))
#    @api.constrains('employee_id')
#    def _check_cessation_date_for_leave(self):
#        '''
#        The method used to check cessation date before Leave request.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.employee_id and rec.employee_id.cessation_date and rec.date_from and (rec.employee_id.cessation_date < rec.date_from):
#                raise ValidationError(_('You can not request a leave over your cessation date!'))


#===============================================================================
# Earned Leave is not in MOM Functionalities 
#===============================================================================

###    @api.constrains('holiday_status_id')
###    def _check_sg_earn_leave(self):
###        '''
###        The method used to Validate for Earn Type Leave.
###        @param self : Object Pointer
###        @param cr : Database Cursor
###        @param uid : Current User Id
###        @param ids : Current object Id
###        @param context : Standard Dictionary
###        @return : True or False
###        ------------------------------------------------------
###        '''
###        if self._context is None:
###            self._context = {}
###        for rec in self:
###            if rec.type == 'remove' and rec.holiday_status_id and rec.holiday_status_id.id and rec.holiday_status_id.earned_leave == True:
###                from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
###                if datetime.datetime.today().date() <= from_date:
###                    raise ValidationError(_('You are not able to apply advance leave Request for this earned leave!'))

#    @api.constrains('holiday_status_id', 'employee_id','date_from','date_to')
#    def _check_employee_leave(self):
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.pre_approved ==True:
#                from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                qualify_date = from_date - relativedelta(days=rec.holiday_status_id.no_of_days)
#                if qualify_date < datetime.datetime.today().date():
#                    raise ValidationError(_('You have to apply leave before  %d days!' % (rec.holiday_status_id.no_of_days)))
#        return True


#    @api.constrains('holiday_status_id','half_day')
#    def _check_half_day_for_leave(self):
#        '''
#        The method used to Validate for Half Day Type Leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.half_day == True:
#                if rec.holiday_status_id and rec.holiday_status_id.id and rec.holiday_status_id.allow_half_day == False:
#                    raise ValidationError(_('You are not able to send half leave Request for this leave type!'))


#    @api.constrains('holiday_status_id','employee_id')
#    def _check_sg_maternity_leave_16_weeks(self):
#        '''
#        The method used to Validate for Maternity Leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name in ['ML16','ML15','ML8','ML4']:
#                if rec.holiday_status_id.pre_approved == True:
#                    if rec.employee_id and rec.employee_id.id and rec.employee_id.join_date:
#                        if rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True:
#                            joining_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT).date()
#                            qualify_date = joining_date + relativedelta(months=3)
#                            if datetime.datetime.today().date() < qualify_date:
#                                raise ValidationError(_('Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
#                            from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                            two_month_date = from_date - relativedelta(months=2)
#                            if two_month_date < datetime.datetime.today().date():
#                                raise ValidationError(_('Warning! \n Maternity Leave request should be submitted 2 months prior to the requested date.!'))
#                        else:
#                            raise ValidationError(_('Warning! \n Child is not Singapore citizen!'))
#                    else:
#                        raise ValidationError(_('You are not able to apply Request for this Maternity leave!'))


#    @api.constrains('date_from','date_to','hr_year_id')
#    def _check_current_year_leave_req(self):
#        '''
#        The method is used to validate only current year leave request.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        current_year = datetime.datetime.today().date().year
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.id:
#                from_date_year = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date().year
#                to_date_year = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date().year
#                if current_year != from_date_year or current_year != to_date_year:
#                        raise ValidationError(_('You can apply leave Request only for the current year!'))
#                if rec.hr_year_id and rec.hr_year_id.date_start and rec.hr_year_id.date_stop:
#                    if rec.hr_year_id.date_start > rec.date_from or rec.hr_year_id.date_stop < rec.date_to:
#                        raise ValidationError(_('Start date and end date must be related to selected HR year!'))

#    @api.constrains('holiday_status_id','employee_id','date_from','date_to','child_birthdate')
#    def _check_paternity_leave(self):
#        '''
#        The method used to Validate for Paternity Leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        today_date = datetime.datetime.today().date()
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'PL':
#                if rec.holiday_status_id.pre_approved == True:
#                    if not rec.employee_id.dependent_ids:
#                        raise ValidationError(_('No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
#                    depends_ids = self.env['dependents'].search([('employee_id','=',rec.employee_id.id),('birth_date','=',rec.child_birthdate),('relation_ship','in',['son','daughter'])])
#                    if len(depends_ids.ids) == 0:
#                        raise ValidationError(_('No Child found! \n No Child found for the Birth date %s !'%(rec.child_birthdate)))
#                    if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and rec.employee_id.join_date:
#                        joining_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT).date()
#                        qualify_date = joining_date + relativedelta(months=3)
#                        if today_date >= qualify_date:
#                            child_birth_date = datetime.datetime.strptime(rec.child_birthdate, DEFAULT_SERVER_DATE_FORMAT).date()
#                            from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                            to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                            qualify_date = child_birth_date + relativedelta(years=1)
#    #                         child_bd_week = child_birth_date.isocalendar()
#                            sixteen_weeks_later = child_birth_date + relativedelta(weeks=16)
#                            before_qualify_date = from_date - relativedelta(weeks=2)
#                            if to_date > qualify_date:
#                                raise ValidationError(_('Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
#                            if to_date > sixteen_weeks_later:
#                                raise ValidationError(_('Warning! \n Paternity leave should be taken within 16 weeks of the child\'s birth date!'))
#                            if before_qualify_date < today_date:
#                                raise ValidationError(_('Warning! \n Paternity Leave request should be submitted 2 weeks prior to the requested date.!'))
#                        else:
#                            raise ValidationError(_('Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
#                    else:
#                        raise ValidationError(_('Warning! \n Child is not Singapore citizen!'))

#    @api.constrains('holiday_status_id','employee_id','date_to','child_birthdate')
#    def _check_unpaid_infant_care_leave(self):
#        '''
#        The method used to Validate for Unpaid Infant Care Leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        date_rec = []
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'UICL':
#                if rec.holiday_status_id.pre_approved == True:
#                    if not rec.employee_id.dependent_ids:
#                        raise ValidationError(_('No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
#                    depends_ids = self.env['dependents'].search([('employee_id','=',rec.employee_id.id),('birth_date','=',rec.child_birthdate),('relation_ship','in',['son','daughter'])])
#                    if len(depends_ids.ids) == 0:
#                        raise ValidationError(_('No Child found! \n No Child found for the Birth date %s !'%(rec.child_birthdate)))
#                    if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True :
#                        if rec.employee_id.join_date:
#                            joining_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT).date()
#                            qualify_date = joining_date + relativedelta(months=3)
#                            if datetime.datetime.today().date() >= qualify_date:
#                                child_birth_date = datetime.datetime.strptime(rec.child_birthdate, DEFAULT_SERVER_DATE_FORMAT).date()
#                                to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                                qualify_date = child_birth_date + relativedelta(years=2)
#                                if to_date > qualify_date:
#                                    raise ValidationError(_('Warning! \n Child is not Singapore citizen!'))
#                            else:
#                                raise ValidationError(_('Not Qualified in Joining date! \n Employee must have worked in the company for a continuous duration of at least 3 months!'))
#                    else:
#                        raise ValidationError(_('You are not able to apply Request for this Unpaid Infant Care leave!'))

#    @api.constrains('holiday_status_id','employee_id','date_to','child_birthdate')
#    def _check_Paid_child_care_leave(self):
#        '''
#        The method used to Validate for Paid Child Care Leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        today_date = datetime.datetime.today().date()
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'CCL':
#                if rec.holiday_status_id.pre_approved == True:
#                    if not rec.employee_id.dependent_ids:
#                        raise ValidationError(_('No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
#                    depends_ids = self.env['dependents'].search([('employee_id','=',rec.employee_id.id),('birth_date','=',rec.child_birthdate),('relation_ship','in',['son','daughter'])])
#                    if len(depends_ids.ids) == 0:
#                        raise ValidationError(_('No Child found! \n No Child found for the Birth date %s !'%(rec.child_birthdate)))
#                    if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and rec.employee_id.join_date:
#                        joining_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT).date()
#                        qualify_date = joining_date + relativedelta(months=3)
#                        if today_date >= qualify_date:
#                            child_birth_date = datetime.datetime.strptime(rec.child_birthdate, DEFAULT_SERVER_DATE_FORMAT).date()
#                            to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                            qualify_date = child_birth_date + relativedelta(years=7)
#                            if to_date > qualify_date:
#                                raise ValidationError(_('You are not able to apply Request for this Paid Child Care leave!'))
#                        else:
#                            raise ValidationError(_('You are not able to apply Request for this Paid Child Care leave!'))
#                    else:
#                        raise ValidationError(_('You are not able to apply Request for this Paid Child Care leave!'))

#    @api.constrains('holiday_status_id','employee_id','date_to','child_birthdate')
#    def _check_extended_child_care_leave(self):
#        '''
#        The method used to Validate for Extended Child Care Leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self.context = {}
#        date_rec = []
#        today_date = datetime.datetime.today().date()
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'ECL':
#                if rec.holiday_status_id.pre_approved == True:
#                    if not rec.employee_id.dependent_ids:
#                        raise ValidationError(_('No Child Depends found! \n Please Add Child Detail in Depend list for this employee Profile !'))
#                    depends_ids = self.env['dependents'].search([('employee_id','=',rec.employee_id.id),('birth_date','=',rec.child_birthdate),('relation_ship','in',['son','daughter'])])
#                    if len(depends_ids.ids) == 0:
#                        raise ValidationError(_('No Child found! \n No Child found for the Birth date %s !'%(rec.child_birthdate)))
#                    if rec.employee_id and rec.employee_id.id and rec.employee_id.singaporean == True and rec.employee_id.depends_singaporean == True and rec.employee_id.join_date:
#                        joining_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT).date()
#                        qualify_date = joining_date + relativedelta(months=3)
#                        if today_date >= qualify_date:
#                            child_birth_date = datetime.datetime.strptime(rec.child_birthdate, DEFAULT_SERVER_DATE_FORMAT).date()
#                            to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                            qualify_date_from = child_birth_date + relativedelta(years=7)
#                            qualify_date_to = child_birth_date + relativedelta(years=12)
#                            if to_date < qualify_date_from or to_date > qualify_date_to:
#                                raise ValidationError(_('You are not able to apply Request for this Extended Child Care leave!'))
#                        else:
#                            raise ValidationError(_('You are not able to apply Request for this Extended Child Care leave!'))
#                    else:
#                        raise ValidationError(_('You are not able to apply Request for this Extended Child Care leave!'))


#    @api.constrains('number_of_days_temp','holiday_status_id')
#    def check_allocation_holidays(self):
#        '''
#        The method used to Validate for Pro rate type Leaves.
#        @param self : Object Pointer
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self.type == 'remove' and self.holiday_status_id.pro_rate == True:
#            date_today = datetime.datetime.today()
#            default_allocation = self.holiday_status_id.default_leave_allocation
#            leave = remain_month = 0.0
#            join_date = datetime.datetime.strptime(self.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT)
#            after_one_year = join_date + relativedelta(years=1)
#            if date_today < after_one_year:
#                working_months = relativedelta(date_today, join_date)
#                if working_months and working_months.months:
#                    remain_month = working_months.months
#                if default_allocation:
#                    leave = (float(default_allocation) /12) * remain_month
#                    leave = round(leave)
#                if self.number_of_days_temp > leave:
#                    raise ValidationError(_('You can not apply leave more than %s !' % (leave)))

#    @api.constrains('date_from','date_to','holiday_status_id')
#    def _check_imm_compassionate_leave(self):
#        '''
#        The method used to Validate immediate compassionate leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'CL':
#                if rec.holiday_status_id.pre_approved == True:
#                    if rec.number_of_days_temp and rec.number_of_days_temp > 5:
#                        raise ValidationError(_('You are not able to apply leave Request more than 5 Working days For compassionate leave!'))

#    @api.constrains('date_from','date_to','holiday_status_id')
#    def _check_other_compassionate_leave(self):
#        '''
#        The method used to Validate other compassionate leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'CLO':
#                if rec.holiday_status_id.pre_approved == True:
#                    if rec.number_of_days_temp and rec.number_of_days_temp > 3:
#                        raise ValidationError(_('You are not able to apply leave Request more than 3 Working days For compassionate leave!'))

#    @api.constrains('holiday_status_id','date_from','date_to')
#    def _check_off_in_leave(self):
#        '''
#        The method used to Validate other compassionate leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        curr_month = datetime.datetime.today().month
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'OIL':
#                if rec.holiday_status_id.pre_approved == True:
#                    from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).month
#                    to_date = datetime.datetime.strptime(rec.date_to, DEFAULT_SERVER_DATETIME_FORMAT).month
#                    if int(from_date) != int(curr_month) or int(to_date) != int(curr_month):
#                        raise ValidationError(_('You can apply off in leave Request for current month only!'))

#    @api.constrains('holiday_status_id','date_from','date_to','employee_id')
#    def _check_marriage_leave(self):
#        '''
#        The method used to Validate other compassionate leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name in ('MLC','ML'):
#                if rec.holiday_status_id.pre_approved == True:
#                    from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                    qualify_date = from_date - relativedelta(weeks=2)
#                    if qualify_date < datetime.datetime.today().date():
#                        raise ValidationError(_('Marriage Leave request should be submitted 2 weeks prior to the requested date.!'))


#    @api.constrains('holiday_status_id','employee_id','date_from','date_to')
#    def _check_sg_annual_leave(self):
#        '''
#        The method used to Validate annual leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'AL':
#                if rec.holiday_status_id.pre_approved == True:
#                    from_date = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT).date()
#                    qualify_date = from_date - relativedelta(weeks=1)
#                    if qualify_date < datetime.datetime.today().date():
#                        raise UserError(('Annual Leave request should be submitted 1 weeks prior to the requested date.!'))

#    @api.constrains('date_from','date_to')
#    def _check_current_month_leave_req(self):
#        '''
#        The method used to Validate current month leave request.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return: Return the False or True
#        ----------------------------------------------------------
#        '''
#        date_today = datetime.datetime.today()
#        first_day = datetime.datetime(date_today.year, date_today.month, 1, 0, 0, 0)
#        first_date_from = first_day.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.pre_approved:
#                rec_date_from  = datetime.datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
#                rec_date_from1 = rec_date_from.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Singapore'))
#                rec_date_from2 = rec_date_from1.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#                if rec_date_from2 and rec_date_from2 < first_date_from:
#                    raise ValidationError(_('You can apply leave Request only for the current month!'))

#    @api.constrains('holiday_status_id','employee_id','date_from','date_to')
#    def _check_sg_medical_opt_leave(self):
#        '''
#        The method used to Validate medical leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
#        date_today = datetime.datetime.today()
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'MOL':
#                if rec.holiday_status_id.pre_approved == True:
#                    if rec.employee_id.join_date and rec.employee_id.join_date <= today:
#                        join_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT)
#                        one_year_day = join_date + relativedelta(months=12)
#                        three_months = join_date + relativedelta(months=3)
#                        if three_months < date_today and one_year_day > date_today:
#                            med_rmv = 0.0
#                            self._cr.execute("SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d and type='remove'" % (rec.employee_id.id, rec.holiday_status_id.id))
#                            all_datas = self._cr.fetchone()
#                            if all_datas and all_datas[0]:
#                                med_rmv += all_datas[0]
#                            res_date = relativedelta(date_today ,join_date)
#                            tot_month = res_date.months
#                            if tot_month == 3 and med_rmv > 5:
#                                raise ValidationError(_('You can not apply medical leave more than 5 days in 3 months!'))
#                            elif tot_month == 4 and med_rmv > 8:
#                                raise ValidationError(_('You can not apply medical leave more than 8 days in 4 months!'))
#                            elif tot_month == 5 and med_rmv > 11:
#                                raise ValidationError(_('You can not apply medical leave more than 11 days in 5 months!'))
#                            elif tot_month >= 6 and med_rmv > 14:
#                                raise ValidationError(_('You can not apply medical leave more than 14 days in one Year!'))
#                        if three_months > date_today:
#                            raise ValidationError(_('You are not able to apply Medical leave Request.!'))

#    @api.constrains('holiday_status_id','employee_id','date_from','date_to')
#    def _check_sg_hospitalisation_leave(self):
#        '''
#        The method used to Validate hospitalisation leave.
#        @param self : Object Pointer
#        @param cr : Database Cursor
#        @param uid : Current User Id
#        @param ids : Current object Id
#        @param context : Standard Dictionary
#        @return : True or False
#        ------------------------------------------------------
#        '''
#        if self._context is None:
#            self._context = {}
#        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
#        date_today = datetime.datetime.today()
#        for rec in self:
#            if rec.type == 'remove' and rec.holiday_status_id.name == 'HOL':
#                if rec.holiday_status_id.pre_approved == True:
#                    if rec.employee_id.join_date and rec.employee_id.join_date <= today:
#                        join_date = datetime.datetime.strptime(rec.employee_id.join_date, DEFAULT_SERVER_DATE_FORMAT)
#                        one_year_day = join_date + relativedelta(months=12)
#                        three_months = join_date + relativedelta(months=3)
#                        if three_months < date_today and one_year_day > date_today:
#                            med_rmv = 0.0
#                            self._cr.execute("SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and holiday_status_id = %d and type='remove'" % (rec.employee_id.id, rec.holiday_status_id.id))
#                            all_datas = self._cr.fetchone()
#                            if all_datas and all_datas[0]:
#                                med_rmv += all_datas[0]
#                            res_date = relativedelta(date_today ,join_date)
#                            tot_month = res_date.months
#                            if tot_month == 3 and med_rmv > 15:
#                                raise ValidationError(_('You can not apply medical leave more than 15 days in 3 months!'))
#                            elif tot_month == 4 and med_rmv > 30:
#                                raise ValidationError(_('You can not apply medical leave more than 30 days in 4 months!'))
#                            elif tot_month == 5 and med_rmv > 45:
#                                raise ValidationError(_('You can not apply medical leave more than 45 days in 5 months!'))
#                            elif tot_month >= 6 and med_rmv > 60:
#                                raise ValidationError(_('You can not apply medical leave more than 60 days in one Year!'))
#                        if three_months > date_today:
#                                raise ValidationError(_('You are not able to apply Hospitalisation leave Request.!'))

    @api.multi
    def action_validate(self):
        '''
        override holidays_validate method for create hospitalization leave,
        on creation of Medical out patient leave.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param ids : Current object Id
        @param context : Standard Dictionary
        ------------------------------------------------------
        '''
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id.name == "MOL":
                today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
                hr_year_id = self.fetch_hryear(today)
                hos_leave_ids = self.env['hr.holidays.status'].search([('name','=','HOL')])
                emp_leave_ids = []
                if hos_leave_ids and hos_leave_ids.ids:
                    hos_leave_id = hos_leave_ids.ids
                    if rec.employee_id.leave_config_id and rec.employee_id.leave_config_id.holiday_group_config_line_ids and rec.employee_id.leave_config_id.holiday_group_config_line_ids.ids:
#                        emp_leave_ids = rec.employee_id.leave_config_id.holiday_group_config_line_ids.ids
                        for leave in rec.employee_id.leave_config_id.holiday_group_config_line_ids:
                            emp_leave_ids.append(leave.leave_type_id.id)
                        if hos_leave_id[0] in emp_leave_ids:
                            med_leave_dict = {
                                'name' : rec.name or False,
                                'employee_id': rec.employee_id.id,
                                'holiday_type' : 'employee',
                                'holiday_status_id' : hos_leave_id[0],
                                'number_of_days_temp' : rec.number_of_days_temp,
                                'type' : 'remove',
                                'hr_year_id':hr_year_id or False,
                                'state':'validate',
                                'date_from':rec.date_from,
                                'date_to':rec.date_to,
                                'leave_config_id':rec.leave_config_id.id or False
                            }
                            new_holiday_create = self.create(med_leave_dict)
                            new_holiday_create.signal_workflow('validate')
        return super(hr_holidays, self).action_validate()

    @api.multi
    def add_follower(self, employee_id):
        self.uid=SUPERUSER_ID
        employee = self.env['hr.employee'].sudo().browse(employee_id)
        if employee.user_id:
            user_ids = employee.user_id.ids
            if employee.leave_manager and employee.leave_manager.user_id and employee.leave_manager.user_id.id:
                user_ids.append(employee.leave_manager.user_id.id)
            self.message_subscribe_users(user_ids)

    @api.onchange('off_in_lieu_detail')
    def off_in_change(self):
        '''
        when you change Off-in Lieu reason, this method will allow
        alf day or full day accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        ------------------------------------------------------
        @return: Dictionary of values.
        '''
        if self.off_in_lieu_detail:
            if self.off_in_lieu_detail in ('lt4','others'):
                self.half_day = True
                self.half_day_related =True
            elif self.off_in_lieu_detail == 'gt4':
                self.half_day = False
                self.half_day_related =False

    @api.onchange('holiday_status_id','employee_id')
    def on_change_leavetype(self):
        '''
        when you change Leave types, this method will set 
        it's code accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        ------------------------------------------------------
        @return: Dictionary of values.
        '''
        if self.holiday_status_id and self.holiday_status_id.id:
            for rec in self.holiday_status_id:
                self.leave_type_code = rec.name
                self.half_day_related = rec.allow_half_day
                self.half_day = False
                self.remainig_days = rec.remaining_leaves

    @api.onchange('employee_id')
    def onchange_employee(self):
        '''
        when you change employee, this method will set 
        it's leave structures accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        ------------------------------------------------------
        @return: Dictionary of values.
        '''
        result = {}
        leave_type_ids = self.env['hr.holidays.status'].search([])
        self.leave_config_id = False
        self.holiday_status_id = False
        result.update({'domain':{'holiday_status_id':[('id','not in',leave_type_ids.ids)]}})
        if self.employee_id and self.employee_id.id:
            self.department_id = self.employee_id.department_id
            if self.employee_id.gender:
                self.gender = self.employee_id.gender
            if self.employee_id.leave_config_id and self.employee_id.leave_config_id.id:
                self.leave_config_id = self.employee_id.leave_config_id.id
                if self.employee_id.leave_config_id.holiday_group_config_line_ids and self.employee_id.leave_config_id.holiday_group_config_line_ids.ids:
                    leave_type_list = []
                    for leave_type in self.employee_id.leave_config_id.holiday_group_config_line_ids:
                        leave_type_list.append(leave_type.leave_type_id.id)
                        result['domain'] = {'holiday_status_id':[('id','in',leave_type_list)]}
            else:
                return {'warning': {'title': 'Leave Warning', 'message': 'No Leave Structure Found! \n Please configure leave structure for current employee from employee\'s profile!'},
                        'domain':result['domain']}
        return result

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
        contract_ids = self.env['hr.contract'].search([('employee_id','=',employee_id),('date_start','<=',start_date),('date_end','>=',end_date)])
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
        for day in dates:
            date = datetime.strptime(day,DEFAULT_SERVER_DATE_FORMAT).date()
            if contract_ids and contract_ids.ids:
                if date.isoweekday() not in data:
                    remove_date.append(day)
            else:
                if date.isoweekday() in [6,7]:
                    remove_date.append(day)
        for remov in remove_date:
            if remov in dates:
                dates.remove(remov)
        date_f = datetime.strptime(start_date,DEFAULT_SERVER_DATETIME_FORMAT).date()
        calendar = date_f.isocalendar()
        public_holiday_ids = self.env['hr.holiday.public'].search([('state', '=', 'validated'),
                                                                   ('name', '=', calendar[0])])
        if public_holiday_ids and public_holiday_ids.ids:
            for public_holiday_record in public_holiday_ids:
                for holidays in public_holiday_record.holiday_line_ids:
                    if holidays.holiday_date in dates:
                        dates.remove(holidays.holiday_date)
        no_of_day = 0.0
        start_date1 = datetime.strptime(start_date,DEFAULT_SERVER_DATETIME_FORMAT).date().strftime(DEFAULT_SERVER_DATE_FORMAT)
        end_date1 = datetime.strptime(end_date,DEFAULT_SERVER_DATETIME_FORMAT).date().strftime(DEFAULT_SERVER_DATE_FORMAT)
        for day in dates:
            if day >= start_date1 and day <= end_date1:
                no_of_day += 1
        return no_of_day


    @api.model
    def create(self, vals):
        '''
            Overrides orm create method to avoid automatic logging of creation.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param vals: dictionary of new values to be set
        @param context: A standard dictionary
        ------------------------------------------------------
        @return: newly created id.
        '''
        if self._context is None:
            self._context = {}
        type_add = False
        type_remove = False
        if 'type' in vals and vals['type'] =='add':
            type_add = True
        if 'date_to' in vals and 'date_from' in vals and 'type' in vals and vals['type'] =='remove':
            least_date = self.onchange_date_to(date_from=vals['date_from'], date_to=vals['date_to'],half_day=False,holiday_status_id=vals['holiday_status_id'],employee_id=vals['employee_id'])
            if least_date.has_key('value'):
                vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
        if 'half_day' in vals and vals['half_day'] ==True and 'type' in vals and vals['type'] =='remove':
            if 'date_from' in vals:
                date_to_with_delta = datetime.strptime(vals['date_from'], DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
                vals.update({'date_to': date_to_with_delta,'number_of_days_temp':0.50})
        res = super(hr_holidays, self).create(vals)
        if type_add == True:
            res.action_approve()
        return res 

    @api.multi
    def write(self,vals):
        '''
            Overrides orm write method for set number of leave days accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        @param vals: dictionary of new values to be set
        @param context: A standard dictionary
        ------------------------------------------------------
        @return: True/False.
        '''
        for rec in self:
            if 'half_day' not in vals and rec.half_day == False:
                if 'holiday_status_id' in vals and vals['holiday_status_id']!= False:
                    leave_type_id = vals['holiday_status_id']
                else:
                    leave_type_id = rec.holiday_status_id.id
                if 'date_from' in vals and 'date_to' not in vals:
                    least_date = self.onchange_date_from(date_from=vals['date_from'], date_to=rec.date_to,half_day=False, holiday_status_id=leave_type_id, employee_id=rec.employee_id.id)
                    vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
                elif 'date_to' in vals and 'date_from' not in vals:
                    least_date = self.onchange_date_to(date_from=rec.date_from, date_to=vals['date_to'], half_day=False,holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
                    vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
                elif 'date_to' in vals and 'date_from' in vals:
                    least_date = self.onchange_date_to(date_from=vals['date_from'], date_to=vals['date_to'], half_day=False,holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
                    vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
            elif 'half_day' not in vals and rec.half_day == True:
                if 'date_from' in vals:
                    date_to_with_delta = datetime.strptime(vals['date_from'], DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
                    vals.update({'date_to': date_to_with_delta,'number_of_days_temp':0.50})
            elif 'half_day' in vals:
                if vals['half_day'] ==True:
                    if 'date_from' in vals :
                        date_to_with_delta = datetime.strptime(vals['date_from'], DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
                        vals.update({'date_to': date_to_with_delta,'number_of_days_temp':0.50})
                    elif 'date_from' not in vals and 'date_to' not in vals:
                        date_to_with_delta = datetime.strptime(rec.date_from, DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
                        vals.update({'date_to': date_to_with_delta,'number_of_days_temp':0.50})
                if vals['half_day'] ==False:
                    if 'holiday_status_id' in vals and vals['holiday_status_id']!= False:
                        leave_type_id = vals['holiday_status_id']
                    else:
                        leave_type_id = rec.holiday_status_id.id
                    if 'date_from' not in vals and 'date_to' not in vals:
                        least_date = self.onchange_date_from(date_from=rec.date_from, date_to=rec.date_to,half_day=False, holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
                        vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
#                    if 'date_from' in vals:
#                        if 'holiday_status_id' in vals and vals['holiday_status_id']!= False:
#                            leave_type_id = vals['holiday_status_id']
#                        else:
#                            leave_type_id = rec.holiday_status_id.id
#                        least_date = self.onchange_date_from(date_from=vals['date_from'], date_to=rec.date_to,half_day=False, holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
#                        vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
#                    if 'date_to' in vals:
#                        if 'holiday_status_id' in vals and vals['holiday_status_id']!= False:
#                            leave_type_id = vals['holiday_status_id']
#                        else:
#                            leave_type_id = rec.holiday_status_id.id
#                        least_date = self.onchange_date_to(date_from=rec.date_from, date_to=vals['date_to'],half_day=False,holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
#                        vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
                    if 'date_from' in vals and 'date_to' not in vals:
                        least_date = self.onchange_date_from(date_from=vals['date_from'], date_to=rec.date_to,half_day=False, holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
                        vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
                    elif 'date_to' in vals and 'date_from' not in vals:
                        least_date = self.onchange_date_to(date_from=rec.date_from, date_to=vals['date_to'],half_day=False,holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
                        vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
                    elif 'date_to' in vals and 'date_from' in vals:
                        least_date = self.onchange_date_to(date_from=vals['date_from'], date_to=vals['date_to'],half_day=False,holiday_status_id=leave_type_id,employee_id=rec.employee_id.id)
                        vals.update({'number_of_days_temp':least_date['value']['number_of_days_temp']})
        return super(hr_holidays, self).write(vals)

    def _get_number_of_daystmp(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""
        from_dt = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
        to_dt = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day = timedelta.days + float(timedelta.seconds) / 86400
        return diff_day

    @api.onchange('half_day', 'date_from', 'date_to', 'holiday_status_id', 'employee_id')
    def onchange_date_from(self,date_from=False, date_to=False,half_day=False, holiday_status_id=False, employee_id=False):
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
                raise UserError(_('Warning!\nThe start date must be anterior to the end date.'))
            elif (date_from and date_to) and half_day == True:
                date_to = date_from
            result = {'value': {}}
            if date_from and not date_to:
                date_to_with_delta = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
                result['value']['date_to'] = str(date_to_with_delta)
            if (date_to and date_from) and (date_from <= date_to):
                if leave_day_count != False and leave_day_count == 'working_days_only':
                    diff_day = self._check_holiday_to_from_dates(date_from, date_to, employee_id)
                    result['value']['number_of_days_temp'] = round(math.floor(diff_day))
                else:
                    diff_day = self._get_number_of_daystmp(date_from, date_to)
                    result['value']['number_of_days_temp'] = round(math.floor(diff_day))+1
            else:
                result['value']['number_of_days_temp'] = 0
            if date_from and date_to and half_day == True:
                date_to_with_delta = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
                result['value']['date_to'] = str(date_to_with_delta)
            if half_day == True:
                result['value']['number_of_days_temp'] = 0.5
            if self.date_from:
                self.hr_year_id = self.fetch_hryear(date_from)
            if rec.holiday_status_id:
                rec.holiday_status_id.write({'hr_year_id': self.fetch_hryear(date_from)})
            return result

    @api.onchange('half_day', 'date_from', 'date_to', 'holiday_status_id', 'employee_id')
    def onchange_date_to(self,date_from=False, date_to=False,half_day=False, holiday_status_id=False, employee_id=False):
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
                result['value']['number_of_days_temp'] = round(math.floor(diff_day))
            else:
                diff_day = self._get_number_of_daystmp(date_from, date_to)
                result['value']['number_of_days_temp'] = round(math.floor(diff_day))+1
        else:
            result['value']['number_of_days_temp'] = 0
        if half_day == True:
            result['value']['number_of_days_temp'] = 0.5
        return result
    
    @api.onchange('hr_year_id')
    def onchange_hr_year_id(self):
        holiday = self.env['hr.holidays.status'].search([('name','=','AL')])
        holiday.write({'hr_year_id': self.hr_year_id.id})
        if self.holiday_status_id:
            self.holiday_status_id.write({'hr_year_id': self.hr_year_id.id})
            
    @api.onchange('half_day', 'date_from', 'holiday_status_id','employee_id')
    def onchange_half_day(self):
        '''
        when you change half day boolean field, this method will set 
        leave type, from date and to dates accordingly.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IDs
        ------------------------------------------------------
        @return: Dictionary of values.
        '''
        if self.half_day == True:
            if self.date_from != False:
                date_to_with_delta = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=4)
                self.date_to = str(date_to_with_delta)
                self.number_of_days_temp = 0.50
            else:
                self.date_to = self.date_from
                self.number_of_days_temp = 0.50
        else:
            result = self.onchange_date_to(date_from=self.date_from, date_to=self.date_to,half_day=False,holiday_status_id=self.holiday_status_id.id,employee_id=self.employee_id.id)
            if self.date_from:
                df = datetime.strptime(self.date_from, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(hours=8)
                self.date_to = df
            self.number_of_days_temp = result['value']['number_of_days_temp']
            self.am_or_pm = False

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
        date_today = datetime.today()
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        curr_hr_year_id = self.fetch_hryear(today)
        year = datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).year
        curr_year_date = str(date_today.year) + '-01-01'
        curr_year_date = datetime.strptime(curr_year_date, DEFAULT_SERVER_DATE_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
        holiday_status_ids = self.env['hr.holidays.status'].search([('default_leave_allocation', '>', 0)])
        empl_ids = self.env['hr.employee'].search([('active','=', True),('leave_config_id','!=', False)])
#        for holiday in holiday_status_ids:
        leave_rec = []
        for employee in empl_ids:
            for holiday in employee.leave_config_id.holiday_group_config_line_ids:
                tot_allocation_leave = holiday.default_leave_allocation
                if tot_allocation_leave > 0:
                    if employee.user_id and employee.user_id.id == 1:
                        continue
                    add = 0.0
                    self.env.cr.execute("SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='add' and hr_year_id=%d" % (employee.id, holiday.leave_type_id.id, curr_hr_year_id))
                    all_datas = self._cr.fetchone()
                    if all_datas and all_datas[0]:
                        add += all_datas[0]
                    if add > 0.0:
                        continue
                    if holiday.leave_type_id.name == 'AL' and employee.join_date > curr_year_date:
                        join_month = datetime.strptime(employee.join_date, DEFAULT_SERVER_DATE_FORMAT).month
                        remaining_months = 12 - int(join_month)
                        if remaining_months:
                            tot_allocation_leave = (float(tot_allocation_leave) /12) * remaining_months
                            tot_allocation_leave = round(tot_allocation_leave)
                    if holiday.leave_type_id.name in ['PL','SPL'] and employee.gender != 'male':
                        continue
                    if holiday.leave_type_id.name == 'PCL' and employee.singaporean != True:
                        continue
                    if employee.leave_config_id.holiday_group_config_line_ids and employee.leave_config_id.holiday_group_config_line_ids.ids:
                        for leave in employee.leave_config_id.holiday_group_config_line_ids:
                            leave_rec.append(leave.leave_type_id.id)
                        if employee.leave_config_id.holiday_group_config_line_ids:
                            if holiday.leave_type_id.name == 'AL' and employee.join_date < curr_year_date:
                                join_year = datetime.strptime(employee.join_date, DEFAULT_SERVER_DATE_FORMAT).year
                                tot_year = year - join_year
                                if holiday.incr_leave_per_year != 0 and tot_year != 0:
                                    tot_allocation_leave += (holiday.incr_leave_per_year * tot_year)
                            if holiday.max_leave_kept != 0 and tot_allocation_leave > holiday.max_leave_kept:
                                tot_allocation_leave = holiday.max_leave_kept
                            leave_dict = {
                                'name' : 'Assign Default ' + str(holiday.leave_type_id.name2),
                                'employee_id': employee.id,
                                'holiday_type' : 'employee',
                                'holiday_status_id' : holiday.leave_type_id.id,
                                'number_of_days_temp' :tot_allocation_leave,
                                'type' : 'add',
                                'hr_year_id': curr_hr_year_id or False,
                                }
                            leave_id = self.create(leave_dict)
        return True

    @api.model
    def assign_carry_forward_leave(self):
        '''
        This method will be called by scheduler which will assign 
        carry forward leave on end of the year.
        @param self : Object Pointer
        @param cr : Database Cursor
        @param uid : Current User Id
        @param context : Standard Dictionary
        @return: Return the True
        --------------------------------------------------------------------------
        '''
        today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        year = datetime.strptime(today, DEFAULT_SERVER_DATE_FORMAT).year
        prev_year_date = str(year - 1) + '-01-01'
        empl_ids = self.env['hr.employee'].search([('active','=', True),('leave_config_id','!=', False)])
        holiday_status_ids = self.env['hr.holidays.status'].search([])
        hr_year_id = self.fetch_hryear(prev_year_date)
        current_hr_year_id = self.fetch_hryear(today)
        hr_year_rec = self.env['hr.year'].browse(hr_year_id)
        start_date = hr_year_rec.date_start
        end_date = hr_year_rec.date_stop
        holiday_ids_lst = []
#        for holiday in holiday_status_ids:
        for employee in empl_ids:
            for holiday in employee.leave_config_id.holiday_group_config_line_ids:
                if employee.user_id and employee.user_id.id == 1:
                    continue
                if employee.join_date and holiday.leave_type_id.number_of_year > 0:
                    joining_date = datetime.strptime(employee.join_date, DEFAULT_SERVER_DATE_FORMAT).date()
                    qualify_date = joining_date + relativedelta(years=int(holiday.leave_type_id.number_of_year))
                    if datetime.today().date() < qualify_date:
                        continue
                add = 0.0
                remove = 0.0
                self._cr.execute("SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='add' and hr_year_id=%d" % (employee.id, holiday.leave_type_id.id, hr_year_id))
                all_datas = self._cr.fetchone()
                if all_datas and all_datas[0]:
                    add += all_datas[0]
                self._cr.execute("SELECT sum(number_of_days_temp) FROM hr_holidays where employee_id=%d and state='validate' and holiday_status_id = %d and type='remove' and date_from >= '%s' and date_to <= '%s'" % (employee.id, holiday.leave_type_id.id, start_date, end_date))
                leave_datas = self._cr.fetchone()
                if leave_datas and leave_datas[0]:
                    remove += leave_datas[0]
                final = add - remove
                if holiday.carryover == 'none':
                    final = 0
                elif holiday.carryover == 'up_to':
                    if float(add/2) > final:
                        final = final
                    elif float(add/2) < final:
                        final = float(add/2)
                    final = final
                elif holiday.carryover == 'unlimited':
                    final = final
                elif holiday.carryover == 'no_of_days':
                    if holiday.carry_no_of_days > final:
                        final = final
                    else:
                        final = holiday.carry_no_of_days
                else:
                    final = 0
                if final > 0.0:
                    cleave_dict = {
                        'name' : 'Default Carry Forward Leave Allocation',
                        'employee_id': employee.id,
                        'holiday_type' : 'employee',
                        'holiday_status_id' : holiday.leave_type_id.id,
                        'number_of_days_temp' : final,
                        'type' : 'add',
                        'hr_year_id' : current_hr_year_id,
                        'carry_forward' : True
                        }
                    new_holiday_rec = self.create(cleave_dict)
                    holiday_ids_lst.append(new_holiday_rec.id)
        temp_id = self.env['ir.model.data'].get_object_reference('sg_hr_holiday', 'sg10_email_temp_hr_holiday')[1]
        for holiday_id in holiday_ids_lst:
            self.send_email(holiday_id, temp_id, force_send=True)
        return True


class hr_holidays_status(models.Model):

    _inherit = "hr.holidays.status"
    _rec_name='name2'
    _order='name2'

    paid_leave = fields.Boolean("Paid Leave",help="Checked if leave type is paid.")
    allow_half_day = fields.Boolean("Allow half day", help="If checked, system allows the employee to take half day leave for this leave type")
    carryover = fields.Selection([('none','None'),('up_to','50% of Entitlement'),('unlimited','Unlimited'),('no_of_days', 'Number of Days')], string="Carryover",help="Select way of carry forward leaves allocation",default='none')
    pro_rate = fields.Boolean("Pro-rate",help="If checked, system allows the employee to take leaves on pro rated basis.")
    count_days_by = fields.Selection([('calendar_day','Calendar Days'),('working_days_only','Working Days only')], string="Count Days By",
                                     help="If Calendar Days : system will counts all calendar days in leave request. \nIf Working Days only : system will counts all days except public and weekly holidays in leave request. ",default='calendar_day')
    earned_leave = fields.Boolean("Earned Leave")
    max_leave_kept =  fields.Integer('Maximum Leave Kept',help="Configure Maximum Number of Leaves to be allocated for this leave type.")
    incr_leave_per_year = fields.Integer('Increment Number of Leave Per Year',help="Configure Number of Leave which auto increments in leave allocation per year.")
    number_of_year = fields.Integer('Number of Year After Carry Forward Allocate', help="Configure Number of year after which carry forward leaves will be allocated.Put O (Zero) if allocation of carry forward from joining")
    pre_approved = fields.Boolean("Pre Approved")
    carry_no_of_days = fields.Float("Number of Days")
    no_of_days = fields.Float("Number of Days")
    hr_year_id = fields.Many2one('hr.year','HR Year')