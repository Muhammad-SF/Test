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

from odoo import fields, models,api,_
from odoo.exceptions import ValidationError


class wiz_emp_away_history(models.TransientModel):
    _name = 'wiz.emp.away.history'

    employee_id = fields.Many2one('hr.employee','Employee')
    exp_date_from = fields.Date('Expected Date From')
    exp_date_to = fields.Date('Expected Date To')
    reason_id=fields.Many2one('emp.away.reason','Reason')
    all_employee=fields.Boolean('All Employee',default=False)

    @api.multi
    def generate_history(self):
        cr,uid,context = self.env.args
        context = dict(context)
        domain = []
        for rec in self:
            if rec.exp_date_to < rec.exp_date_from:
                    raise ValidationError('Expected Date To must be Higher than Expected Date From !')
            if context.get('default_all_employee',False):
                domain = [('id','in',context.get('active_ids',False))]
            else:
                domain = [('id','=',rec.employee_id.id)]
            emp_rec=self.env['hr.employee'].search(domain)
            if emp_rec:
                for emp in emp_rec:
                    vals={'emp_id':emp.id,
                          'exp_date_from':rec.exp_date_from,
                          'exp_date_to':rec.exp_date_to,
                          'reason_id':rec.reason_id.id
                          }
                    self.env['emp.away.history'].create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: