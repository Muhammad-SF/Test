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
from datetime import datetime
import base64
from odoo import fields, api, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.report import render_report
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class document_type(models.Model):
    _name = 'document.type'
    _description = 'Document Type'

    name = fields.Char('Name', size=64, required=True)


class employee_immigration(models.Model):
    _name = 'employee.immigration'
    _description = 'Employee Immigration'
    _rec_name = 'documents'

    documents = fields.Char("Documents" , size=256, required=True)
    number = fields.Char('Number', size=256)
    employee_id = fields.Many2one('hr.employee', 'Employee Name')
    exp_date = fields.Date('Expiry Date')
    issue_date = fields.Date('Issue Date')
    eligible_status = fields.Char('Eligible Status', size=256)
    issue_by = fields.Many2one('res.country', 'Issue By')
    eligible_review_date = fields.Date('Eligible Review Date')
    doc_type_id = fields.Many2one('document.type', 'Document Type')
    comments = fields.Text("Comments")
    attach_document = fields.Binary('Attach Document')

class hr_education_information(models.Model):
    _name = 'hr.education.information'
    _description = 'Employee Education Information'

    comp_prog_knw = fields.Char('Computer Programs Knowledge', size=64)
    shorthand = fields.Integer('Shorthand')
    course = fields.Char('Courses Taken', size=64)
    typing = fields.Integer('Typing')
    other_know = fields.Char('Other Knowledge & Skills', size=64)
    hr_employee_id = fields.Many2one('hr.employee', 'Employee Id')


class hr_employee(models.Model):
    _inherit = "hr.employee"

    @api.constrains('birthday')
    def _check_employee_birthday(self):
        today = datetime.today()
        for rec in self:
            if rec.birthday:
                born = datetime.strptime(rec.birthday,
                                                  DEFAULT_SERVER_DATE_FORMAT)
                if born > today:
                    raise ValidationError(_('Please enter valid Birthdate.'))

    @api.multi
    def _calculate_age(self, born):
        today = datetime.today()
        try:  # raised when birth date is February 29 and the current year is not a leap year
            birthday = born.replace(year=today.year)
        except ValueError:
            birthday = born.replace(year=today.year, day=born.day - 1)
        if birthday > today:
            return today.year - born.year - 1
        return today.year - born.year

    @api.multi
    @api.depends('birthday')
    def _compute_age(self):
        # now = datetime.now()
        # for record in self:
        #     if record.birthday:
        #         birthday = fields.Datetime.from_string(
        #             record.birthday,
        #         )
        #         delta = relativedelta(now, birthday)
        #         years_months_days = '%d%s' % (
        #             delta.years, _(' Year'),
        #         )
        #     else:
        #         years_months_days = _('No DoB')
        #     record.age = years_months_days
        for records in self:
            age = 0
            age_year = 0
            current_year = datetime.today().year
            if records.birthday:
                birth_year = datetime.strptime(records.birthday, "%Y-%m-%d").year
                age = current_year - birth_year
                age_year = '%d%s' % (
                    age, _(' Year'),
                )
            print("=======================", age)
            records.update({
                'age': age_year
            })

    @api.multi
    def _get_rem_days(self):
        for employee in self:
            if employee.cessation_date and employee.emp_status == 'in_notice':
                from_dt = datetime.strptime(employee.cessation_date, "%Y-%m-%d")
                today = datetime.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d")
                timedelta = from_dt - today
                diff_day = timedelta.days + float(timedelta.seconds) / 86400
                employee.rem_days = diff_day > 0 and round(diff_day) or 0

    @api.multi
    def _get_month(self):
        for emp in self:
            y, m, d = emp.birthday and emp.birthday.split('-') or [0, 0, 0]
            emp.birthday_month = m

    @api.multi
    def _get_date(self):
        for emp in self:
            y, m, d = emp.birthday and emp.birthday.split('-') or [0, 0, 0]
            emp.birthday_day = d

    @api.multi
    def compute_joined_year(self):
        for emp in self:
            difference_in_years = 0
            if emp.join_date:
                start_date = datetime.today()
                end_date = datetime.strptime(emp.join_date, DEFAULT_SERVER_DATE_FORMAT)
                difference_in_years = relativedelta(start_date, end_date).years
                emp.joined_year = difference_in_years + 1

    @api.multi
    def compute_pr_year(self):
        for emp in self:
            difference_in_years = 0
            if emp.pr_date:
                start_date = datetime.today()
                end_date = datetime.strptime(emp.pr_date, DEFAULT_SERVER_DATE_FORMAT)
                difference_in_years = relativedelta(start_date, end_date).years
                emp.pr_year = difference_in_years + 1

    @api.multi
    def compute_emp_status12(self):
        for emp in self:
            print("emp_statusWWWWWWWWW",emp.employment_status12)
            if emp.employment_status123:
                emp.employment_status12 = emp.employment_status123

            
            else:

                contracts = self.env['hr.contract'].search([('employee_id','=',emp.id)])    
                for cont in contracts:
                    if cont.state == 'draft' or cont.state == 'open':  

                        emp.employment_status12 = 'active'


    @api.onchange('active')
    def onchange_emp_active(self):
        vals = {}
        if not self.active:
            vals.update({'emp_status': 'inactive'})
        return {'value' : vals}


    emp_id = fields.Char('Employee ID')
    end_date = fields.Date('End Date')
    cessation_date = fields.Date('Cessation Date')
    job_id = fields.Many2one('hr.job', 'Job', domain="[]")
    parent_id = fields.Many2one('hr.employee', 'Expense Manager')
