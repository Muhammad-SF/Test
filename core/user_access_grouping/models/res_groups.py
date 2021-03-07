# -*- coding: utf-8 -*-

from openerp import models, fields, api

class res_groups(models.Model):
    _inherit = 'res.groups'

    @api.model
    def get_groups_by_application(self):
        result = []
        res = super(res_groups, self).get_groups_by_application()
        for app, type, gs in res:
            if app.name == 'Access Type':
                if type == 'boolean':
                    type = 'selection'
            result.append((app, type, gs))
        return result