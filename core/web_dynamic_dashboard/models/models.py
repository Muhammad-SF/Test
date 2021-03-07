# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
from odoo import models, fields, api

from odoo import http
import json
import logging
from werkzeug.exceptions import Forbidden

import werkzeug.urls

from odoo import http, tools, _
from odoo.http import request
from odoo.exceptions import ValidationError

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from random import choice
from string import ascii_uppercase

from datetime import datetime, timedelta
import re
import math


class View(models.Model):
    _inherit = 'ir.ui.view'
    type = fields.Selection(
        selection_add=[('ddashboard', 'DDashboard')]
    )


class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'
    view_mode = fields.Selection(
        selection_add=[('ddashboard', 'DDashboard')]
    )


class Dashboard(models.Model):
    _name = 'web.dashboard'

    name = fields.Char('Name', required=True, default="My Dashboard")
    parent_menu_id = fields.Many2one(
        'ir.ui.menu', 'Add Dashboard Under Menu', copy=False)
    menu_id = fields.Many2one('ir.ui.menu', 'Generated Menu', copy=False)
    block_ids = fields.One2many(
        'web.dashboard.block', 'dashboard_id', 'Blocks', copy=True)

    # TODO: Copy to 10
    dashboard_source = fields.Selection([('odoo', 'Odoo Dynamic Dashboard'), ('tableau', 'Tableau')],
                                        string='Dashboard Source', required=True, default='odoo')
    tableau_url = fields.Char('Tableau URL', required=False)

    @api.onchange('name', 'parent_menu_id')
    def onchange_parent_menu(self):
        if self.parent_menu_id:
            if not self.menu_id:
                dashboard_action = self.env.ref('web_dynamic_dashboard.web_dashboard_action').copy({
                    'context': """{ 'dashboard_id' : %s }""" % self._origin.id
                })
                menu = self.env['ir.ui.menu'].sudo().create({
                    'parent_id': self.parent_menu_id.id,
                    'name': self.name,
                    'action': 'ir.actions.act_window,%s' % dashboard_action.id,
                    'sequence': -100
                })
                self.menu_id = menu.id
            else:
                self.menu_id.write({
                    'name': self.name,
                    'parent_id': self.parent_menu_id.id,
                    'sequence': -100
                })