#    parent_id2 = fields.Many2one('hr.employee', 'Leave Manager')
    leave_manager = fields.Many2one('hr.employee', 'Leave Manager')
    employee_leave_ids = fields.One2many('hr.holidays', 'employee_id', 'Leaves', domain=[('type','=','remove')])
    join_date = fields.Date('Date Joined')
    confirm_date = fields.Date('Date Confirmation')
    history_ids = fields.One2many('employee.history', 'history_id', 'Job History')
    reason = fields.Text('Reason')
    immigration_ids = fields.One2many('employee.immigration', 'employee_id', 'Immigration')
#    parent_user_id = fields.Many2one(related='parent_id.user_id', string="Direct Manager User")
#    parent_user_id2 = fields.Many2one(related='parent_id2.user_id', string="Indirect Manger User")
    last_date = fields.Date('Last Date')
    rem_days = fields.Integer(compute='_get_rem_days', method=True, string='Remaining Days', help="Number of remaining days of his/her employment expire")
    hr_manager = fields.Boolean(string='Hr Manager')
    training_ids = fields.One2many('employee.training', 'tr_id', 'Training')
    birthday_month = fields.Char(compute='_get_month', size=2)
    birthday_day = fields.Char(compute='_get_date', size=2)
    age = fields.Char(compute='_compute_age', string='Age')
    place_of_birth = fields.Char('Place of Birth', size=32)
    issue_date = fields.Date('Passport Issue Date')
    dialect = fields.Char('Dialect', size=32)
    driving_licence = fields.Char('Driving Licence:Class', size=16)
    car = fields.Boolean('Do you own a car?')
    resume = fields.Binary('Resume')
    physical_stability = fields.Boolean('Physical Stability (Yes)')
    physical = fields.Text('Physical Stability Information')
    court_b = fields.Boolean('Court (Yes)')
    court = fields.Char('Court Information', size=256)
    dismissed_b = fields.Boolean('Dismissed (Yes)')
    dismiss = fields.Char('Dismissed Information', size=256)
    bankrupt_b = fields.Boolean('Bankrupt (Yes)')
    bankrupt = fields.Char('Bankrupt Information', size=256)
    about = fields.Text('About Yourself')
    bankrupt_no = fields.Boolean('Bankrupt (No)')
    dismissed_no = fields.Boolean('Dismissed (No)')
    court_no = fields.Boolean('Court (No)')
    physical_stability_no = fields.Boolean('Physical Disability (No)')
    bank_detail_ids = fields.One2many('hr.bank.details', 'bank_emp_id', 'Bank Details')
    # employee_type_id = fields.Many2one('employee.id.type', 'Type Of ID')
    employee_type_id = fields.Selection([('employment_pass', 'Employement Pass'), ('skilled_pass', 'Skilled S Pass'),
                                         ('unskilled_pass', 'Unskilled S Pass'),
                                         ('skilled_work_permit', 'Skilled Work Permit'),
                                         ('unskilled_work_permit', 'Unskilled Work Permit'),
                                         ('dependant_pass', 'Dependant Pass (LOC)'), ('traning_pass', 'Training Pass'),
                                         ('work_holiday_pass', 'Work Holiday Pass'), ('others', 'Others')],
                                        string='Type Of ID')
    emp_country_id = fields.Many2one('res.country', 'Country')
    emp_state_id = fields.Many2one('res.country.state', 'State')
    emp_city_id = fields.Many2one('employee.city', 'City')
    is_daily_notificaiton_email_send = fields.Boolean('Receiving email notifications of employees who are on leave?', default=True)
    is_pending_leave_notificaiton = fields.Boolean('Receiving email notifications of Pending Leaves Notification Email?')
    is_all_final_leave = fields.Boolean('Receiving email notifications of 2nd Reminder to Direct / Indirect Managers?')
    joined_year = fields.Integer(compute='compute_joined_year', string='Joined Year')
    app_date = fields.Date('Application Date', help='The date when the Work Permit was Applied')
    wp_number = fields.Char('Work Permit No')
    education_info_line = fields.One2many('hr.education.information', 'hr_employee_id', 'Education Info Line')
    singaporean = fields.Boolean('Singaporean')
    pr_date = fields.Date('PR Date')
    pr_year = fields.Integer(compute='compute_pr_year', string='PR Year')
    factors = fields.Selection(selection=[('skilled', 'Skilled'),
                                        ('unskilled', 'Unskilled')], string='Factors', default='skilled')
    sectors = fields.Selection(selection=[('service', 'Service'),('manufacturing', 'Manufacturing'),
                                        ('construction', 'Construction'),('process', 'Process'),
                                        ('marine', 'Marine'),('s_pass', 'S Pass')],
                               string='Sectors', default='service')
    type_tiers = fields.Selection(selection=[('basic_tier_1', 'Basic/Tier 1'),('tier_2', 'Tier 2'),
                                            ('tier_3', 'Tier 3'),('mye', 'MYE'),
                                            ('mye-waiver', 'MYE-waiver')], string='Tiers', default='basic_tier_1')
    emp_status = fields.Selection(selection=[('probation', 'Probation'),('active', 'Active'),
                                            ('in_notice', 'In notice Period'),('terminated', 'Terminated'),
                                            ('inactive', 'Inactive'),
                                            ('promoted', 'Promoted')], string='Employment Status', default='active')
    employee_race_id = fields.Many2one(
        comodel_name='employee.race', string='Employee Race',
        help='Employee Race')

    emp_status_new = fields.Many2one('hr.contract.type',string='Employment Type')
    contract_status = fields.Selection([('running', 'Running'),('expired', 'Expired'),('new', 'New'),('to_renew', 'To Renew')],'Contract Status')
    employment_status12 = fields.Selection([('active', 'Active'),('inactive', 'Inactive')],'Employment Status',compute = 'compute_emp_status12')
    employment_status123 = fields.Selection([('active', 'Active'),('inactive', 'Inactive')])
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], groups='hr.group_hr_user',required=True)
    
    def _default_get_cpf_muslim(self):
        return self.env['hr.salary.rule'].sudo().search([('code', '=', 'CPFMBMF')], limit=1)

    # cpf_shg_id = fields.Many2one('hr.salary.rule', string='CPF SHG',
    #     domain=[('race_id.name', '=', 'Muslim')],
    #     default= _default_get_cpf_muslim,
    #     help='Please specify the CPF contribution to the Self-Help Group(SHG).')

    display_cpf_shg = fields.Boolean('Display CPF SHG field?')
    cpf_shg_id = fields.Many2one('hr.salary.rule', string='CPF SHG',
        domain=[('race_id.name', '=', 'Muslim')],
        default= _default_get_cpf_muslim,
        help='Please specify the CPF contribution to the Self-Help Group(SHG).')


