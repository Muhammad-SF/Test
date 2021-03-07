# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TenantManagement(models.Model):
    _name = 'tenant.management'

    name   = fields.Char(required=True)
    unit   = fields.Char('Unit',required=True)
    t_info = fields.Text('Tenant Info')
    phone  = fields.Char('Phone',required=True)
    mail   = fields.Char('Email',required=True)
    image  = fields.Binary('Image')
    