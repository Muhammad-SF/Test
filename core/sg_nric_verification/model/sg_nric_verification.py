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
from odoo import models, fields, api, _
from odoo.tools import ustr
from odoo.exceptions import ValidationError

class hr_employee(models.Model):
    _inherit='hr.employee'
    
    @api.constrains('identification_id','identification_no')
    def _check_identification_id(self):
        for employee in self:
            args=[]
            if employee.identification_id and employee.identification_no=='1':
                id_no = employee.identification_id
                for no in id_no[1:-1]:
                    args.append(no)
                count = 0
                total_amount=0
                for digit in args:
                    count=count+1
                    if count==1:
                        first_digit=int(digit)*2
                        total_amount+=first_digit
                    elif count==2:
                        second_digit=int(digit)*7
                        total_amount+=second_digit
                    elif count==3:
                        third_digit=int(digit)*6
                        total_amount+=third_digit
                    elif count==4:
                        fourth_digit=int(digit)*5
                        total_amount+=fourth_digit
                    elif count==5:
                        fifth_digit=int(digit)*4
                        total_amount+=fifth_digit
                    elif count==6:
                        sixth_digit=int(digit)*3
                        total_amount+=sixth_digit
                    elif count==7:
                        seventh_digit=int(digit)*2
                        total_amount+=seventh_digit
                first_arg = id_no[0:1].upper()
                if first_arg=='T' or first_arg=='G':
                    total_amount+=4
                reminder=total_amount%11
                if first_arg=='S' or first_arg=='T':
                    if reminder==0:
                        reminder='J'
                    elif reminder==1:
                        reminder='Z'
                    elif reminder==2:
                        reminder='I'
                    elif reminder==3:
                        reminder='H'
                    elif reminder==4:
                        reminder='G'
                    elif reminder==5:
                        reminder='F'
                    elif reminder==6:
                        reminder='E'
                    elif reminder==7:
                        reminder='D'
                    elif reminder==8:
                        reminder='C'
                    elif reminder==9:
                        reminder='B'
                    elif reminder==10:
                        reminder='A'
                if first_arg=='F' or first_arg=='G':
                    if reminder==0:
                        reminder='X'
                    elif reminder==1:
                        reminder='W'
                    elif reminder==2:
                        reminder='U'
                    elif reminder==3:
                        reminder='T'
                    elif reminder==4:
                        reminder='R'
                    elif reminder==5:
                        reminder='Q'
                    elif reminder==6:
                        reminder='P'
                    elif reminder==7:
                        reminder='N'
                    elif reminder==8:
                        reminder='M'
                    elif reminder==9:
                        reminder='L'
                    elif reminder==10:
                        reminder='K'
                last_arg=id_no[-1].upper()
                if last_arg != reminder:
                    raise ValidationError(_("Please enter valid NRIC Number"))
                