# #######################  unused fields

#    inact_date = fields.Datetime('Inactive Date')
#    passport_exp_date = fields.Date('Passport Expiry Date')
#    contact_num2 = fields.Char('Contact:Mobile', size=16)
# #############################

    @api.onchange('employee_race_id')
    def onchange_employee_race_id(self):
        if self.employee_race_id and self.employee_race_id.name == 'Muslim':
            cpfmbmf = self.env['hr.salary.rule'].sudo().search([('code', '=', 'CPFMBMF')])
            self.cpf_shg_id = cpfmbmf and cpfmbmf.id or False
            self.display_cpf_shg = True
        else:
            self.cpf_shg_id = False
            self.display_cpf_shg = False

    @api.onchange('emp_status')
    def onchange_employee_status(self):
        if self.emp_status == 'inactive':
            self.active = False
        if self.emp_status == 'active':
            self.cessation_date = False

    @api.onchange('cessation_date')
    def onchange_employee_cessation_date(self):
        if self.emp_status == 'in_notice':
            contratc_id = self.env['hr.contract'].search([('employee_id','=',self._origin.id)])
            if contratc_id and self.cessation_date:
                contratc_id.write({'date_end':self.cessation_date})

    @api.onchange('physical_stability')
    def onchange_health_yes(self):
        if self.physical_stability == True:
            self.physical_stability_no = False

    @api.onchange('physical_stability_no')
    def onchange_health_no(self):
        if self.physical_stability_no == True:
            self.physical_stability = False

    @api.onchange('court_b')
    def onchange_court_yes(self):
        if self.court_b == True:
            self.court_no = False

    @api.onchange('court_no')
    def onchange_court_no(self):
        if self.court_no == True:
            self.court_b = False

    @api.onchange('dismissed_b')
    def onchange_dismissed_yes(self):
        if self.dismissed_b == True:
            self.dismissed_no = False

    @api.onchange('dismissed_no')
    def onchange_dismissed_no(self):
        if self.dismissed_no == True:
            self.dismissed_b = False

    @api.onchange('bankrupt_b')
    def onchange_bankrupt_yes(self):
        if self.bankrupt_b == True:
            self.bankrupt_no = False

    @api.onchange('bankrupt_no')
    def onchange_bankrupt_no(self):
        if self.bankrupt_no == True:
            self.bankrupt_b = False

    @api.multi
    def copy(self, default={}):
        default = default or {}
        default['employee_leave_ids'] = []
        default['contract_ids'] = []
        return super(hr_employee, self).copy(default)

    @api.multi
    def write(self, vals):
        uid = self.env.uid
        # if vals.get('job_id', '') or vals.get('emp_status', '') or vals.get('join_date', '') or vals.get('confirm_date', ''):
        #     for emp_rec in self:
        #         print("RRRRRRRRRRRRRRR",emp_rec.contract_status)
        #         self.env['employee.history'].create({
        #                                     'job_id': vals.get('job_id', '') or emp_rec.job_id.id,
        #                                     'history_id': emp_rec.id,
        #                                     'user_id': uid,
        #                                     'emp_status' : vals.get('emp_status', emp_rec.emp_status),
        #                                     'contract_status' : vals.get('contract_status', emp_rec.contract_status),
        #                                     'emp_status_new' : vals.get('emp_status_new', emp_rec.emp_status_new.id),
        #                                     'join_date': vals.get('join_date', emp_rec.join_date),
        #                                     'confirm_date': vals.get('confirm_date', emp_rec.confirm_date),
        #                                     'cessation_date': vals.get('cessation_date', emp_rec.cessation_date)
        #                             })
        if 'active' in vals:
            user_ids = []
            for employee in self:
                if employee.user_id:
                    user_ids.append(employee.user_id.id)
            if user_ids:
                user_rec = self.env['res.users'].browse(user_ids)
                user_rec.write({'active': vals.get('active')})
        return super(hr_employee, self).write(vals)

    @api.model
    def create(self, vals):
        employee_id = super(hr_employee, self).create(vals)
        uid = self.env.uid
        # if vals.get('job_id', '') or vals.get('emp_status', '') or vals.get('join_date', '') or vals.get('confirm_date', ''):
        #     self.env['employee.history'].create({
        #                                 'job_id':  vals.get('job_id'),
        #                                 'history_id': employee_id.id,
        #                                 'user_id': uid,
        #                                 'emp_status' : vals.get('emp_status', 'active'),
        #                                 'join_date': vals.get('join_date', False),
        #                                 'confirm_date': vals.get('confirm_date', False),
        #                                 'cessation_date': vals.get('cessation_date', False
        #                         )})
        active = vals.get('active', False)
        if vals.get('user_id') and not active:
            user_rec = self.env['res.users'].browse(vals.get('user_id'))
            user_rec.write({'active' : active})
        return employee_id


