# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt.Ltd. (<http://www.serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, ustr

class hr_employee(models.Model):
    
    _inherit = 'hr.employee'

    accommodated = fields.Boolean('Accommodated')
    pub_accommodation_history_ids = fields.One2many('pub.accommodation.history','emp_id','Pub History')
    worker_location_id = fields.Many2one('site.location', string='Worker Location')
    away = fields.Boolean('Away')
    emp_away_history_ids = fields.One2many('emp.away.history','emp_id','Employee Away History')


class beds_beds(models.Model):
    _name = 'beds.beds'

    name = fields.Char('Name', size=240, required=True)
    room_id = fields.Many2one('room.room', 'Room', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', 'Employee Name')

    @api.constrains('employee_id')
    def check_emp(self):
        """
        This constrains is used to check available bed for employee
        --------------------------------------------------------------
        @param self : Records set
        @constrains : The decorator of constrains
        @return: True
        """
        for bed_emp in self:
            bed_emp_ids = bed_emp.employee_id.id
            if not bed_emp_ids:
                break
            bed_ids = self.search([('employee_id', '=', bed_emp_ids)])
            if len(bed_ids) > 1 :
                raise ValidationError(_('Error!'),
                    _("No more bed is available for '%s' ") % \
                            (bed_emp.employee_id.name,))
        return True

class room_room(models.Model):
    _name = 'room.room'

    @api.multi
    def _beds_available(self):
        """
        This method is used to total calculate on available beds of employee
        --------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of multi 
        """
        res = {}
        total_capacity = 0.0
        for rec in self:
            emp_bed = 0.0
            for bed in rec.bed_ids:
                if not bed.employee_id:
                    emp_bed += 1
            rec.available_beds = emp_bed

    name = fields.Char('Name', size=240, required=True)
    bed_ids = fields.One2many('beds.beds', 'room_id', 'Beds')
    available_beds = fields.Integer(string='Available Beds', compute='_beds_available')
    accommodation_id = fields.Many2one('accommodation.accommodation', 'Accommodation', ondelete='cascade')
    visa_quota_ids = fields.One2many('visa.quota', 'room_id', 'Visa Quota', ondelete='cascade')

    @api.multi
    @api.constrains('bed_ids')
    def check_bed_ids(self):
        """
        This constrains used to the maximum capacity, visa quota and
        stay capacity
        -------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of multi
        @constrains : The decorator of constrains
        @return: True
        """
        for rooms_rec in self:
            accomodation_id = rooms_rec.accommodation_id and rooms_rec.accommodation_id.id or False
            if not accomodation_id:
                break
            room_ids = self.search([('accommodation_id', '=', accomodation_id)])
            beds = 0
            for f_room in room_ids:
                beds += len(f_room.bed_ids)
            if beds > rooms_rec.accommodation_id.maximum_capacity:
                raise ValidationError(_("Maximum Capacity Exceeded for room '%s'!") % (rooms_rec.name))
            for bed in rooms_rec.bed_ids:
                if not bed.employee_id:
                    continue
                emp_nation_id = bed.employee_id.emp_country_id and bed.employee_id.emp_country_id.id or False
                visa_ids = self.env['visa.quota'].search([('nationality_id', '=', emp_nation_id), ('room_id', '=', bed.room_id.id)])
                if not visa_ids:
                    raise ValidationError(_("No Visa Quota allocated for '%s' ") % (bed.employee_id.emp_country_id and bed.employee_id.emp_country_id.name or False))
                number_of_quota = 0.0
                if visa_ids.ids:
                    for visa in visa_ids:
                        number_of_quota = visa.quota_available
                if number_of_quota < 0.0:
                    raise ValidationError(_("Visa Quota limit exceed for '%s' ") % \
                        (bed.employee_id.emp_country_id and bed.employee_id.emp_country_id.name or False))
            stay_capacity = rooms_rec.accommodation_id and rooms_rec.accommodation_id.stay_capacity or False
            if stay_capacity < 0:
                raise ValidationError(_("Stay Capacity limit exceed!"))
        return True

class visa_quota(models.Model):
    _name = 'visa.quota'

    @api.multi
    def get_quota_available(self):
        """
        This method used to get total calculate of quota available
        -------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of multi
        """
        res = {}
        for rec in self:
            reserv_bed = 0
            for bed_line in rec.room_id.bed_ids:
                if bed_line.employee_id and bed_line.employee_id.emp_country_id.id\
                and rec.nationality_id.id == bed_line.employee_id.emp_country_id.id:
                    reserv_bed += 1
            res[rec.id] = rec.number_of_quota - reserv_bed
        return res

    _rec_name = 'nationality_id'

    nationality_id = fields.Many2one('res.country', 'Nationality')
    number_of_quota = fields.Integer('Total', size=40, digits=(10, 2))
    quota_available = fields.Integer(string='Available', compute='get_quota_available')
    accommodation_id = fields.Many2one('accommodation.accommodation', 'Accommodation', ondelete='cascade')
    room_id = fields.Many2one('room.room','Room',ondelete='cascade')

    @api.multi
    def unlink(self):
        """
        This method used to delete record if not assigned quota
        ------------------------------------
        @param self : Records set
        @multi : The decorator of multi
        """
        for rec in self:
            if rec.number_of_quota == rec.quota_available:
                return super(visa_quota, self).unlink()
            else:
                raise ValidationError(_('You cannot delete quota that is already assigned. !'))

    @api.multi
    @api.constrains('number_of_quota')
    def check_quota_avail(self):
        """
        This constrains used to check the available quota
        -------------------------------------------------
        @param self : Records set
        @constrains : The decorator of constrains
        @multi : The decorator of multi
        @return: True
        """
        for rec in self:
            room_rec=rec.room_id
            if not rec.room_id:
                break
            acco_ids = self.search([('room_id', '=', room_rec.id)])
            total = 0
            for acco_val in acco_ids:
                total += acco_val.number_of_quota
                if total > acco_val.room_id.available_beds:
                    return False
        return True

class accommodation_accommodation(models.Model):
    _name = 'accommodation.accommodation'

    @api.multi
    def _get_occupied(self):
        """
        This method is used to get total number of count of bed occupy
        --------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of the multi 
        """
        res = {}
        for acc in self:
            bed_occupy = self.env['beds.beds'].search([('room_id.accommodation_id', '=', acc.id), ('employee_id', '!=', False)], count=True)
            acc.occupied = bed_occupy

    @api.multi
    def _get_available(self):
        """
        This method is used to get the total number of count of stay capacity
        ------------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of the multi 
        """
        res = {}
        for acc in self:
            bed_avail = self.env['beds.beds'].search([('room_id.accommodation_id', '=', acc.id), ('employee_id', '=', False)], count=True)
            acc.stay_capacity = bed_avail

    @api.multi
    def _cal_tenure_duration(self):
        """
        This method is used to get the total  month and year on start and end date
        -------------------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of the multi 
        """
        total = 0.0
        res = {}
        for accommodation_rec in self:
            dt_st = accommodation_rec.date_start
            dt_en = accommodation_rec.date_end
            if dt_st and dt_en:
                date1 = datetime.strptime(dt_st, DEFAULT_SERVER_DATE_FORMAT)
                date2 = datetime.strptime(dt_en, DEFAULT_SERVER_DATE_FORMAT)
                r = (date2 - date1)
                days_total = r.days
                years = days_total / 365
                rem_days = days_total % 365
                months = rem_days / 30
                tenure_str = ''
                if years:
                    tenure_str += ustr(years) + " Year(s)"
                if months:
                    if years:
                        tenure_str += " "
                    tenure_str += ustr(months) + " Month(s)"
                accommodation_rec.tenure = tenure_str

    @api.multi
    def cal_total_amount(self):
        """
        This method is used to total calculate on the amount
        -------------------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of the multi 
        """
        total = 0.0
        res = {}
        for amt in self:
            if amt.ser_and_cons or amt.fur_and_fit or amt.other_charges or amt.rent:
                total = float(amt.ser_and_cons) + float(amt.fur_and_fit) + float(amt.other_charges) + float(amt.rent)
                amt.total_amount = total

    @api.multi
    def cal_rent_divide(self):
        """
        This method is used to get the calculate on the rent per pax
        -------------------------------------------------------------------------
        @param self : Records set
        @multi : The decorator of the multi
        """
        res = {}
        for amt in self:
            amount = 0.0
            rent_per_pax = 0.0
            if amt.rent and amt.maximum_capacity:
                amount=round(float(amt.rent) / float(amt.maximum_capacity),2)
                split_amount = str(amount).split('.')
                if split_amount:
                    if int(split_amount[1]) != 0 and int(split_amount[1]) <= 50:
                        rent_per_pax = split_amount[0] + '.50'
                    else:
                        rent_per_pax = round(amount)
                amt.rent_per_pax = rent_per_pax

    accommodation_id = fields.Integer('Accommodation Id')
    active = fields.Boolean('Active', help='The active field which denotes the active accommodation', default=True)
    name = fields.Char('Description', help='Description of Accommodation!')
    land_lord_id = fields.Many2one('res.partner', 'LandLord')
    address_id = fields.Many2one('res.partner', 'Location Address')
    paying_comp_id = fields.Many2one('res.company', 'Tenant')
    rent = fields.Float('Rent', digits=(10, 2))
    rental_pax = fields.Integer('Rental Pax', digits=(5, 2))
    maximum_capacity = fields.Integer('Maximum Capacity', digits=(10, 2))
    stay_capacity = fields.Integer(string='Available', compute='_get_available')
    occupied = fields.Integer(string="Occupied", compute='_get_occupied')
    employee_deduction = fields.Float('Employee Deduction(%)', digits=(10, 2))
    company_deduction = fields.Float('Company Deduction(%)', digits=(10, 2))
    room_ids = fields.One2many('room.room', 'accommodation_id', 'Rooms')
    date_start = fields.Date("Date Start")
    date_end = fields.Date("Date End")
    type = fields.Many2one('accommodation.type' , 'Accommodation Type')
    amenities_ids = fields.Many2many('amenities.amenities', 'rel_amenities', 'acco_amenities', 'amenities_id', 'Amenities')
    security_ids = fields.Many2many('security.security', 'rel_security', 'acco_security', 'security_id', 'Security')
    exclusion_ids = fields.Many2many('amenities.amenities', 'rel_exclusion', 'acco_sid', 'exclusion_id', 'Exclusion')
    payment_term_id = fields.Many2one('account.payment.term', 'Terms of Payment')
    premises = fields.Char('Use of Premises', size=128)
    stamp_fees = fields.Char('Stamp Fees', size=128)
    deposit = fields.Float('Deposit', digits=(10, 2))
    change_of_worker = fields.Integer('Change of Worker', help='Days written notice in advance')
    termination = fields.Integer('Termination', help='Days written notice for termination')
    liabilities = fields.Text('Liabilities')
    tenure = fields.Char(string='Tenure', compute='_cal_tenure_duration')
    rcb_no = fields.Char('RCB NO')
    block_no = fields.Char('Block No')
    ser_and_cons = fields.Float('Service & Conservancy', digits=(10, 2))
    fur_and_fit = fields.Float('Furniture & Fittings', digits=(10, 2))
    other_charges = fields.Float('Other Charges', digits=(10, 2))
    total_amount = fields.Float(string='Total Amount per unit', compute='cal_total_amount')
    agent = fields.Boolean("Agent")
    agent_id = fields.Many2one('res.partner', "Agent Address")
    designation = fields.Char('Designation', size=24)
    ll_responsible = fields.Char('Landlord Responsible', size=32)
    nric_no = fields.Char('NRIC No', size=24)
    ll_witness = fields.Char('Landlord Witness', size=32)
    witness_nric_no = fields.Char('NRIC No', size=24)
    ten_responsible = fields.Char('Tenant Responsible', size=32)
    nric_no_ten = fields.Char('NRIC No', size=24)
    ten_witness = fields.Char('Tenant Witness', size=32)
    witness_nric_no_ten = fields.Char('NRIC No', size=24)
    corres_address = fields.Boolean("Same as Registered Address")
    corress_address_id = fields.Many2one('res.partner', "Correspondence Address")
    admin_fees = fields.Float('Administration Fee')
    reference_no = fields.Char('Reference No')
    history_ids = fields.One2many('accommodation.history', 'accommodation_id', 'Accommodation History')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('expired', 'Expired'), ('waiting', 'Waiting for Renewal'), ('renewed', 'Renewed')], 'State', default='draft')
    visa_quota_ids = fields.One2many('visa.quota', 'accommodation_id', 'Visa Quota', ondelete='cascade')
    pub_history_ids = fields.One2many('pub.history', 'accommodation_id', 'Pub History', ondelete='cascade')
    rent_per_pax = fields.Float(string='Rent Per Pax', compute='cal_rent_divide')

    @api.multi
    def confirm_accommodation(self):
        """
        This method is used to confirm the accommodation
        ------------------------------------------------
        @param self : Records set
        @multi : The decorator of the multi
        @return: True
        """
        self.write({'state':'open'})
        return True

    @api.multi
    def expire_accommodation(self):
        """
        This method is used to expire the accommodation
        ------------------------------------------------
        @param self : Records Set
        @multi : The decorator of the multi
        @return: True
        """
        self.write({'state':'expired'})
        return True

    @api.multi
    def draft_accommodation(self):
        """
        This method is used to set the accommodation as draft
        -----------------------------------------------------
        @param self : Records Set
        @multi : The decorator of the multi
        @return: True
        """
        self.write({'state':'draft'})
        return True

    @api.multi
    def request_renew_accommodation(self):
        """
        This method is used to request the renewal of accommodation
        ------------------------------------------------------------
        @param self : Records Set
        @multi : The decorator of the multi 
        @return: True
        """
        self.write({'state':'waiting'})
        return True

    @api.multi
    def renew_accommodation(self):
        """
        This method is used to request the renewal of accommodation
        ------------------------------------------------------------
        @param self : Records Set
        @multi : The decorator of the multi 
        @return: True
        """
        self.write({'state':'renewed'})
        return True

    @api.multi
    def check_date_format(self, date_start, date_end):
        """
        The method used to compare the between both start and end date 
        -----------------------------------------------
        @param self : Records Set
        @multi : The decorator of the multi 
        @return: Return the dictionary
        """
        res = {}
        if date_start and date_end:
            s_date = datetime.strptime(date_start, DEFAULT_SERVER_DATE_FORMAT)
            e_date = datetime.strptime(date_end, DEFAULT_SERVER_DATE_FORMAT)
            
            if s_date > e_date:
                res.update({'date_start':False , 'date_end':False})
                warning = {
                           'message': _('Start date must be less than end date')
                           }
                return {'value':res, 'warning':warning}
            return res

    @api.multi
    @api.constrains('maximum_capacity')
    def check_maximum_capacity(self):
        """
        The constrains used to validation check on the maximum capacity 
        ---------------------------------------------------------------
        @param self : Records Set
        @constrains : The decorator of the constrains
        @multi : The decorator of the multi 
        @return: True
        """
        for acc in self:
            no_of_beds = 0
            for room in acc.room_ids:
                no_of_beds += len(room.bed_ids)
            no_visa_ids = 0
            for visa in acc.visa_quota_ids:
                no_visa_ids += visa.number_of_quota
            if no_visa_ids > acc.maximum_capacity or no_of_beds > acc.maximum_capacity:
                raise Warning(_('Maximum Capacity Must be greater or equal to number of Beds and number of Visa Quota !'))
        return True

