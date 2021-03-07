# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)


class StockConfigurationSettings(models.TransientModel):
    _inherit = 'stock.config.settings'

    # group_material_request_approving_menu = fields.Boolean("Material Request Approval Matrix Menu",
    #     implied_group='std_material_request.group_material_request_approving_menu',
    #     help="""1) If user set the boolean to “true” then Material Request Approval Matrix Menu Visible.
    # 			2) If user set the boolean to “false” then Material Request Approval Matrix Menu invisible.""")
    approval_on_off_material_request = fields.Boolean(string='Approval Matrix Material Request')

    @api.model
    def get_values(self, fields):
        IrValue = self.env['ir.values'].sudo()
        return {
            'approval_on_off_material_request': IrValue.get_default('stock.config.settings', 'approval_on_off_material_request'),
        }

    @api.multi
    def set_approval_on_off_material_request(self):
        self._cr.execute("""UPDATE std_material_request SET 
        approval_on_off_material_request='%s'"""%(self.approval_on_off_material_request))
        return self.env['ir.values'].sudo().set_default(
            'stock.config.settings', 'approval_on_off_material_request', self.approval_on_off_material_request)