class employee_city(models.Model):
    _name = "employee.city"
    _description = 'Employee City'

    name = fields.Char('City Name', size=64, required=True)
    code = fields.Char('City Code', size=64, required=True)
    state_id = fields.Many2one('res.country.state', 'State', required=True)


class hr_bank_details(models.Model):
    _name = 'hr.bank.details'
    _description = 'Employee Bank Details'
    _rec_name = 'bank_name'

    bank_name = fields.Char('Name Of Bank', size=256)
    bank_code = fields.Char('Bank Code', size=256)
    bank_ac_no = fields.Char('Bank Account Number', size=256, required=True)
    bank_emp_id = fields.Many2one('hr.employee', 'Bank Detail')
    branch_code = fields.Char('Branch Code', size=256)
    beneficiary_name = fields.Char('Beneficiary Name', size=256)


class employee_id_type(models.Model):
    _name = 'employee.id.type'
    _description = 'Employee ID Type'

    name = fields.Char("EP", size=256, required=True)
    s_pass = fields.Selection(selection=[('skilled', 'Skilled'),
                                           ('unskilled', 'Un Skilled')], string='S Pass', default='skilled')
    wp = fields.Selection(selection=[('skilled', 'Skilled'),
                                       ('unskilled', 'Un Skilled')], string='Wp', default='skilled')

