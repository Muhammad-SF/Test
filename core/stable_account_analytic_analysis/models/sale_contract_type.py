from odoo import models, fields, api

class AccountAnalyticAccountContractType(models.Model):
    _name = 'account.analytic.account.contracttype'

    name = fields.Char(string='Contract Type', size=512, required=True)