# -*- coding: utf-8 -*-

from odoo import models, fields, api

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, values):
        context = self.env.context
        if not context.get('search_default_customer', False) and context.get('search_default_no_share', False):
            if values.get('customer', False):
                values.update({
                    'customer': False,
                })
        result = super(res_partner, self).create(values)
        return result