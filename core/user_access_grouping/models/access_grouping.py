# -*- coding: utf-8 -*-

from openerp import models, fields, api

class access_grouping(models.Model):
    _name = 'access.grouping'

    name = fields.Char('Name', required=True)
    group_ids = fields.Many2many('res.groups', string='Groups')
# eval="[(4, ref('base.group_user'))]"