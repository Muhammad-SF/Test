# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import models, fields, api, _, tools
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp

class sales_terms_condition(models.Model):
    _name = 'sale.tc'
    _rec_name = 'name'

    name = fields.Char('Name')
    terms = fields.Text(string='Terms & Condtions')
    active = fields.Boolean('Active', default=True)
    sale_order = fields.Boolean('Sale Order & Quotations')
    purchase_order = fields.Boolean('Purchase RFQ & Purchase Orders')
    account_order = fields.Boolean('Invoices')
