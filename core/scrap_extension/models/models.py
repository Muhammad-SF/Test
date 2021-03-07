# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ScrapReason(models.Model):
    _name = 'scrap.reason'

    name   = fields.Char('Reason')

ScrapReason()

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    reason_id = fields.Many2one('scrap.reason', string='Reason', required=1)
    date_submitted = fields.Date(string='Date Submitted',default=fields.Date.today())

StockScrap()