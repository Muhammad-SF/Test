# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api

class Commission(models.Model):
    _name = 'commission.commission'
    _description = 'Commission'

    salesperson = fields.Char(string='Salesperson')
    sales_team = fields.Char(string='Sales Team')
    so_reference = fields.Char(string='SO Reference')
    invoice_reference = fields.Char(string='Invoice Reference')
    payment_reference = fields.Char(string='Payment Reference')
    date = fields.Date(string='Date')
    commission_calculation_type = fields.Char(string='Commission Calculation Type')
    commission_line = fields.Char(string='Commission Line')
    target_type = fields.Char(string='Target Type')
    commission_scheme_id = fields.Char(string='Commission Scheme ID')
    base_amount = fields.Float(string='Base Amount')
    commission_amount = fields.Float(string='Commission Amount', default=0.0)
    total_sales_min_target = fields.Float(string='Total Sales Min Target', default=0.0)
    total_sales_max_target = fields.Float(string='Total Sales Max Target', default=0.0)
    product_category_min_target = fields.Float(string='Product Category Min Target', default=0.0)
    product_category_max_target = fields.Float(string='Product Category Max Target', default=0.0)
    product_min_target = fields.Float(string='Product Min Target', default=0.0)
    product_max_target = fields.Float(string='Product Max Target', default=0.0)
    total_sales_target_achieved = fields.Float(string='Total Sales Achieved Target', default=0.0)
    product_category_target_achieved = fields.Float(string='Product Category Target Achieved', default=0.0)
    product_target_achieved = fields.Float(string='Product Target Achieved', default=0.0)
    target = fields.Float(string='Target Amount/Qty', default=0.0)
    achieved = fields.Float(string='Achived Amount/Qty', default=0.0)
    interval = fields.Selection(
        string='Interval',
        selection=[
            ('daily', 'Daily'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
            ('transaction', 'Transaction'),
        ]
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    update_reach = fields.Boolean(string='Update Reach', copy=False)
    
    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.entitle_commission()
        return res
    
    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        self.entitle_commission()
        return res
    
    @api.multi
    def entitle_commission(self):
        self._commission_based_on_so()

    @api.multi
    def _create_commission_record(self, commission_vals):
        return self.env['commission.commission'].create(commission_vals)

    @api.multi
    def _commission_based_on_so(self):
        """
        sales person: amount based commission
        """
        if self.order_line and self.user_id and self.team_id:
            # only process further when salesperson and team both are set
            if self.user_id != self.team_id.user_id and self.user_id in self.team_id.member_ids:
                commission_amount = 0.0
                base_amount = 0.0
                total_sales_min_target = 0.0
                total_sales_max_target = 0.0
                product_category_min_target = 0.0
                product_category_max_target = 0.0
                product_min_target = 0.0
                product_max_target = 0.0
                total_sales_target_achieved = 0.0
                product_category_target_achieved = 0.0
                product_target_achieved = 0.0
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.name or '',
                    'invoice_reference': 'N/A',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': self.amount_total,
                    'commission_amount': 0.0,
                    'total_sales_min_target' : 0.0,
                    'total_sales_max_target' : 0.0,
                    'product_category_min_target' : 0.0,
                    'product_category_max_target' : 0.0,
                    'product_min_target' : 0.0,
                    'product_max_target' : 0.0,
                    'total_sales_target_achieved' : 0.0,
                    'product_category_target_achieved' : 0.0,
                    'product_target_achieved' : 0.0,
                    'interval': '',
                    'commission_line': '',
                }
                commissioned_product = []
                commissioned_category = []
                # sales person : has to be member of team
                if self.team_id.commission_scheme_salesperson_id and self.team_id.commission_scheme_salesperson_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesperson_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and scheme.interval == 'transaction':
                            commission_vals['interval'] = scheme.interval
                            if scheme.start_date and scheme.end_date and self.date_order >= scheme.start_date and self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='so':
                                    commission_vals['commission_calculation_type'] = 'SO'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                for line in self.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if product.target <= price_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                for line in self.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if category.target <= price_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if category.percent_of_sales:
                                                        # commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                order_amount = self.amount_untaxed
                                                if total.max_sales >= order_amount >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += order_amount
                                                    base_amount += order_amount
                                                    if total.percent_of_sales:
                                                        # commission_amount += total.commission_amount
                                                        commission_amount += self.amount_total * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                            
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:

                                                print("1")
                                                print(commission_vals)
                                                existing_id.create(commission_vals)
                                            else:
                                                # print("2")
                                                # print(commission_vals)
                                                self._create_commission_record(commission_vals)
    
                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                                if product.target <= qty_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                                if category.target <= qty_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if category.percent_of_sales:
                                                        # commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                order_amount = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.order_line:
                                                    order_amount += line.price_subtotal
                                                    qty_subtotal += line.product_uom_qty
                                                if total.max_sales >= qty_subtotal >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += order_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
    
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:

                                                print("3")
                                                print(commission_vals)
                                                existing_id.create(commission_vals)
                                            else:
                                                # print("4")
                                                # print(commission_vals)


                                                self._create_commission_record(commission_vals)
                        
                        if scheme.interval and scheme.interval != 'transaction':
                            commission_vals['interval'] = scheme.interval
                            scheme.update_interval()
                            order_ids = self.env['sale.order'].search([('confirmation_date','>=',scheme.start_date+' 00:00:00'),('confirmation_date','<=',scheme.end_date+' 23:59:59'),('user_id','=',self.user_id.id),('state','=','sale')])
                            commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                            if scheme.based_on and scheme.based_on=='so':
                                commission_vals['commission_calculation_type'] = 'SO'
                                if scheme.target_type and scheme.target_type=='amount':
                                    commission_vals['target_type'] = 'Amount'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if product.target <= price_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if category.target <= price_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if category.percent_of_sales:
                                                    # commission_amount += category.commission_amount
                                                    commission_amount += self.amount_total * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            order_amount = 0.0
                                            for order in order_ids:
                                                order_amount += order.amount_untaxed
                                            if total.max_sales >= order_amount >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += order_amount
                                                # base_amount += order_amount
                                                if total.percent_of_sales:
                                                    commission_amount = self.amount_total * (total.percent_of_sales / 100)
                                                    print(commission_amount)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:

                                            print("7")
                                            print(commission_vals)
                                            existing_id.create(commission_vals)
                                        else:
                                            # print("8")
                                            # print(commission_vals)

                                            self._create_commission_record(commission_vals)

                                elif scheme.target_type and scheme.target_type=='qty':
                                    # commission on qty
                                    commission_vals['target_type'] = 'Qty'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                            if product.target <= qty_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                            if category.target <= qty_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            order_amount = 0.0
                                            qty_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    order_amount += line.price_subtotal
                                                    qty_subtotal += line.product_uom_qty
                                            if total.max_sales >= qty_subtotal >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += order_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount

                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:

                                            print("5")
                                            print(commission_vals)
                                            existing_id.create(commission_vals)
                                        else:
                                            # print("6")
                                            # print(commission_vals)

                                            self._create_commission_record(commission_vals)

            if self.team_id.user_id or self.user_id == self.team_id.user_id:
                commission_amount = 0.0
                base_amount = 0.0
                total_sales_min_target = 0.0
                total_sales_max_target = 0.0
                product_category_min_target = 0.0
                product_category_max_target = 0.0
                product_min_target = 0.0
                product_max_target = 0.0
                total_sales_target_achieved = 0.0
                product_category_target_achieved = 0.0
                product_target_achieved = 0.0
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.name or '',
                    'invoice_reference': 'N/A',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': self.amount_total,
                    'commission_amount': 0.0,
                    'total_sales_min_target' : 0.0,
                    'total_sales_max_target' : 0.0,
                    'product_category_min_target' : 0.0,
                    'product_category_max_target' : 0.0,
                    'product_min_target' : 0.0,
                    'product_max_target' : 0.0,
                    'total_sales_target_achieved' : 0.0,
                    'product_category_target_achieved' : 0.0,
                    'product_target_achieved' : 0.0,
                    'interval': '',
                    'commission_line':'',
                }
                commissioned_product = []
                commissioned_category = []
                # team leader
                if self.team_id.commission_scheme_salesteamleader_id and self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and scheme.interval == 'transaction':
                            commission_vals['interval'] = scheme.interval
                            if scheme.start_date and scheme.end_date and self.date_order >= scheme.start_date and self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='so':
                                    commission_vals['commission_calculation_type'] = 'SO'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                for line in self.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if product.target <= price_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                for line in self.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if category.target <= price_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                order_amount = self.amount_untaxed
                                                if total.max_sales >= order_amount >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += order_amount
                                                    base_amount += order_amount
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += order_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                            
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:

                                                print("3wwwwwwwwwwwww")

                                                # print("3wwwwwwwwwwwww")

                                                print(commission_vals)

                                                existing_id.create(commission_vals)
                                            else:

                                                print("else")
                                                # print("else")

                                                print(commission_vals)
                                                self._create_commission_record(commission_vals)
                                            for pc in scheme.commission_scheme_product_category_ids:
                                                if pc.reached >= pc.target:
                                                    pc.reached = 0.0
                                            for product in scheme.commission_scheme_product_ids:
                                                if product.reached >= product.target:
                                                    product.reached = 0.0
    
                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                                if product.target <= qty_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                                if category.target <= qty_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                order_amount = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.order_line:
                                                    order_amount += line.price_subtotal
                                                    qty_subtotal += line.product_uom_qty
                                                if total.max_sales >= qty_subtotal >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += order_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
    
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:

                                                print("qwwwwwwwwwwww")
                                                print(commission_vals)
                                                existing_id.create(commission_vals)
                                            else:
                                                # print("222wwwwwwww")
                                                # print(commission_vals)

                                                self._create_commission_record(commission_vals)
                                            for pc in scheme.commission_scheme_product_category_ids:
                                                if pc.reached >= pc.target:
                                                    pc.reached = 0.0
                                            for product in scheme.commission_scheme_product_ids:
                                                if product.reached >= product.target:
                                                    product.reached = 0.0

                        if scheme.interval and scheme.interval != 'transaction':
                            commission_vals['interval'] = scheme.interval
                            scheme.update_interval()
                            user_list = self.team_id.member_ids.ids
                            user_list.append(self.team_id.user_id.id)
                            order_ids = self.env['sale.order'].search([('confirmation_date','>=',scheme.start_date+' 00:00:00'),('confirmation_date','<=',scheme.end_date+' 23:59:59'),('user_id','in',user_list),('state','=','sale')])
                            commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                            if scheme.based_on and scheme.based_on=='so':
                                commission_vals['commission_calculation_type'] = 'SO'
                                if scheme.target_type and scheme.target_type=='amount':
                                    commission_vals['target_type'] = 'Amount'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if product.target <= price_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if category.target <= price_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            order_amount = 0.0
                                            for order in order_ids:
                                                order_amount += order.amount_untaxed
                                            if total.max_sales >= order_amount >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += order_amount
                                                # base_amount += order_amount
                                                if total.percent_of_sales:
                                                    commission_amount = self.amount_total * (total.percent_of_sales / 100)
                                                    print(commission_amount)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved

                                                # commission_vals['base_amount'] = base_amount
                                                print(base_amount)
                                                print(order_amount)
                                                print(order.amount_total)

                                                # commission_vals['base_amount'] = base_amount


                                        
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:

                                            print("asdasdasdas")
                                            print(commission_vals)
                                            existing_id.create(commission_vals)
                                        else:
                                            print("dasdasd")
                                            print(commission_vals)

                                            self._create_commission_record(commission_vals)
                                        for pc in scheme.commission_scheme_product_category_ids:
                                            if pc.reached >= pc.target:
                                                pc.reached = 0.0
                                        for product in scheme.commission_scheme_product_ids:
                                            if product.reached >= product.target:
                                                product.reached = 0.0

                                elif scheme.target_type and scheme.target_type=='qty':
                                    # commission on qty
                                    commission_vals['target_type'] = 'Qty'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                            if product.target <= qty_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if product.percent_of_sales:
                                                    # #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.product_uom_qty
                                            if category.target <= qty_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            order_amount = 0.0
                                            qty_subtotal = 0.0
                                            for order in order_ids:
                                                for line in order.order_line:
                                                    order_amount += line.price_subtotal
                                                    qty_subtotal += line.product_uom_qty
                                            if total.max_sales >= qty_subtotal >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += order_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount

                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            print("qwsdasdas")
                                            print(commission_vals)
                                            existing_id.create(commission_vals)
                                        else:
                                            print("qweasdasd")
                                            print(commission_vals)
                                            self._create_commission_record(commission_vals)
                                        for pc in scheme.commission_scheme_product_category_ids:
                                            if pc.reached >= pc.target:
                                                pc.reached = 0.0
                                        for product in scheme.commission_scheme_product_ids:
                                            if product.reached >= product.target:
                                                product.reached = 0.0
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    update_reach = fields.Boolean(string='Update Reach', copy=False)

    @api.multi
    def entitle_commission(self):
        self._commission_based_on_invoice()
        self._commission_based_on_payment()
        
    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        self.entitle_commission()
        return res
    
    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        self.entitle_commission()
        return res
    
    @api.multi
    def _create_commission_record(self, commission_vals):
        return self.env['commission.commission'].create(commission_vals)

    @api.multi
    def _commission_based_on_invoice(self):
        if self.invoice_line_ids and self.user_id and self.team_id:
            # only process further when salesperson and team both are set
            if self.user_id != self.team_id.user_id and self.user_id in self.team_id.member_ids:
                commissioned_product = []
                commissioned_category = []
                total_sales_min_target = 0.0
                total_sales_max_target = 0.0
                product_category_min_target = 0.0
                product_category_max_target = 0.0
                product_min_target = 0.0
                product_max_target = 0.0
                total_sales_target_achieved = 0.0
                product_category_target_achieved = 0.0
                product_target_achieved = 0.0
                base_amount = 0.0
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': self.amount_total,
                    'commission_amount': 0.0,
                    'total_sales_min_target' : 0.0,
                    'total_sales_max_target' : 0.0,
                    'product_category_min_target' : 0.0,
                    'product_category_max_target' : 0.0,
                    'product_min_target' : 0.0,
                    'product_max_target' : 0.0,
                    'total_sales_target_achieved' : 0.0,
                    'product_category_target_achieved' : 0.0,
                    'product_target_achieved' : 0.0,
                    'interval': '',
                    'commission_line': '',
                }
                commission_amount = 0.0
                # sales person : has to be member of team
                if self.team_id.commission_scheme_salesperson_id and self.team_id.commission_scheme_salesperson_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesperson_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and scheme.interval == 'transaction':
                            commission_vals['interval'] = scheme.interval
                            if scheme.start_date and scheme.end_date and self.date_order >= scheme.start_date and self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='invoice':
                                    commission_vals['commission_calculation_type'] = 'Invoice'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if product.target <= price_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if product.percent_of_sales:
                                                        # #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
    
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if category.target <= price_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = self.amount_untaxed
                                                if total.max_sales >= invoice_amount >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += invoice_amount
                                                    base_amount += invoice_amount
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)
    
                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if product.target <= qty_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if product.percent_of_sales:
                                                        # #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if category.target <= qty_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                                if total.max_sales >= qty_subtotal >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)

                        if scheme.interval and scheme.interval != 'transaction':
                            commission_vals['interval'] = scheme.interval
                            scheme.update_interval()
                            invoice_ids = self.env['account.invoice'].search([('date_invoice','>=',scheme.start_date),('date_invoice','<=',scheme.end_date),('user_id','=',self.user_id.id),('state','=','open')])
                            commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                            if scheme.based_on and scheme.based_on=='invoice':
                                commission_vals['commission_calculation_type'] = 'Invoice'
                                if scheme.target_type and scheme.target_type=='amount':
                                    commission_vals['target_type'] = 'Amount'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if product.target <= price_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if product.percent_of_sales:
                                                    # #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount

                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if category.target <= price_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            for invoice in invoice_ids:
                                                invoice_amount += invoice.amount_untaxed
                                            if total.max_sales >= invoice_amount >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += invoice_amount
                                                base_amount += invoice_amount
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)

                                elif scheme.target_type and scheme.target_type=='qty':
                                    # commission on qty
                                    commission_vals['target_type'] = 'Qty'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if product.target <= qty_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if product.percent_of_sales:
                                                    # #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if category.target <= qty_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                            if total.max_sales >= qty_subtotal >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)
                                        
            if self.team_id.user_id or self.user_id == self.team_id.user_id:
                commissioned_product = []
                commissioned_category = []
                total_sales_min_target = 0.0
                total_sales_max_target = 0.0
                product_category_min_target = 0.0
                product_category_max_target = 0.0
                product_min_target = 0.0
                product_max_target = 0.0
                total_sales_target_achieved = 0.0
                product_category_target_achieved = 0.0
                product_target_achieved = 0.0
                base_amount = 0.0
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': self.amount_total,
                    'commission_amount': 0.0,
                    'total_sales_min_target' : 0.0,
                    'total_sales_max_target' : 0.0,
                    'product_category_min_target' : 0.0,
                    'product_category_max_target' : 0.0,
                    'product_min_target' : 0.0,
                    'product_max_target' : 0.0,
                    'total_sales_target_achieved' : 0.0,
                    'product_category_target_achieved' : 0.0,
                    'product_target_achieved' : 0.0,
                    'interval' : '',
                    'commission_line':'',
                }
                commission_amount = 0.0
                # team leader
                if self.team_id.commission_scheme_salesteamleader_id and self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and scheme.interval == 'transaction':
                            commission_vals['interval'] = scheme.interval
                            if scheme.start_date and scheme.end_date and self.date_order >= scheme.start_date and self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='invoice':
                                    commission_vals['commission_calculation_type'] = 'Invoice'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if product.target <= price_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if product.percent_of_sales:
                                                        ##commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if category.target <= price_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = invoice.amount_total
                                                if total.max_sales >= invoice_amount >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += invoice_amount
                                                    base_amount += invoice_amount
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)
                                            for pc in scheme.commission_scheme_product_category_ids:
                                                if pc.reached >= pc.target:
                                                    pc.reached = 0.0
                                            for product in scheme.commission_scheme_product_ids:
                                                if product.reached >= product.target:
                                                    product.reached = 0.0
    
                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if product.target <= qty_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if product.percent_of_sales:
                                                        ##commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if category.target <= qty_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                                if total.max_sales >= qty_subtotal >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)
                                            for pc in scheme.commission_scheme_product_category_ids:
                                                if pc.reached >= pc.target:
                                                    pc.reached = 0.0
                                            for product in scheme.commission_scheme_product_ids:
                                                if product.reached >= product.target:
                                                    product.reached = 0.0

                        if scheme.interval and scheme.interval != 'transaction':
                            commission_vals['interval'] = scheme.interval
                            scheme.update_interval()
                            user_list = self.team_id.member_ids.ids
                            user_list.append(self.team_id.user_id.id)
                            invoice_ids = self.env['account.invoice'].search([('date_invoice','>=',scheme.start_date),('date_invoice','<=',scheme.end_date),('user_id','in',user_list),('state','=','open')])
                            commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                            if scheme.based_on and scheme.based_on=='invoice':
                                commission_vals['commission_calculation_type'] = 'Invoice'
                                if scheme.target_type and scheme.target_type=='amount':
                                    commission_vals['target_type'] = 'Amount'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if product.target <= price_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if category.target <= price_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            for invoice in invoice_ids:
                                                invoice_amount += invoice.amount_total
                                            if total.max_sales >= invoice_amount >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += invoice_amount
                                                base_amount += invoice_amount
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)
                                        for pc in scheme.commission_scheme_product_category_ids:
                                            if pc.reached >= pc.target:
                                                pc.reached = 0.0
                                        for product in scheme.commission_scheme_product_ids:
                                            if product.reached >= product.target:
                                                product.reached = 0.0

                                elif scheme.target_type and scheme.target_type=='qty':
                                    # commission on qty
                                    commission_vals['target_type'] = 'Qty'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if product.target <= qty_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if category.target <= qty_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                            if total.max_sales >= qty_subtotal >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)
                                        for pc in scheme.commission_scheme_product_category_ids:
                                            if pc.reached >= pc.target:
                                                pc.reached = 0.0
                                        for product in scheme.commission_scheme_product_ids:
                                            if product.reached >= product.target:
                                                product.reached = 0.0
    
    @api.multi
    def _commission_based_on_payment(self):
        if self.invoice_line_ids and self.user_id and self.team_id:
            # only process further when salesperson and team both are set
            if not self.user_id == self.team_id.user_id and self.user_id in self.team_id.member_ids:
                commissioned_product = []
                commissioned_category = []
                total_sales_min_target = 0.0
                total_sales_max_target = 0.0
                product_category_min_target = 0.0
                product_category_max_target = 0.0
                product_min_target = 0.0
                product_max_target = 0.0
                total_sales_target_achieved = 0.0
                product_category_target_achieved = 0.0
                product_target_achieved = 0.0
                base_amount = 0.0
                all_payment_references = ""
                for payment in self.payment_ids:
                    if payment.state == 'posted':
                        all_payment_references += (payment.name + ", ")
                all_payment_references = all_payment_references.rstrip(', ')
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': all_payment_references or '',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': self.amount_total,
                    'commission_amount': 0.0,
                    'total_sales_min_target' : 0.0,
                    'total_sales_max_target' : 0.0,
                    'product_category_min_target' : 0.0,
                    'product_category_max_target' : 0.0,
                    'product_min_target' : 0.0,
                    'product_max_target' : 0.0,
                    'total_sales_target_achieved' : 0.0,
                    'product_category_target_achieved' : 0.0,
                    'product_target_achieved' : 0.0,
                    'interval': '',
                    'commission_line': '',
                }
                commission_amount = 0.0
                # sales person : has to be member of team
                if self.team_id.commission_scheme_salesperson_id and self.team_id.commission_scheme_salesperson_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesperson_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and scheme.interval == 'transaction':
                            commission_vals['interval'] = scheme.interval
                            if scheme.start_date and scheme.end_date and self.date_order >= scheme.start_date and self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='payment':
                                    commission_vals['commission_calculation_type'] = 'Payment'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if product.target <= price_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
    
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if category.target <= price_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = invoice.amount_total
                                                if total.max_sales >= invoice_amount >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += invoice_amount
                                                    base_amount += invoice_amount
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)
    
                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if product.target <= qty_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if category.target <= qty_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                                if total.max_sales >= qty_subtotal >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)

                        if scheme.interval and scheme.interval != 'transaction':
                            commission_vals['interval'] = scheme.interval
                            scheme.update_interval()
                            invoice_ids = self.env['account.invoice'].search([('date_invoice','>=',scheme.start_date),('date_invoice','<=',scheme.end_date),('user_id','=',self.user_id.id),('state','=','paid')])
                            commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                            if scheme.based_on and scheme.based_on=='payment':
                                commission_vals['commission_calculation_type'] = 'Payment'
                                if scheme.target_type and scheme.target_type=='amount':
                                    commission_vals['target_type'] = 'Amount'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if product.target <= price_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount

                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if category.target <= price_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            for invoice in invoice_ids:
                                                invoice_amount += invoice.amount_total
                                            if total.max_sales >= invoice_amount >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += invoice_amount
                                                base_amount += invoice_amount
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)

                                elif scheme.target_type and scheme.target_type=='qty':
                                    # commission on qty
                                    commission_vals['target_type'] = 'Qty'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if product.target <= qty_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if category.target <= qty_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                            if total.max_sales >= qty_subtotal >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)
                
            if self.team_id.user_id or self.user_id == self.team_id.user_id:
                commissioned_product = []
                commissioned_category = []
                total_sales_min_target = 0.0
                total_sales_max_target = 0.0
                product_category_min_target = 0.0
                product_category_max_target = 0.0
                product_min_target = 0.0
                product_max_target = 0.0
                total_sales_target_achieved = 0.0
                product_category_target_achieved = 0.0
                product_target_achieved = 0.0
                base_amount = 0.0
                all_payment_references = ""
                for payment in self.payment_ids:
                    if payment.state == 'posted':
                        all_payment_references += (payment.name + ", ")
                all_payment_references = all_payment_references.rstrip(', ')
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': all_payment_references or '',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': self.amount_total,
                    'commission_amount': 0.0,
                    'total_sales_min_target' : 0.0,
                    'total_sales_max_target' : 0.0,
                    'product_category_min_target' : 0.0,
                    'product_category_max_target' : 0.0,
                    'product_min_target' : 0.0,
                    'product_max_target' : 0.0,
                    'total_sales_target_achieved' : 0.0,
                    'product_category_target_achieved' : 0.0,
                    'product_target_achieved' : 0.0,
                    'interval': '',
                    'commission_line':'',
                }
                commission_amount = 0.0
                # team leader
                if self.team_id.commission_scheme_salesteamleader_id and self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and scheme.interval == 'transaction':
                            commission_vals['interval'] = scheme.interval
                            if scheme.start_date and scheme.end_date and self.date_order >= scheme.start_date and self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='payment':
                                    commission_vals['commission_calculation_type'] = 'Payment'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if product.target <= price_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                if category.target <= price_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += price_subtotal
                                                    base_amount += price_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = invoice.amount_total
                                                if total.max_sales >= invoice_amount >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += invoice_amount
                                                    base_amount += invoice_amount
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)
                                            for pc in scheme.commission_scheme_product_category_ids:
                                                if pc.reached >= pc.target:
                                                    pc.reached = 0.0
                                            for product in scheme.commission_scheme_product_ids:
                                                if product.reached >= product.target:
                                                    product.reached = 0.0
    
                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Product'
                                            for product in scheme.commission_scheme_product_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if product.target <= qty_subtotal <= product.max_sales:
                                                    product_min_target = product.target
                                                    product_max_target = product.max_sales
                                                    product_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if product.percent_of_sales:
                                                        #commission_amount += product.commission_amount
                                                        commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += product.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_min_target'] = product_min_target
                                                    commission_vals['product_max_target'] = product_max_target
                                                    commission_vals['product_target_achieved'] = product_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                                            
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Category'
                                            for category in scheme.commission_scheme_product_category_ids:
                                                price_subtotal = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                                if category.target <= qty_subtotal <= category.max_sales:
                                                    product_category_min_target = category.target
                                                    product_category_max_target = category.max_sales
                                                    product_category_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if category.percent_of_sales:
                                                        commission_amount += category.commission_amount
                                                        commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += category.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['product_category_min_target'] = product_category_min_target
                                                    commission_vals['product_category_max_target'] = product_category_max_target
                                                    commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            commission_vals['commission_line'] = 'Total Sales'
                                            for total in scheme.commission_scheme_total_sales_ids:
                                                invoice_amount = 0.0
                                                qty_subtotal = 0.0
                                                for line in self.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                                if total.max_sales >= qty_subtotal >= total.target:
                                                    total_sales_min_target = total.target
                                                    total_sales_max_target = total.max_sales
                                                    total_sales_target_achieved += qty_subtotal
                                                    base_amount += qty_subtotal
                                                    if total.percent_of_sales:
                                                        commission_amount += total.commission_amount
                                                        commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                    else:
                                                        commission_amount += total.commission_amount
                                                    commission_vals['commission_amount'] = commission_amount
                                                    commission_vals['total_sales_min_target'] = total_sales_min_target
                                                    commission_vals['total_sales_max_target'] = total_sales_max_target
                                                    commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                    # commission_vals['base_amount'] = base_amount
                                        
                                        if commission_vals['commission_amount'] >= 0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                      ('sales_team','=',commission_vals['sales_team']),
                                                                                                      ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                      ('target_type','=',commission_vals['target_type']),
                                                                                                      ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                      ('interval','=',commission_vals['interval']),
                                                                                                      ('date','>=',scheme.start_date),
                                                                                                      ('date','<=',scheme.end_date)], limit=1)
                                            if existing_id:
                                                existing_id.create(commission_vals)
                                            else:
                                                self._create_commission_record(commission_vals)
                                            for pc in scheme.commission_scheme_product_category_ids:
                                                if pc.reached >= pc.target:
                                                    pc.reached = 0.0
                                            for product in scheme.commission_scheme_product_ids:
                                                if product.reached >= product.target:
                                                    product.reached = 0.0

                        if scheme.interval and scheme.interval != 'transaction':
                            commission_vals['interval'] = scheme.interval
                            scheme.update_interval()
                            user_list = self.team_id.member_ids.ids
                            user_list.append(self.team_id.user_id.id)
                            invoice_ids = self.env['account.invoice'].search([('date_invoice','>=',scheme.start_date),('date_invoice','<=',scheme.end_date),('user_id','in',user_list),('state','=','paid')])
                            commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                            if scheme.based_on and scheme.based_on=='payment':
                                commission_vals['commission_calculation_type'] = 'Payment'
                                if scheme.target_type and scheme.target_type=='amount':
                                    commission_vals['target_type'] = 'Amount'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if product.target <= price_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                            if category.target <= price_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += price_subtotal
                                                base_amount += price_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            for invoice in invoice_ids:
                                                invoice_amount += invoice.amount_total
                                            if total.max_sales >= invoice_amount >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += invoice_amount
                                                base_amount += invoice_amount
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)
                                        for pc in scheme.commission_scheme_product_category_ids:
                                            if pc.reached >= pc.target:
                                                pc.reached = 0.0
                                        for product in scheme.commission_scheme_product_ids:
                                            if product.reached >= product.target:
                                                product.reached = 0.0

                                elif scheme.target_type and scheme.target_type=='qty':
                                    # commission on qty
                                    commission_vals['target_type'] = 'Qty'
                                    if scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Product'
                                        for product in scheme.commission_scheme_product_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if product.target <= qty_subtotal <= product.max_sales:
                                                product_min_target = product.target
                                                product_max_target = product.max_sales
                                                product_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if product.percent_of_sales:
                                                    #commission_amount += product.commission_amount
                                                    commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                else:
                                                    commission_amount += product.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_min_target'] = product_min_target
                                                commission_vals['product_max_target'] = product_max_target
                                                commission_vals['product_target_achieved'] = product_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                                        
                                    if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Category'
                                        for category in scheme.commission_scheme_product_category_ids:
                                            price_subtotal = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    if category.product_category_id.id == line.product_id.categ_id.id:
                                                        price_subtotal += line.price_subtotal
                                                        qty_subtotal += line.quantity
                                            if category.target <= qty_subtotal <= category.max_sales:
                                                product_category_min_target = category.target
                                                product_category_max_target = category.max_sales
                                                product_category_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if category.percent_of_sales:
                                                    commission_amount += category.commission_amount
                                                    commission_amount += price_subtotal * (category.percent_of_sales / 100)
                                                else:
                                                    commission_amount += category.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['product_category_min_target'] = product_category_min_target
                                                commission_vals['product_category_max_target'] = product_category_max_target
                                                commission_vals['product_category_target_achieved'] = product_category_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if scheme.commission_scheme_total_sales_ids and not scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                        commission_vals['commission_line'] = 'Total Sales'
                                        for total in scheme.commission_scheme_total_sales_ids:
                                            invoice_amount = 0.0
                                            qty_subtotal = 0.0
                                            for invoice in invoice_ids:
                                                for line in invoice.invoice_line_ids:
                                                    invoice_amount += line.price_subtotal
                                                    qty_subtotal += line.quantity
                                            if total.max_sales >= qty_subtotal >= total.target:
                                                total_sales_min_target = total.target
                                                total_sales_max_target = total.max_sales
                                                total_sales_target_achieved += qty_subtotal
                                                base_amount += qty_subtotal
                                                if total.percent_of_sales:
                                                    commission_amount += total.commission_amount
                                                    commission_amount += invoice_amount * (total.percent_of_sales / 100)
                                                else:
                                                    commission_amount += total.commission_amount
                                                commission_vals['commission_amount'] = commission_amount
                                                commission_vals['total_sales_min_target'] = total_sales_min_target
                                                commission_vals['total_sales_max_target'] = total_sales_max_target
                                                commission_vals['total_sales_target_achieved'] = total_sales_target_achieved
                                                # commission_vals['base_amount'] = base_amount
                                    
                                    if commission_vals['commission_amount'] >= 0.0:
                                        commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                        existing_id = self.env['commission.commission'].search([('salesperson','=',commission_vals['salesperson']),
                                                                                                  ('sales_team','=',commission_vals['sales_team']),
                                                                                                  ('commission_calculation_type','=',commission_vals['commission_calculation_type']),
                                                                                                  ('target_type','=',commission_vals['target_type']),
                                                                                                  ('commission_scheme_id','=',commission_vals['commission_scheme_id']),
                                                                                                  ('interval','=',commission_vals['interval']),
                                                                                                  ('date','>=',scheme.start_date),
                                                                                                  ('date','<=',scheme.end_date)], limit=1)
                                        if existing_id:
                                            existing_id.create(commission_vals)
                                        else:
                                            self._create_commission_record(commission_vals)
                                        for pc in scheme.commission_scheme_product_category_ids:
                                            if pc.reached >= pc.target:
                                                pc.reached = 0.0
                                        for product in scheme.commission_scheme_product_ids:
                                            if product.reached >= product.target:
                                                product.reached = 0.0

class AccountPayment(models.Model):
    _inherit = 'account.payment'


    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        active_id = self.env.context.get('active_id')
        invoice = self.env['account.invoice'].browse(active_id)
        invoice.entitle_commission()
        return res
