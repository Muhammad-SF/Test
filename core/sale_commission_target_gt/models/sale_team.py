# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class Crmteam(models.Model):
    _inherit = 'crm.team'

    target_group_id = fields.Many2one('target.group',string='Sales Commission Target')

Crmteam()