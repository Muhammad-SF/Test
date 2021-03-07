# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

class POSOrder(models.Model):
    _inherit = "pos.order"
    
    @api.multi
    def create_pos_order_payment(self,payment_data):
        order = self.browse(payment_data.get('pos_statement_id'))
        logger.error("\n\n========order %s",order)
        journal_obj = self.env['account.journal'].browse(payment_data.get('journal_id'))
        amount = order.amount_total - order.amount_paid
        data = {
            'amount': payment_data.get('amount'),
            'journal': payment_data.get('journal_id'),
            'journal_id': journal_obj and journal_obj.id or False,
            'payment_date': fields.Date.today(),
        }
        logger.error("\n\n========data %s",data)
        if amount != 0.0:
            order.add_payment(data)
        if order.test_paid():
            order.action_pos_order_paid()
            return {'type': 'ir.actions.act_window_close'}
        return True
        
