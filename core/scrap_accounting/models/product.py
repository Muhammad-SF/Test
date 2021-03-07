# -*- coding: utf-8 -*-

from odoo import models, fields, api

class product_template(models.Model):
    _inherit = 'product.template'

    stock_scrap_account_id = fields.Many2one('account.account', 'Stock Scrap Account')




class product_category(models.Model):
    _inherit = 'product.category'

    stock_scrap_account_id = fields.Many2one('account.account', 'Stock Scrap Account')