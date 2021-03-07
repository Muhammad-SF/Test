# -*- coding: utf-8 -*-
# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

from odoo import models, fields


class AccountAccount(models.Model):
    """Adding the treasury planing boolean on COA accounts."""
    _inherit = "account.account"

    treasury_planning = fields.Boolean(
        string="Treasury Planning",
        company_dependent=True)
