# -*- coding: utf-8 -*-
# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

from odoo import api, fields, models, _


class TreasMananConfigSettings(models.TransientModel):
    _name = 'treasury.management.config.settings'
    _inherit = 'res.config.settings'

    @api.multi
    def set_fc_accounts(self):
        account_list = self.env['account.account'].search([])
        for account in account_list:
            if account in self.fc_account_ids:
                account.treasury_planning = True
            else:
                account.treasury_planning = False

    def _default_fc_accounts(self):
        return self.env['account.account'].search([('treasury_planning', '=', True)])

    def _default_fc_css(self):
        css = """{
            '': '',
            'BNK': '#FFFFFF',
            'FBK': '#D4EFDF',
            'FPL': '#FAFAD2',
            'DFT': '#D7DBDD',
        }"""
        return css

    def set_default_css_dict(self):
        self.env['ir.values'].sudo().set_default(
            'treasury.management.config.settings',
            'fc_css_dict', self.fc_css_dict)

    fc_css_dict = fields.Text(
        string='Dictionary with colours',
        default=lambda self: self._default_fc_css(),)

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)

    fc_account_ids = fields.Many2many(
        comodel_name='account.account',
        string='Accounts for treasury planning',
        default=lambda self: self._default_fc_accounts(),
        help='The accounts selected here are those on which the treasury planning will be based')

