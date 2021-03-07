# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-2012 Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
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
from odoo import models, fields, api
from datetime import date

class hr_employee(models.Model):
    _inherit="hr.employee"
    
    spouse_name=fields.Char("Spouse Name")
    spouse_dob=fields.Date("Date of Birth")
    spouse_ident_no=fields.Char("Identification number")
    marriage_date=fields.Date("Date of Marriage")
    spouse_nationality=fields.Many2one('res.country', "Nationality")
    nric_no=fields.Char("NRIC No")
    fin_no=fields.Char("FIN No")    
    
    