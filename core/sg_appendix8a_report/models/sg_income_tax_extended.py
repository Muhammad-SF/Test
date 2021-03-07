# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
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
from datetime import datetime,date
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class hr_contract_income_tax(models.Model):

    _inherit = 'hr.contract.income.tax'
    
    @api.multi
    @api.depends('furniture_value_indicator','annual_value')
    def _get_furniture_value(self):
        for rec in self:
            fur_value = 0.0
            if rec.furniture_value_indicator == 'P':
                fur_value = rec.annual_value * 0.40 
            elif rec.furniture_value_indicator == 'F':
                fur_value = rec.annual_value * 0.50
            rec.furniture_value = fur_value

    @api.multi
    @api.depends('total_taxable_value','taxalble_value_of_utilities_housekeeping','taxable_value_of_hotel_acco',
                 'cost_of_home_leave_benefits','interest_payment','insurance_payment','free_holidays','edu_expenses',
                 'non_monetary_awards','entrance_fees','gains_from_assets','cost_of_motor','car_benefits','non_monetary_benefits')
    def get_total_value_of_benefits(self):
        for rec in self:
            total=0.0
            total = rec.total_taxable_value + rec.taxalble_value_of_utilities_housekeeping \
            + rec.taxable_value_of_hotel_acco + rec.cost_of_home_leave_benefits \
            + rec.interest_payment  + rec.insurance_payment  + rec.free_holidays + \
            + rec.edu_expenses + rec.non_monetary_awards + rec.entrance_fees + rec.gains_from_assets \
            + rec.cost_of_motor + rec.car_benefits + rec.non_monetary_benefits
            rec.total_value_of_benefits = total
            
    @api.multi
    @api.depends('actual_hotel_accommodation','employee_paid_amount')
    def _get_hotel_acco(self):
        for rec in self:
            rec.taxable_value_of_hotel_acco = rec.actual_hotel_accommodation - rec.employee_paid_amount

    @api.multi
    @api.depends('utilities_misc_value','driver_value','employer_paid_amount')
    def get_taxable_value_utilities(self):
        for rec in self:
            rec.taxalble_value_of_utilities_housekeeping = rec.utilities_misc_value + rec.driver_value + rec.employer_paid_amount

    @api.multi
    @api.depends('place_of_residence_taxable_value','total_rent_paid')
    def _get_total_taxable_value(self):
        for rec in self:
            rec.total_taxable_value = (rec.place_of_residence_taxable_value - rec.total_rent_paid) 

    @api.multi
    @api.depends('annual_value','furniture_value','rent_landloard')
    def _get_residence_taxable_values(self):
        for rec in self:
            rec.place_of_residence_taxable_value = (rec.annual_value + rec.furniture_value) or rec.rent_landloard

    @api.depends('from_date', 'to_date')
    def get_no_of_days(self):
        """ Return the number of days"""
        for record in self:
            if record.from_date and record.to_date:
                start_date = datetime.strptime(record.from_date, DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.strptime(record.to_date, DEFAULT_SERVER_DATE_FORMAT)
                if start_date > end_date:
                    raise ValidationError(_("Please select valid date!"))
                diff = end_date - start_date
                noofday = str(diff.days)
                record.no_of_days = int(noofday) + 1

     #---------------------------
        #    Appendix 8A Fields
        #---------------------------
    address = fields.Text("Address:")
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    no_of_days = fields.Integer(compute='get_no_of_days', string="No. of days:", store=True)
    no_of_emp = fields.Integer("Number of employee(s) sharing the premises (exclude family members who are not employees):")
    annual_value = fields.Float("a) Annual Value (AV) of Premises for the period provided (state apportioned amount, if applicable)")
    furniture_value_indicator =  fields.Selection([('P', 'Partially furnished'), ('F', 'Fully furnished')], string='b).Furniture & Fitting Indicator')
    rent_landloard = fields.Float("C).Rent paid to landlord including rental of Furniture & Fittings")
    total_rent_paid = fields.Float("e).Total Rent paid by employee for Place of Residence")
    utilities_misc_value = fields.Float("g).Utilities/Telephone/Pager/Suitcase/Golf Bag & Accessories/Camera/Electronic Gadgets")
    driver_value = fields.Float("h).Driver [ Annual Wages X (Private / Total Mileage)]")
    employer_paid_amount = fields.Float("i).Servant / Gardener / Upkeep of Compound")
    actual_hotel_accommodation = fields.Float("a).Actual Hotel accommodation/Serviced Apartment within hotel building")
    employee_paid_amount = fields.Float("b).Amount paid by the employee")
    cost_of_home_leave_benefits = fields.Float(" Cost of home leave passages and incidental benefits")
    no_of_passanger = fields.Integer("No.of passages for self:")
    spouse = fields.Integer("Spouse")
    children = fields.Integer("Children")
    pioneer_service = fields.Selection([('yes','Yes'),('no','No',)])
    interest_payment = fields.Float()
    insurance_payment = fields.Float("c.Life insurance premiums paid by the employer:")
    free_holidays = fields.Float("d.Free or subsidised holidays including air passage, etc.:")
    edu_expenses = fields.Float("e.   Educational expenses including tutor provided:")
    non_monetary_awards = fields.Float("f.   Non-monetary awards for long service (for awards exceeding $200 in value) :")
    entrance_fees = fields.Float("g.   Entrance/transfer fees and annual subscription to social or recreational clubs :")
    gains_from_assets = fields.Float("h.   Gains from assets, e.g. vehicles, property, etc. sold to employees at a price lower than open market value :")
    cost_of_motor = fields.Float("i.   Full cost of motor vehicles given to employee :")
    car_benefits = fields.Float("j).Car benefits (See Explanatory Note 16)")
    non_monetary_benefits = fields.Float("k).Other non-monetary benefits which do not fall within the above items")
    furniture_value =  fields.Float(compute='_get_furniture_value', string='Value of Furniture & Fitting')
    total_value_of_benefits = fields.Float(compute='get_total_value_of_benefits',string=" TOTAL VALUE OF BENEFITS-IN-KIND (ITEMS 2 TO 4) TO BE REFLECTED IN ITEM d9 OF FORM IR8A")
    taxable_value_of_hotel_acco = fields.Float(compute='_get_hotel_acco', string="c).Taxable Value of Hotel Accommodation")
    taxalble_value_of_utilities_housekeeping = fields.Float(compute='get_taxable_value_utilities', string="j).Taxable value of utilities and housekeeping costs")
    total_taxable_value = fields.Float(compute='_get_total_taxable_value',string="f).Total Taxable Value of Place of Residence")
    place_of_residence_taxable_value = fields.Float(compute='_get_residence_taxable_values',string="d).Taxable Value of Place of Residence")
    benifits_in_kinds = fields.Float(related='total_value_of_benefits', string='44. Value of benefits-in- kinds')
            
hr_contract_income_tax()