class DashboardBlock(models.Model):
    _name = 'web.dashboard.block'
    _order = 'sequence'

    name = fields.Char('Name', required=True)
    dashboard_id = fields.Many2one('web.dashboard', 'Dashboard')
    block_type = fields.Selection([('tile', 'Tile'), ('line', 'Line'), ('area', 'Area'), ('bar', 'Bar'),
                                   ('stackbar', 'Stack Bar'), ('hbar', 'Horizontal Bar'), ('pie', 'Pie'),
                                   ('donut', 'Donut')], string='Block Type', required=True)
    block_size = fields.Selection([('6col', '1/6 (Suitable for Large Screen)'), ('4col', '1/4 (Suitable for Tile Block)'), ('3col', '1/3'),
                                   ('2col', '1/2'), ('1col', 'Full Screen')], string='Block Size', required=True)
    data_source = fields.Selection([('query', 'Configuration (Query)'), ('function', 'Function (Python)')],
                                   string='Data Source', required=True, default='query')
    # TODO: orm
    data_function = fields.Char('Function Name')
    model_id = fields.Many2one('ir.model', 'Model')
    model = fields.Char(related='model_id.model', readonly=True)
    field_id = fields.Many2one('ir.model.fields', 'Measured Field',
                               domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['float','integer','monetary'])]")  # Float / Int / Money
    operation = fields.Selection([('count', 'Count'), ('sum', 'Sum'),
                                  ('average', 'Average')], string='Operation', required=True, default='sum')

    # Group is for Chart only
    group_field_id = fields.Many2one('ir.model.fields', 'Group By',
                                     domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    group_field_id_model_name = fields.Char(
        'Group By Model', related='group_field_id.relation')
    group_relation_field_id = fields.Many2one('ir.model.fields', ' ',
                                              domain="[('store', '=', True), ('model_id.model', '=', group_field_id_model_name), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    group_field_ttype = fields.Selection(
        related='group_field_id.ttype', readonly=1)
    group_date_format = fields.Selection([('day', 'Day'), ('week', 'Week'),
                                          ('month', 'Month'), ('year', 'Year')],
                                         string='Date Format')
    show_group = fields.Boolean('Show Group If Empty')
    group_limit = fields.Integer('Limit')
    group_limit_selection = fields.Selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '7'), (8, '8'), (9, '9'),
                                            (10, '10'), (15, '15'), (20, '20'), (30, '30')])
    show_group_others = fields.Boolean('Show Others')

    subgroup_field_id = fields.Many2one('ir.model.fields', 'Sub Group By',
                                        domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    subgroup_field_id_model_name = fields.Char(
        'Sub Group By Model', related='subgroup_field_id.relation')
    subgroup_relation_field_id = fields.Many2one('ir.model.fields', ' ',
                                                 domain="[('store', '=', True), ('model_id.model', '=', subgroup_field_id_model_name), ('ttype', 'in', ['char','date','datetime','many2one','boolean','selection'])]")
    subgroup_field_ttype = fields.Selection(
        related='subgroup_field_id.ttype', readonly=1)
    subgroup_date_format = fields.Selection([('day', 'Day'), ('week', 'Week'),
                                             ('month', 'Month'), ('year', 'Year')],
                                            string='Sub Group Date Format')
    show_subgroup = fields.Boolean('Show Sub Group If Empty')
    subgroup_limit = fields.Integer('Limit')
    subgroup_limit_selection = fields.Selection([(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '7'), (8, '8'), (9, '9'),
                                            (10, '10'), (15, '15'), (20, '20'), (30, '30')])
    show_subgroup_others = fields.Boolean('Show Others')

    # Domain, Limit, Sort
    time_calculation_method = fields.Selection([('normal', 'Normal'), ('cumulative', 'Cumulative'),
        ('before', 'Cumulative from before')], string='Calculation Method', default='normal')
    domain_date_field_id = fields.Many2one('ir.model.fields', 'Date Field', domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]")
    domain_date = fields.Selection([('today', 'Today'), ('this_week', 'This Week'),
                                    ('this_month', 'This Month'), ('this_year', 'This Year'),
                                    ('last_two_months', 'Last 2 Months'), ('last_three_months', 'Last 3 Months'),
                                    ('last_month', 'Last Month'), ('last_10', 'Last 10 Days'), 
                                    ('last_30', 'Last 30 Days'), ('last_60', 'Last 60 Days'),
                                    ('before_today', 'Before Today'), ('after_today', 'After Today'),
                                    ('before_and_today', 'Before and Today'), ('today_and_after', 'Today and After')],
                                   string='Date Filter')
    domain = fields.Char('Domain', required=False, default='')
    domain_values_field_id = fields.Many2one('ir.model.fields', 'Domain Values Field', domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char', 'many2one', 'integer', 'float'])]")
    domain_values_string = fields.Text('Domain Values String')
    subdomain_values_field_id = fields.Many2one('ir.model.fields', 'Domain Values Field', domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['char', 'many2one', 'integer', 'float'])]")
    subdomain_values_string = fields.Text('Domain Values String')
    domain_line_ids = fields.One2many('web.domain.line', 'block_id', 'Domains')
    barang_masuk_id = fields.Many2one('barang.masuk', 'Barang Masuk')
    limit = fields.Integer('Limit', default=0)
    sort_by = fields.Many2one('ir.model.fields', 'Sort By')
    sort = fields.Selection([('asc', 'ASC'), ('desc', 'DESC')],
                                string='Sort', required=True, default="desc")
    others_operation = fields.Selection([('count', 'Count'), ('sum', 'Sum'),
                                         ('average', 'Average')], string='Others Operation', required=True, default="average")

    active = fields.Boolean('Active', required=True, default=True)
    menu_id = fields.Many2one('ir.ui.menu', 'Linked Menu')
    link = fields.Char('URL')
    show_metadata = fields.Boolean('Show Metadata')
    sequence = fields.Integer('Sequence')

    # Styling
    tile_color = fields.Selection([
        ('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'), ('purple', 'Purple'),
    ], string='Tile Color')
    tile_icon = fields.Char('Tile Icon')

    @api.onchange('block_type')
    def _change_block_type(self):
        for block in self:
            if block.block_type == 'tile':
                block.block_size = '4col'
            else:
                block.block_size = '2col'

    # Format Return
    # [{'Value': 102.78}] For Tile
    # [{'Account': 28, 'Value': 102.78}, ] 1 Dimensional
    # [{'Account': 28, 'Date': '01 Jan', 'Value': 102.78}, ] 2 Dimensional
    def get_data_function(self):
        query_result = [] 
        label_field = False
        legend_field = False
        label_ttype = False
        legend_ttype = False
        # TODO: Query aja
        if self.data_function == 'income_vs_expense_per_day':
            query = """
                select aat.name as "Name", to_char(date_trunc('day', aml.date),'MM/DD') as "Date", abs(sum(aml.balance)) as "Value" from account_move_line aml
                left join account_account aa on (aa.id = aml.account_id)
                left join account_account_type aat on (aa.user_type_id = aat.id)
                where date <= CURRENT_DATE
                and date >= CURRENT_DATE - interval '1 month'
                and (aat.name ilike 'Income' or aat.name ilike 'Expenses')
                group by aat.name, aml.date
                order by aat.name,aml.date; """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
            label_field = "Date"
            legend_field = "Name"
            label_ttype = "date"
            legend_ttype = "char"
        if self.data_function == 'bank_cash_payable_receivable_per_day':
            query = """
                select aa.name as "Name", to_char(date_trunc('day', aml.date),'MM/DD') as "Date", abs(sum(aml.balance)) as "Value" from account_move_line aml
                left join account_account aa on (aa.id = aml.account_id)
                left join account_account_type aat on (aa.user_type_id = aat.id)
                where date <= CURRENT_DATE
                and date >= CURRENT_DATE - interval '1 month'
                and (aat.name ilike 'Bank and Cash' or aat.name ilike 'Payable' or aat.name ilike 'Receivable')
                group by aa.name, aml.date
                order by aa.name,aml.date; """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
            label_field = "Date"
            legend_field = "Name"
            label_ttype = "date"
            legend_ttype = "char"
        if self.data_function == 'sales_by_region':
            # Bar
            query = """
                select rcs.name as "Region", sum(so.amount_total) as "Value"
                from sale_order so 
                left join res_partner rp on (so.partner_id = rp.id) 
                left join res_country_state rcs on (rp.state_id = rcs.id)
                where so.date_order <= CURRENT_DATE
                and so.date_order >= CURRENT_DATE - interval '1 month'
                group by rcs.name
                order by "Value" desc; """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
            label_field = "Region"
            label_ttype = "char"
            # legend_field = "Region"
        if self.data_function == 'profit_loss_this_month':
            # Tile
            query = """
            select abs(sum(balance)) as "Value"
            from account_move_line aml
            left join account_account aa on (aml.account_id = aa.id)
            left join account_account_type aat on (aa.user_type_id = aat.id)
            where date <= (date_trunc('month', CURRENT_DATE) + interval '1 month - 1 day')::Date 
            and date >= date_trunc('month', CURRENT_DATE)::Date
            and aat.name ilike '%Income%'; """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
            income_value = 0
            if query_result:
                income_value = query_result[0]['Value'] or 0

            query = """
            select abs(sum(balance)) as "Value"
            from account_move_line aml
            left join account_account aa on (aml.account_id = aa.id)
            left join account_account_type aat on (aa.user_type_id = aat.id)
            where date <= (date_trunc('month', CURRENT_DATE) + interval '1 month - 1 day')::Date 
            and date >= date_trunc('month', CURRENT_DATE)::Date
            and (aat.name ilike '%Expenses%' or aat.name ilike '%Depreciation%' or aat.name ilike '%Cost of Revenue%'); """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
            expense_value = 0
            if query_result:
                expense_value = query_result[0]['Value'] or 0
            query_result = [{'Value': income_value - expense_value}]
        # if self.data_function == 'oustanding_transfer':
            # Tile
        if self.data_function == 'total_overdue_payable':
            # Tile
            query = """
            select abs(sum(balance)) as "Value"
            from account_move_line aml
            left join account_account aa on (aml.account_id = aa.id)
            left join account_account_type aat on (aa.user_type_id = aat.id)
            where date <= CURRENT_DATE
            and aat.name ilike '%Payable%'; """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
        if self.data_function == 'total_overdue_receivable':
            # Tile
            query = """
            select abs(sum(balance)) as "Value"
            from account_move_line aml
            left join account_account aa on (aml.account_id = aa.id)
            left join account_account_type aat on (aa.user_type_id = aat.id)
            where date <= CURRENT_DATE
            and aat.name ilike '%Receivable%'; """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
        # if self.data_function == 'warning_stock_and_average_sales:
            # Stack Bar
        # if self.data_function == 'production_efficiency_per_day':
            # Line
        if self.data_function == 'stock_valuation_per_categ_per_location':
            # Multi Bar
            # sq.quantity for 11, qty for 10
            query = """
                select sw.name as "Location",
                pc.name as "Category", sum(pph.cost * sq.qty) as "Value"
                from stock_quant sq
                left join product_product pp on (pp.id = sq.product_id)
                left join product_template pt on (pt.id = pp.product_tmpl_id)
                left join product_category pc on (pt.categ_id = pc.id)
                left join (SELECT DISTINCT ON (product_id) product_id, cost, id FROM product_price_history ORDER BY product_id, id desc) pph on (pph.product_id = pp.id)
                left join stock_location sl on (sq.location_id = sl.id)
                left join stock_warehouse sw on (sl.id = sw.lot_stock_id)
                where sl.complete_name ilike '%Physical%'
                group by sw.name, pc.name
                order by sw.name, pc.name; """
            request._cr.execute(query)
            query_result = request._cr.dictfetchall()
            label_field = "Location"
            legend_field = "Category"
            label_ttype = "char"
            legend_ttype = "char"

        return query_result, label_field, legend_field, label_ttype, legend_ttype


class DomainLine(models.Model):
    _name = 'web.domain.line'

    block_id = fields.Many2one('web.dashboard.block', 'Block')
    field_id = fields.Many2one('ir.model.fields', 'Field',
                               domain="[('ttype', 'in', ['char', 'selection', 'float', 'integer', 'monetary'])]", required=True)  # Float / Int / Money
    operator = fields.Selection([('=', '='), ('!=', '!='), ('<', '<'), ('>', '>'), ('>=', '>='), ('<=', '<='),
                                 ('like', 'like'), ('ilike', 'ilike'), ('in', 'in'), ('not in', 'not in')],
                                string='Operator', required=True)
    value = fields.Char('Value', required=True, default='')
