# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    out_manual_return_id = fields.Many2one('manual.return', 'Manual Return')
    in_manual_return_id = fields.Many2one('manual.return', 'Manual Return')
