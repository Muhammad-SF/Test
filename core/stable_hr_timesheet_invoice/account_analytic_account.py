# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from odoo import fields, models, api, exceptions

class account_analytic_account(models.Model):
    _inherit = "account.analytic.account"

    type         = fields.Selection([
        ('view', 'Analytic View'),
        ('normal', 'Analytic Account'),
        ('contract', 'Contract or Project'),
        ('template', 'Template of Contract')
    ], 'Type of Account', required=True, default='contract',
        help="If you select the View Type, it means you won\'t allow to create journal entries using that account.\n" \
             "The type 'Analytic account' stands for usual accounts that you only want to use in accounting.\n" \
             "If you select Contract or Project, it offers you the possibility to manage the validity and the invoicing options for this account.\n" \
             "The special type 'Template of Contract' allows you to define a template with default data that you can reuse easily.")
    state        = fields.Selection([
        ('template', 'Template'),
        ('draft', 'New'),
        ('open', 'In Progress'),
        ('pending', 'To Renew'),
        ('close', 'Closed'),
        ('cancelled', 'Cancelled')], 'Status', required=True, default='draft',
        track_visibility='onchange', copy=False)
    quantity_max = fields.Float('Prepaid Service Units',
                                help='Sets the higher limit of time to work on the contract, based on the timesheet. (for instance, number of hours in a limited support contract.)')
    date         = fields.Date('Expiration Date', select=True, track_visibility='onchange')
    parent_id    = fields.Many2one('account.analytic.account', 'Parent Analytic Account', select=2)
    child_ids    = fields.One2many('account.analytic.account', 'parent_id', 'Child Accounts', copy=True)
    manager_id   = fields.Many2one('res.users', 'Account Manager', track_visibility='onchange')
    template_id  = fields.Many2one('account.analytic.account', 'Template of Contract')
    description  = fields.Text('Description')
    date_start   = fields.Date('Start Date')