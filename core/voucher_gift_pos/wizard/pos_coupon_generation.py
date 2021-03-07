# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError
from datetime import datetime

class HrExpenseRefuseWizard(models.TransientModel):

    _name = "pos_generate_coupons"
    _description = "POS Generates Coupons"

    start_date = fields.Date(string="Coupon Start Date", required=True)
    end_date   = fields.Date(string="Coupon End Date", required=True)
    voucher_val = fields.Float(string="Voucher Value" , required=True)
    type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ], store=True, default='fixed', required=True)

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        
        if self.start_date and self.end_date:
            s_date1 = datetime.strptime(self.start_date, '%Y-%m-%d')
            e_date1 = datetime.strptime(self.end_date, '%Y-%m-%d')
            
            if s_date1 > e_date1:
                self.end_date = False
                return {
                    'warning': {'title': _('Error'), 'message': _('End Date can not below the Start Date'),},
                     }


    @api.multi
    def generate_coupons(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        voucher_id = self.env['gift.voucher.pos'].browse(active_ids)
        
        if voucher_id.total_number_coupons==0:
            raise UserError(_("Kindly Set Coupon maximum limit!"))
        
        for i in range(voucher_id.total_number_coupons):
            rec = {'name': voucher_id.name+"-"+str(i),
                   'voucher': active_ids[0],
                   'start_date': self.start_date,                   
                   'end_date': self.end_date,
                   'voucher_val': self.voucher_val,
                   'type': self.type}
            self.env['gift.coupon.pos'].create(rec)    
        return {'type': 'ir.actions.act_window_close'}
