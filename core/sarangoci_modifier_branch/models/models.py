# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResBranch(models.Model):
    _inherit = 'res.branch'

    service_charge_id = fields.Many2one('service.charge', string = 'Service Charge')
    tax_id = fields.Many2one('account.tax', string='Tax')
    servicecharge = fields.Float('Service Charge')

