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
from odoo import tools
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import datetime
import time

class sg_letter_undertaking(models.AbstractModel):
    _name='report.sg_report_letter_undertaking.report_form_letter'
    
    @api.multi
    def get_data(self, form):
        employee_obj=self.env['hr.employee']
        
        vals = []
        emp_ids = employee_obj.search([('id', 'in', form.get('employee_ids'))])
        for employee in emp_ids:
            res = {}
            date=datetime.date.today()
            res['name']=employee.name
            res['cmp_name']=employee.address_id.name
            res['cmp_house_no']=employee.address_id.house_no
            res['cmp_street']=employee.address_id.street
            res['cmp_unit_no']=employee.address_id.unit_no
            res['cmp_email']=employee.address_id.email
            res['cmp_contry']=employee.address_id.country_id.name
            res['cmp_zip']=employee.address_id.zip
            res['cmp_phone']=employee.address_id.phone
            res['user_house_no']=employee.address_home_id.house_no
            res['user_unit_no']=employee.address_home_id.unit_no
            res['user_street']=employee.address_home_id.street
            res['user_country']=employee.address_home_id.country_id.name
            res['user_zip']=employee.address_home_id.zip
            res['user_phone']=employee.address_home_id.phone
            res['nric_no']=employee.nric_no
            res['date']=date
            vals.append(res)
        return vals
    
    @api.multi
    def render_html(self,docids, data):
        self.model=self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        datas=docs.read([])[0]
        report_lines = self.get_data(datas)
        docargs = {'doc_ids': self.ids,
                   'doc_model': self.model,
                   'data': datas,
                   'docs': docs,
                   'get_data' : report_lines}
        return self.env['report'].render('sg_report_letter_undertaking.report_form_letter', docargs)
            