# -*- coding: utf-8 -*-

from odoo import models, fields

class CommissionSchemeSalesTeamLeader(models.Model):
    _name = 'commission.scheme.salesteamleader'
    _description = 'Commission Structure Sales Team Leader'
    _rec_name = 'name'

    name = fields.Char(string='Name')    
    commission_scheme_ids = fields.Many2many(comodel_name='commission.scheme', string='Commission Structure')
    # sales_team_id = fields.Many2one(comodel_name='crm.team', string='Sales Team')
