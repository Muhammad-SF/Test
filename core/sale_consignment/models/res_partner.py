# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class res_partner(models.Model):
    _inherit = 'res.partner'

    is_consignment = fields.Boolean('Is Consignment')
    consignment_percent = fields.Float('Consignment Percent')
    consignment_wh = fields.Many2one('stock.warehouse', 'Consignment Warehouse')

    @api.multi
    @api.onchange('is_consignment')
    def _onchange_is_consignment(self):
        for record in self:
            if record.is_consignment:
                record.supplier = True