# -*- coding: utf-8 -*-
# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

from odoo import models, fields, api, _
from collections import Counter
import json


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    date_treasury = fields.Date(string="Treasury Date")
