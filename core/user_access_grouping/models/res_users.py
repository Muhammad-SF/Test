# -*- coding: utf-8 -*-

from openerp import models, fields, api

class res_users(models.Model):
    _inherit = 'res.users'

    access_id = fields.Many2one('access.grouping', string='Access Type')

    @api.model
    def create(self, values):
        if 'access_id' in values:

            added_groups = []
            active_access_id = values.get('access_id')
            accesses = self.env['access.grouping'].search([('id','!=',active_access_id)])
            for access in accesses:
                for group in access.group_ids:
                    if group and group.id:
                        added_groups.append((group.id, False))
            active_access = self.env['access.grouping'].browse(active_access_id)
            for group in active_access.group_ids:
                if group and group.id:
                    added_groups.append((group.id, True))

            for group_id, group_value in added_groups:
                access_group_name = self.get_group_name_field(group_id)
                values[access_group_name] = group_value

        result = super(res_users, self).create(values)
        return result

    @api.multi
    def write(self, values):
        if 'access_id' in values:

            added_groups = []
            active_access_id = values.get('access_id')
            accesses = self.env['access.grouping'].search([('id','!=',active_access_id)])
            for access in accesses:
                for group in access.group_ids:
                    if group and group.id:
                        added_groups.append((group.id, False))
            active_access = self.env['access.grouping'].browse(active_access_id)
            for group in active_access.group_ids:
                if group and group.id:
                    added_groups.append((group.id, True))

            for group_id, group_value in added_groups:
                access_group_name = self.get_group_name_field(group_id)
                values[access_group_name] = group_value

        result = super(res_users, self).write(values)
        return result

    def get_group_name_field(self, group_id):
        return 'in_group_%s' % (group_id)