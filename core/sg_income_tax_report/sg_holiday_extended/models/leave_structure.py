# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class sg_leave_contract(models.Model):

    _name = 'holiday.group.config'

    name = fields.Char("Name", size=48)
    holiday_group_config_line_ids = fields.One2many('holiday.group.config.line','holiday_group_config_id','Config Line')
    
    
class holiday_group_config_line(models.Model):
    _name = 'holiday.group.config.line'

    holiday_group_config_id = fields.Many2one('holiday.group.config','Leave Types')
    leave_type_id = fields.Many2one('hr.holidays.status','Leave Types')
    default_leave_allocation = fields.Float('Default Annual Leave')
    incr_leave_per_year = fields.Float('Increment Leaves Per Year')
    max_leave_kept = fields.Float('Maximum Leave')
    carryover = fields.Selection([('none','None'), ('up_to','50% of Entitlement'),
                                  ('no_of_days','Number of Days'),
                                  ('unlimited','Unlimited')], default="unlimited" ,string="Carryover")
    carry_no_of_days = fields.Float("Number of Days")


    @api.constrains('leave_type_id')
    def _check_multiple_leaves_configured(self):
        """
            This constrain method is used to restrict the system 
            that do not configure same leave for multiple time.
        """
        for holiday in self:
            domain = [
                ('leave_type_id', '=',holiday.leave_type_id.id),
                ('holiday_group_config_id', '=', holiday.holiday_group_config_id.id),
                ('id', '!=', holiday.id),
                ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError('You can not add multiple configurations for leave type "%s".'%(holiday.leave_type_id.name2))
