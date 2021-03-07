# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def load_views(self, views, options=None):
        res = super(AccountInvoice, self).load_views(views, options)
        if 'fields' in res and 'invoice_date' in res['fields']:
            res['fields']['invoice_date']['searchable'] = False
        return res

# class partner(models.Model):
#     _inherit = 'res.partner'
#
#     property_account_payable_id = fields.Many2one(domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]")