class res_partner(models.Model):
    
    _inherit = 'res.partner'

    landlord = fields.Boolean('Landlord', help='Is this a landlord of a property?')
    location = fields.Boolean('Location', help='Is this address an Accommodation Location?')

class res_company(models.Model):
    
    _inherit = 'res.company'

    tenant = fields.Boolean('Tenant', help='Is this company a tenant or not?')

class amenities_amenities(models.Model):
    _name = "amenities.amenities"
    
    name = fields.Char('Name')
    code = fields.Char('Code')

class security_security(models.Model):
    _name = "security.security"

    name = fields.Char('Name')
    code = fields.Char('Code')
    price = fields.Float('Price')

class accommodation_type(models.Model):
    
    _name = 'accommodation.type'

    name = fields.Char('Name')
    code = fields.Char('Code')


class accommodation_history(models.Model):
    
    _name = 'accommodation.history'
    
    _rec_name = 'bed_id'

    bed_id = fields.Many2one('beds.beds', 'Bed')
    room_id = fields.Many2one('room.room', 'Room')
    accommodation_id = fields.Many2one('accommodation.accommodation', 'Accommodation')
    date = fields.Datetime('Date')
    country_id = fields.Many2one('res.country', 'Country')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    type = fields.Selection([('vacant', 'Vacant'), ('occupy', 'Occupy')], 'Type')

