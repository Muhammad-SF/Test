# -*- coding: utf-8 -*-
from odoo import models, fields

class return_reason(models.Model):
    _name = 'return.reasons'
    _description = 'License'
    _rec_name = 'name'

    name = fields.Char('Return Reason')
    active = fields.Boolean('Active', default=True)

return_reason()