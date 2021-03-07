# -*- coding: utf-8 -*-

import datetime,calendar

from odoo import models, fields, api

class CommissionScheme(models.Model):
    _name = 'commission.scheme'
    _description = 'Commission Scheme'

    name = fields.Char(string='Name')
    target_type = fields.Selection(
        string='Target Type',
        selection=[
            ('amount', 'Amount'),
            ('qty', 'Qty'),
        ], default='amount'
    )
    based_on = fields.Selection(
        string='Based On',
        selection=[
            ('so', 'SO'),
            ('invoice', 'Invoice'),
            ('payment', 'Payment'),
        ], default='so'
    )
    start_date = fields.Date(string='Applicable From')
    end_date = fields.Date(string='Applicable To')
    description = fields.Text(string='Description')
    commission_scheme_product_ids = fields.One2many(
        comodel_name='commission.scheme.product',
        inverse_name='commission_scheme_id',
        string='Commission Scheme Product'
    )
    commission_scheme_product_category_ids = fields.One2many(
        comodel_name='commission.scheme.productcategory',
        inverse_name='commission_scheme_id',
        string='Commission Scheme Product'
    )
    commission_scheme_total_sales_ids = fields.One2many(
        comodel_name='commission.scheme.total.sales',
        inverse_name='commission_scheme_id',
        string='Commission Scheme Total Sales'
    )
    interval = fields.Selection(
        string='Interval',
        selection=[
            ('daily', 'Daily'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('transaction', 'Transaction'),
        ], default='monthly'
    )

    @api.multi
    def update_interval(self):
        this_month = datetime.datetime.now().month
        this_year = datetime.datetime.now().year
        last_date = calendar.monthrange(this_year, this_month)[1]
        if self.interval=='yearly':
            self.start_date = datetime.date(this_year, 1, 1)
            self.end_date = datetime.date(this_year, 12, 31)
        elif self.interval=='monthly':
            self.start_date = datetime.date(this_year, this_month, 1)
            self.end_date = datetime.date(this_year, this_month, last_date)
        elif self.interval=='daily':
            self.start_date = datetime.datetime.today()
            self.end_date = datetime.datetime.today()
        else:
            self.start_date = False
            self.end_date = False
        
        print"Intervals Updated!"
        # \nNew interval set from ", self.start_date, " to ", self.end_date, " for ", self.name
        
        for pc in self.commission_scheme_product_category_ids:
            if pc.reached >= pc.target:
                pc.reached = 0.0
        
        for p in self.commission_scheme_product_ids:
            if p.reached  >= p.target:
                p.reached = 0.0

    

    @api.onchange('interval')
    def _onchange_interval(self):
        this_month = datetime.datetime.now().month
        this_year = datetime.datetime.now().year
        last_date = calendar.monthrange(this_year, this_month)[1]
        if self.interval=='yearly':
            self.start_date = datetime.date(this_year, 1, 1)
            self.end_date = datetime.date(this_year, 12, 31)
        elif self.interval=='monthly':
            self.start_date = datetime.date(this_year, this_month, 1)
            self.end_date = datetime.date(this_year, this_month, last_date)
        elif self.interval=='daily':
            self.start_date = datetime.datetime.today()
            self.end_date = datetime.datetime.today()
        else:
            self.start_date = False
            self.end_date = False