class pub_accommodation_history(models.Model):
    
    _name = 'pub.accommodation.history'

    year_emp = fields.Char('Year')
    emp_id = fields.Many2one('hr.employee', 'Employee')
    date = fields.Date('Date')
    month_emp = fields.Selection([('1', 'Jan'), ('2', 'Feb'),('3', 'Mar'),('4', 'Apr'),('5', 'May'),('6', 'June')
                                                          ,('7', 'July'),('8', 'Aug'),('9', 'Sep'),('10', 'Oct'),('11', 'Nov'),('12', 'Dec')], 'Month')
    rent = fields.Float('Rent')
    pub_amount_emp = fields.Float('Pub Amount')
    accommodation_id = fields.Many2one('accommodation.accommodation', 'Accommodation')

class pub_history(models.Model):
    
    _name = 'pub.history'

    month = fields.Selection([('1', 'Jan'), ('2', 'Feb'),('3', 'Mar'),('4', 'Apr'),('5', 'May'),('6', 'June')
                                                          ,('7', 'July'),('8', 'Aug'),('9', 'Sep'),('10', 'Oct'),('11', 'Nov'),('12', 'Dec')], 'Month')
    year = fields.Char('Year')
    pub_amount = fields.Float('Pub Amount')
    date = fields.Date('Date')
    accommodation_id = fields.Many2one('accommodation.accommodation', 'Accommodation')
    pub_active = fields.Boolean('Active')

    @api.model
    def create(self, vals):
        '''
        The method used to create new record at time check the accommodation state 
        If accommodation state is open or renewed at time Validation error generate. 
        ---------------------------------------------------------------------------
        @param self: Record set
        @multi : The decorator of multi
        @return: True
        '''
        pub_rec = super(pub_history, self).create(vals)
        if not pub_rec.accommodation_id.state == 'open' and 'renewed':
            raise ValidationError(_("Cannot import pub file in  state '%s' for this accommodation")%(pub_rec.accommodation_id.state))
        return pub_rec

    @api.multi
    def divide_pub(self):
        '''
        The method used to when user click on the button while create 
        accommodation history
        ---------------------------------------------------------------------------
        @param self: Record set
        @multi : The decorator of multi
        @return: True
        '''
        emp_list = []
        emp_bed = 0
        for pub_brw in self:
            for acc_rec in pub_brw.accommodation_id:
                for room in acc_rec.room_ids:
                    for bed in room.bed_ids:
                        if bed.employee_id:
                            emp_bed += 1
                            emp_list.append(bed.employee_id.id)
                if emp_bed > 0:
                    for emp in emp_list:
                        amount = pub_brw.pub_amount / emp_bed
                        amt=round(float(amount),2)
                        split_amount = str(amt).split('.')
                        if split_amount:
                            if int(split_amount[1]) != 0 and int(split_amount[1]) <= 50:
                                multiple_amount = split_amount[0] + '.50'
                            else:
                                multiple_amount = round(amount)
                        vals = {'emp_id':emp,'accommodation_id':pub_brw.accommodation_id.id,'rent':acc_rec.rent_per_pax,'pub_amount_emp':multiple_amount,'date':datetime.today()
                                ,'year_emp':str(pub_brw.year),'month_emp':str(int(pub_brw.month))}
                        self.env['pub.accommodation.history'].create(vals)
                        pub_brw.pub_active = True
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
