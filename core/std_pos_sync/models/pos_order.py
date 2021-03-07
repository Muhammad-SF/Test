# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

class POSOrder(models.Model):
    _inherit = "pos.order"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(POSOrder, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.company_id:
                if rec.company_id.branch_id:
                    branch_id = str(rec.company_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in company.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
    @api.multi
    def create_pos_order_payment(self,payment_data):
        order = self.browse(payment_data.get('pos_order_id'))
        journal_obj = self.env['account.journal'].browse(payment_data.get('journal_id'))
        amount = order.amount_total - order.amount_paid
        data = {
            'amount': payment_data.get('amount'),
            'journal': payment_data.get('journal_id'),
            'journal_id': journal_obj and journal_obj.id or False,
            'payment_date': fields.Date.today(),
        }
        if amount != 0.0:
            order.add_payment(data)
        if order.test_paid():
            order.action_pos_order_paid()
            return {'type': 'ir.actions.act_window_close'}
        return True
        
class POSSession(models.Model):
    _inherit = "pos.session"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(POSSession, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.config_id and rec.config_id.company_id:
                if rec.config_id.company_id.branch_id:
                    branch_id = str(rec.config_id.company_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in company.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class POSConfig(models.Model):
    _inherit = "pos.config"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(POSConfig, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.branch_id:
                branch_id = str(rec.branch_id.id)
            else:
                raise UserError(_('Please configure branch in POS Config.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec


class PosConfiguration(models.TransientModel):
    _inherit = 'pos.config.settings'
    
    pos_client = fields.Boolean(string="POS Client")
    
    @api.model
    def get_default_pos_client(self, fields):
        pos_client = self.env.ref('std_pos_sync.pos_client').value
        if pos_client == 'False':
            return {'pos_client': False}
        if pos_client == 'True':
            return {'pos_client': True}

    @api.multi
    def set_default_pos_client(self):
        for record in self:
            print "\n\n=record.pos_client",record.pos_client
            if record.pos_client:
                self.env.ref('std_pos_sync.pos_client').write({'value': 'True'})
            else:
                self.env.ref('std_pos_sync.pos_client').write({'value': 'False'})
    

