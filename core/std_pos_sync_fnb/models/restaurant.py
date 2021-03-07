# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError


class RestaurantFloor(models.Model):
    _inherit = "restaurant.floor"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(RestaurantFloor, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.branch_id:
                branch_id = str(rec.create_uid.branch_id.id)
            else:
                raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class RestaurantTable(models.Model):
    _inherit = "restaurant.table"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(RestaurantTable, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.branch_id:
                branch_id = str(rec.create_uid.branch_id.id)
            else:
                raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec

    

