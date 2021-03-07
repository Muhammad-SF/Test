# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError


class ResPartner(models.Model):
    _inherit = "res.partner"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ResPartner, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.company_id:
                if rec.company_id.branch_id:
                    branch_id = str(rec.company_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in company.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class ResUsers(models.Model):
    _inherit = "res.users"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ResUsers, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.branch_id:
                if rec.branch_id:
                    branch_id = str(rec.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in Users.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec

    

