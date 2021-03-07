# -*- coding: utf-8 -*-
import re
from openerp import models, fields, api


class res_users(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, values):
        added_groups = []
        for group_key in values:
            match = re.search('in_group_([0-9]+)', group_key)
            if match and match.group(1):
                group_id = int(match.group(1))
                group_value = values.get(group_key)
                added_groups += self.get_added_group_data(group_id, group_value)
            else:
                match = re.search('sel_groups_([0-9_]+)', group_key)
                if match and match.group(1):
                    group_ids = match.group(1).split('_')
                    if len(group_ids) > 0:
                        for group_id in group_ids:
                            added_groups += self.get_added_group_data(int(group_id), False)
                        group_value = values.get(group_key)
                        added_groups += self.get_added_group_data(int(group_value), True)
        for group_id, group_value in added_groups:
            access_group_name = self.get_group_name_field(group_id)
            values[access_group_name] = group_value
        result = super(res_users, self).create(values)
        return result

    def get_added_group_data(self, group_id, group_value):
        result = []
        accesses = self.env['access.grouping'].search([('group_id', '=', group_id)])
        for access in accesses:
            for access_group in access.group_ids:
                if access_group and access_group.id:
                    result.append((access_group.id, group_value))
        return result

    @api.multi
    def write(self, values):
        added_groups = []
        for group_key in values:
            match = re.search('in_group_([0-9]+)', group_key)
            if match and match.group(1):
                group_id = int(match.group(1))
                group_value = values.get(group_key)
                added_groups += self.get_added_group_data(group_id, group_value)
            else:
                match = re.search('sel_groups_([0-9_]+)', group_key)
                if match and match.group(1):
                    group_ids = match.group(1).split('_')
                    if len(group_ids) > 0:
                        for group_id in group_ids:
                            added_groups += self.get_added_group_data(int(group_id), False)
                        group_value = values.get(group_key)
                        added_groups += self.get_added_group_data(int(group_value), True)
        for group_id, group_value in added_groups:
            access_group_name = self.get_group_name_field(group_id)
            values[access_group_name] = group_value
        result = super(res_users, self).write(values)
        return result

    def get_group_name_field(self, group_id):
        return 'in_group_%s' % (group_id)