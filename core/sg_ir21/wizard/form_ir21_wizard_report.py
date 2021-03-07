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
from odoo import models, fields, api, _
from odoo.tools import misc
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time

class wiz_hr_employee_report(models.TransientModel):
    
    _name = 'wiz.hr.employee.report'
    
    employee_ids = fields.Many2many('hr.employee', 'rel_employee', 'an_employee', 'employee_id', 'Employee')
    start_date = fields.Date("Start Date", default=time.strftime('%Y-01-01'))
    end_date = fields.Date("End Date", default=time.strftime('%Y-12-31'))
    
    @api.multi
    def print_report(self):
        start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT)
        end_date = datetime.strptime(self.end_date, DEFAULT_SERVER_DATE_FORMAT)
        if start_date.year != end_date.year:
            raise ValidationError(_("Start date and End date must be from same year"))
        if start_date > end_date:
            raise ValidationError(_("Start Date should be Greater than End Date"))
        
        data = self.read([])[0]
        data = {
                'ids' : [],
                'model' : 'hr.employee',
                'form' : data
            }
        return self.env['report'].get_action(self, 'sg_ir21.report_form_ir21', data=data)
