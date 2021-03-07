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

#import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class hr_year(models.Model):

    _name = "hr.year"
    _description = "HR Fiscal Year"
    _order = "date_start, id"
    
    name = fields.Char('HR Year', required=True,help="Name of hr year")
    code = fields.Char('Code', size=6, required=True)
    date_start = fields.Date('Start Date', required=True)
    date_stop = fields.Date('End Date', required=True)
    period_ids = fields.One2many('hr.period', 'hr_year_id', 'Periods')
    state = fields.Selection([('draft','Draft'),('open','Open'), ('done','Closed')], 'Status',
                             default='draft',readonly=True, copy=False)
    
    _sql_constraints = [
        ('hr_year_code_uniq', 'unique(code)', 'Code must be unique per year!'),
        ('hr_year_name_uniq', 'unique(name)', 'Name must be unique')
    ]

#    @api.constrains('date_start','date_stop')
#    def _check_hr_year_duration(self):
#        for obj_fy in self:
#            if obj_fy.date_stop < obj_fy.date_start:
#                raise ValidationError(_('Error!\nThe start date of a hr year must precede its end date!'))
            
    @api.multi
    def close_period(self):
        return self.write({'state':'done'})
    

    @api.multi
    def create_period(self):
        interval=1
        for fy in self:
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                self.env['hr.period'].create({
                                              'name': ds.strftime('%m/%Y'),
                                              'code': ds.strftime('%m/%Y'),
                                              'date_start': ds.strftime('%Y-%m-%d'),
                                              'date_stop': de.strftime('%Y-%m-%d'),
                                              'hr_year_id': fy.id,
                                              })
                ds = ds + relativedelta(months=interval)
            fy.write({'state':'open'})
        return True

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = ['|', ('code', operator, name), ('name', operator, name)]
        hr_year_rec = self.search(['|', ('code', operator, name), ('name', operator, name)]+ args, limit=limit)
        return hr_year_rec.name_get()


class hr_period(models.Model):
    _name = "hr.period"
    _description = "HR period"
    _order = "date_start desc"

    name = fields.Char('Period Name', required=True)
    code = fields.Char('Code', size=12)
    special = fields.Boolean('Opening/Closing Period',help="These periods can overlap.")
    date_start = fields.Date('Start of Period', required=True, states={'done':[('readonly',True)]})
    date_stop = fields.Date('End of Period', required=True, states={'done':[('readonly',True)]})
    hr_year_id = fields.Many2one('hr.year', 'HR Year', required=True, states={'done':[('readonly',True)]})
    state = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False,default="draft",
                              help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.')


#    @api.constrains('date_start','date_stop')
#    def _check_hr_period_duration(self):
#        for obj_period in self:
#            if obj_period.date_stop < obj_period.date_start:
#                raise ValidationError(_('Error!\nThe duration of the Period(s) is/are invalid.'))
#
#    @api.constrains('date_stop')
#    def _check_year_limit(self):
#        for obj_period in self:
#            if obj_period.hr_year_id.date_stop < obj_period.date_stop or \
#               obj_period.hr_year_id.date_stop < obj_period.date_start or \
#               obj_period.hr_year_id.date_start > obj_period.date_start or \
#               obj_period.hr_year_id.date_start > obj_period.date_stop:
#                raise ValidationError(_('Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the hr year.'))
#            pids = self.search([('date_stop','>=',obj_period.date_start),('date_start','<=',obj_period.date_stop), ('id','!=',obj_period.id)])
#            if pids:
#                raise ValidationError(_('Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the hr year.'))


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = ['|', ('code', operator, name), ('name', operator, name)]
        hr_period_rec = self.search(['|', ('code', operator, name), ('name', operator, name)]+ args, limit=limit)
        return hr_period_rec.name_get()
