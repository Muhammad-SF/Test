# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    validate_id = fields.Many2one(
        comodel_name='res.users', string='Validated By', help='')
    validate_signature = fields.Binary(
        string="Validate Signature")
    validate_date_time = fields.Datetime(
        string='Validated On', help='Validated datetime.')

    @api.multi
    def do_new_transfer(self):
        res = super(StockPicking, self).do_new_transfer()
        if self.env.user.main_signature == 'upload_file':
            validate_signature = self.env.user.upload_datas
        else:
            validate_signature = self.env.user.signature
        self.write({'validate_id': self.env.user.id,
                    'validate_signature': validate_signature,
                    'validate_date_time': fields.Datetime.now(),
                    })
        return res
StockPicking()