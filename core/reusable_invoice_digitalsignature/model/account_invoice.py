# -*- coding: utf-8 -*-
from odoo import api, models, fields
from datetime import datetime

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    customer_signature = fields.Binary(string='Customer Signature')
    consultant_signature = fields.Binary(string='Consultant Signature')
    customer_signature_date = fields.Date(string='Customer Signature Date')
    consultant_signature_date = fields.Date(string='Consultant Signature Date')

    @api.multi
    def write(self, vals):
        if vals.get('customer_signature'):
            vals.update({'customer_signature_date':datetime.today().date()})
        if vals.get('consultant_signature'):
            vals.update({'consultant_signature_date':datetime.today().date()})    
        res = super(AccountInvoice, self).write(vals)
        return res