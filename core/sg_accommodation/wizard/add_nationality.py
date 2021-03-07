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


class add_nationality(models.TransientModel):
    _name = 'add.nationality'

    room_id = fields.Many2one('room.room','Room')
    country_id = fields.Many2one('res.country','Country')
    availability = fields.Float('Availability')

    @api.multi
    def add_country_avail(self):
        """
        This method is used to add/update national availability for rooms
        -----------------------------------------------------------------
        @self : Records Set
        @return True
        """
        vis_obj = self.env['visa.quota']
        for wiz_rec in self:
            visa_rec = vis_obj.search([('nationality_id','=',wiz_rec.country_id.id),
                                      ('room_id','=',wiz_rec.room_id.id)])
            if visa_rec:
                for vis_rec in visa_rec:
                    quota = vis_rec.number_of_quota + wiz_rec.availability
                visa_rec.write({'number_of_quota': quota})
            else:
                visa_vals = {
                    'room_id':wiz_rec.room_id.id,
                    'number_of_quota':wiz_rec.availability,
                    'accommodation_id':wiz_rec.room_id.accommodation_id.id,
                    'nationality_id':wiz_rec.country_id.id
                }
                visa_rec = vis_obj.create(visa_vals)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: