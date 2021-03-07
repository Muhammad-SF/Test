# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    group_analytic_account_for_sales = fields.Boolean('Analytic accounting for sales',
        implied_group='analytic.group_analytic_accounting',
        help='Allows you to specify an analytic account on purchase order lines.')