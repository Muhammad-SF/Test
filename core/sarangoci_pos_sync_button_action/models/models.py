# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError



class pos_config(models.Model):
    _inherit = 'pos.config'

    last_sync_date = fields.Datetime()
    last_sync_order_date = fields.Datetime()

    @api.model
    def _cron_action_sync_button(self):
        pos_config = self.env['pos.config'].search([], limit=1)
        pos_config.action_sync_button()

    @api.multi
    def action_sync_order_button(self):
        orders = self.env['pos.order'].search([('is_sync', '=', False), ('state', '=', 'paid')])
        self.env['pos.send.order'].send_order_to_server(orders)
        pos_configs = self.env['pos.config'].search([])
        current_datetime = datetime.now()
        for config in pos_configs:
            config.last_sync_order_date = current_datetime

    @api.multi
    def action_sync_button(self):
        if self.env['ir.values'].get_default('pos.config.settings', 'synchronize_user') == 'client':
            try:
                products = self.env['product.sync.server'].search([])
                for product in products:
                    product.pull_product()
            except Exception as e:
                if e.name != 'Success':
                    raise e
        else:
            try:
                products = self.env['product.sync.server'].search([])
                for product in products:
                    product.push_product()
            except Exception as e:
                if e.name != 'Success':
                    raise e
        pos_configs = self.env['pos.config'].search([])
        current_datetime = datetime.now()
        for config in pos_configs:
            config.last_sync_date = current_datetime

class PosRound(models.TransientModel):
    _inherit = 'pos.config.settings'

    synchronize_user = fields.Selection([('client','Client'),('server','Server')])

    @api.multi
    def set_synchronize_user(self):
        ir_values_obj = self.env['ir.values']
        ir_values_obj.sudo().set_default('pos.config.settings', "synchronize_user", self.synchronize_user)