# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError


class GiftVoucherPos(models.Model):
    _inherit = "gift.voucher.pos"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(GiftVoucherPos, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.branch_id:
                branch_id = str(rec.create_uid.branch_id.id)
            else:
                raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class GiftCouponPos(models.Model):
    _inherit = "gift.coupon.pos"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(GiftCouponPos, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.branch_id:
                branch_id = str(rec.create_uid.branch_id.id)
            else:
                raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec

    

