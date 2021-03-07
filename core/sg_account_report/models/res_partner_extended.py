# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields


class res_partner(models.Model):
    _inherit = 'res.partner'

    customer_uen = fields.Char('Customer UEN', size=64)
    customer_id = fields.Char('Customer ID', size=16)
    supplier_uen = fields.Char('Supplier UEN', size=64)

    _sql_constraints = [
        ('customer_id_uniq', 'unique(customer_id)', 'Customer ID must be unique per Customer!'),
    ]


class res_company(models.Model):
    _inherit = 'res.company'

    company_uen = fields.Char('Company UEN', size=64)
    gst_no = fields.Char('GST No', size=64)
    period_start = fields.Date('Period Start')
    period_end = fields.Date('Period End')
    iaf_creation_date = fields.Date('IAF Creation Date')
    product_version = fields.Char('Product Version', size=32)
    iaf_version = fields.Char('IAF Version', size=32)
    credit_account_ids = fields.Many2many('account.account','credit_account_company_rel','company_id', 'account_id','Creditable Accounts')
    debit_account_ids = fields.Many2many('account.account','debit_account_company_rel','company_id', 'account_id','Debitable Accounts')


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    permit_no = fields.Char('Permit No.', size=32)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
