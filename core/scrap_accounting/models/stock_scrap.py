# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class stock_scrap(models.Model):
    _inherit = 'stock.scrap'

    @api.multi
    def do_scrap(self):
        stock_scrap_account_id = self.product_id.stock_scrap_account_id
        if not stock_scrap_account_id:
            stock_scrap_account_id = self.product_id.categ_id.stock_scrap_account_id
        # if not stock_scrap_account_id:
        #     raise ValidationError(_('Stock Scrap Account must be filled!'))
        res = super(stock_scrap, self).do_scrap()
        return res