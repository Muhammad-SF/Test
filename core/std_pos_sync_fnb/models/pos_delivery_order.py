# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError


class POSDeliveryOrder(models.Model):
    _inherit = "pos.delivery.order"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(POSDeliveryOrder, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.user_id:
                if rec.user_id.branch_id:
                    branch_id = str(rec.user_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
