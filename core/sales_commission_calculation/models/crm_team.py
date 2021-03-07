# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CRMTeam(models.Model):
    _name = "crm.team"
    _inherit = ['mail.thread' , 'ir.needaction_mixin', 'crm.team']
    _description = "Sales Team"
    _rec_name = 'name'


    name = fields.Char(string='Sales Team',track_visibility = 'always')

    user_id = fields.Many2one(track_visibility ='onchange')
    alias_name = fields.Char(track_visibility ='onchange')

    commission_scheme_salesteamleader_id = fields.Many2one(
        comodel_name='commission.scheme.salesteamleader',
        string='Team Leader Commission',track_visibility='onchange',
    )

    commission_scheme_salesperson_id = fields.Many2one(
        comodel_name='commission.scheme.salesperson',
        string='Sales Person Commission',track_visibility='onchange',
    )
    