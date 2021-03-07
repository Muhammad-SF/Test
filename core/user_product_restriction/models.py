# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_product_ids = fields.Many2many(
        'product.template',
        'product_user_rel',
        'user_id',
        'product_id',
        'Allowd Products')