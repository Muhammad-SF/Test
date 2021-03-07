# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError


class ResCompany(models.Model):
    _inherit = "res.company"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    #active = fields.Boolean(string="Active")
    