class employee_training(models.Model):
    _name = 'employee.training'
    _description = 'Employee Training'
    _rec_name = 'tr_title'

    tr_id = fields.Many2one('hr.employee', 'Employee')
    tr_title = fields.Char('Title of Training/Workshop', size=64, required=True)
    tr_institution = fields.Char('Institution', size=64)
    tr_date = fields.Date('Date')
    comments = fields.Text('Comments')
    training_attachment = fields.Binary('Attachment Data')


class employee_history(models.Model):
    _name = 'employee.history'
    _description = 'Employee History'
    _rec_name = 'history_id'

    history_id = fields.Many2one('hr.employee', 'History', required="1")
    job_id = fields.Many2one('hr.job', 'Job title', readonly=True, store=True)
    date_changed = fields.Datetime('Date Changed', readonly=True, default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    user_id = fields.Many2one('res.users', "Changed By", readonly=True)
    emp_status = fields.Selection(selection=[('probation', 'Probation'),('active', 'Active'),
                                   ('in_notice', 'In notice Period'),('terminated', 'Terminated'),
                                   ('inactive', 'Inactive')], string='Employment Status', default='active')
    join_date = fields.Date('Joined Date')
    confirm_date = fields.Date('Date of Confirmation')
    cessation_date = fields.Date('Cessation Date')
    emp_last_status = fields.Selection([('active', 'Active'),('inactive', 'Inactive')], 'Employment history',default='active')
    emp_status_new = fields.Many2one('hr.contract.type',string='Employment Status')
    contract_status = fields.Selection([('running', 'Running'),('expired', 'Expired'),('new', 'New'),('to_renew', 'To Renew')],'Contract Status')

class res_company(models.Model):
    _inherit = 'res.company'

    department_id = fields.Many2one('hr.department', 'Department')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
