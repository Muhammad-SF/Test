# -*- coding: utf-8 -*-
from odoo import fields, models, api

class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    is_user_rate_po = fields.Boolean("Activate User Rate in Purchase Order", help="Activate to process user rate in purchase order.")

    @api.multi
    def set_default_fields(self):
        ir_values_obj = self.env['ir.values']
        ir_values_obj.sudo().set_default('purchase.config.settings', 'is_user_rate_po', self.is_user_rate_po)

    @api.model
    def get_default_fields(self, fields):
        ir_values_obj = self.env['ir.values']
        is_user_rate_po = ir_values_obj.sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        return {
            'is_user_rate_po': is_user_rate_po,
        }

PurchaseConfigSettings()

class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    is_user_rate_so = fields.Boolean("Activate User Rate in Sales Order", help="Activate to process user rate in sales order.")

    @api.multi
    def set_default_fields(self):
        ir_values_obj = self.env['ir.values']
        ir_values_obj.sudo().set_default('sale.config.settings', 'is_user_rate_so', self.is_user_rate_so)

    @api.model
    def get_default_fields(self, fields):
        ir_values_obj = self.env['ir.values']
        is_user_rate_so = ir_values_obj.sudo().get_default('sale.config.settings', 'is_user_rate_so')
        return {
            'is_user_rate_so': is_user_rate_so,
        }

SaleConfigSettings()