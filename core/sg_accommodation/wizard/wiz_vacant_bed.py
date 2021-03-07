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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time


class wiz_vacant_bed(models.TransientModel):

    _name = 'wiz.vacant.bed'

    employee_id = fields.Many2one('hr.employee','Employee')
    room_id = fields.Many2one('room.room', 'Room')
    bed_id = fields.Many2one('beds.beds', 'Bed')

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
        This method is used to identify the bed and room based on the 
        employee selected.
        ------------------------------------------------------------------
        @param self : object pointer
        @param return : True
        """
        cr, uid, context = self.env.args
        emp_id = self.employee_id.id
        if emp_id:
            #If employee is there fetch the related room and bed
            bed_id = self.env['beds.beds'].search([('employee_id','=',self.employee_id.id),('room_id.accommodation_id','=',context.get('accommodation_id'))])
            if not bed_id:
                emp_name = self.employee_id.name
                raise ValidationError('The Employee is not accommodated here!' + emp_name)
            self.bed_id = bed_id.id
            self.room_id = bed_id.room_id.id

    @api.multi
    def vacant_bed(self):
        """
        This method is used to vacant the bed in a room in accommodation
        @api.multi : The api of multi decorator
        @param self : object pointer and Record set
        @return True
        """
        for vac_rec in self:
            history_vals = {
                'bed_id': vac_rec.bed_id.id,
                'room_id':vac_rec.room_id.id,
                'accommodation_id':vac_rec.room_id.accommodation_id.id,
                'date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'employee_id':vac_rec.bed_id.employee_id.id,
                'country_id':vac_rec.bed_id.employee_id.emp_country_id.id,
                'type':'vacant',
            }
            # Make the bed Empty
            vac = vac_rec.bed_id.write({'employee_id':False})
            # Create History in Accommodation
            his = self.env['accommodation.history'].create(history_vals)
            #Update Accomodated in Employee
            vac_upt = vac_rec.employee_id.write({'accommodated':False})
        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: