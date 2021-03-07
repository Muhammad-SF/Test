# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    group_prepayment = fields.Boolean("Use Prepayment", implied_group='standard_prepayment.group_prepayment', help="""Allows to show prepayment menu. """)

AccountConfigSettings()