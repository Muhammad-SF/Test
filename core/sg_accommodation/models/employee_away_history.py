##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt.Ltd. (<http://www.serpentcs.com>).
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
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
from odoo import fields, models,api,_
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time

class employee_away_history(models.Model):
    
    _name = 'emp.away.history'
    
    @api.multi
    def set_date_from(self):
        """
        This method is used to set the Date From field based on Leave Button
        ------------------------------------------------
        """
        cr,uid,context = self.env.args
        context = dict(context)
        for rec in self:
            rec.write({'date_from':time.strftime(DEFAULT_SERVER_DATE_FORMAT)})
            emp_rec=self.env['hr.employee'].search([('id','=',rec.emp_id.id)])
            if emp_rec:
                emp_rec.write({'away':True})
        return True
    
    @api.multi
    def set_date_to(self):
        """
        This method is used to set the Date To field based on Return Button
        ------------------------------------------------
        """
        cr,uid,context = self.env.args
        context = dict(context)
        for rec in self:
            rec.write({'date_to':time.strftime(DEFAULT_SERVER_DATE_FORMAT)})
            emp_rec=self.env['hr.employee'].search([('id','=',rec.emp_id.id)])
            if emp_rec:
                emp_rec.write({'away':False})
        return True
    
    exp_date_from = fields.Date('Expected Date From')
    exp_date_to = fields.Date('Expected Date To')
    date_from = fields.Date('Date From')
    date_to=fields.Date('Date To')
    reason_id=fields.Many2one('emp.away.reason','Reason')
    emp_id=fields.Many2one('hr.employee','Employee')

class employee_away_reason(models.Model):
    
    _name = 'emp.away.reason'
    
    code=fields.Char(string='Code')
    name=fields.Char(string='Name')

