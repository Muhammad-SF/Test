# -*- coding: utf-8 -*-

import math
from odoo import models, fields, api
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class StockWarehouseOrderpointLine(models.Model):
    _inherit = 'stock.warehouse.orderpoint.line'

    based_on_run_rate = fields.Boolean(string="Based on Run Rate")
    run_rate_data = fields.Integer(string="Run Rate Data (days)", help="Number of days back to calculate Run Rate Qty")
    run_rate = fields.Float(string="Run Rate Quantity", help="Average outcoming or usage goods during the Run Rate Data (days)", compute='_get_run_rate', store=True)
    run_rate_copy = fields.Float(string="Run Rate Quantity", help="Average outcoming or usage goods during the Run Rate Data (days)")
    stock_days = fields.Float(string="Stock Days", help="Remaining days until the stock runs out")
    stock_days_copy = fields.Float(string="Stock Days", help="Remaining days until the stock runs out")
    qty_on_hand = fields.Float(string="Current Stock Level", help="Available stock in the chosen Location")
    qty_on_hand_copy = fields.Float(string="Current Stock Level", help="Available stock in the chosen Location")

    safe_stock = fields.Float(string="Safety Stock", help="Additional stock to mitigate risk of stockout")
    safe_stock_copy = fields.Float(string="Safety Stock")
    par_level = fields.Boolean(string="Safety Stock", help="Additional stock to mitigate risk of stockout")
    # par_level_type = fields.Selection([('fixed_stock', 'Fixed Stock'), ('coefficient_stock', 'Coefficient Stock'), ('minimal_days', 'Minimal Days')], string="Par Level Type")
    par_level_data = fields.Float(string="Safety Stock Rate", help="Coefficient rate of Safety Stock for the Available Stock")
    product_id = fields.Many2one('product.product')
    location_id = fields.Many2one('stock.location')
    process_day = fields.Integer(compute="compute_process_time", string='Processed Time')
    avg_lead_time = fields.Float(string='Average Lead Time', compute='compute_process_time')
    avg_sales_daily = fields.Integer(string='Average Sales Daily', compute='_get_run_rate', store=True)
    lead_time_demand = fields.Integer(string='Lead Time Demand', compute='_get_lead_time', store=True)

    @api.depends('avg_lead_time', 'avg_sales_daily')
    def _get_lead_time(self):
        for record in self:
            record.lead_time_demand = record.avg_lead_time * record.avg_sales_daily

    @api.depends('run_rate_data')
    def compute_process_time(self):
        for record in self:
            stock_move_obj = self.env['stock.move']
            if record.run_rate_data:
                if record.start_date and record.product_id and record.based_on_run_rate and record.location_id and record.run_rate_data > 0:
                    virtual_scrapped_location = self.env.ref('stock.stock_location_scrapped').id
                    virtual_inventory_adjustment = self.env.ref('stock.location_inventory').id
                    virtual_product_usage = self.env.ref('product_usage.stock_location_product_usage').id
                    start_date = datetime.strptime(record.start_date, DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days=int(record.run_rate_data))
                    end_date = datetime.strptime(record.start_date, DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days=1)
                    stock_move_ids = stock_move_obj.search(
                            [('product_id', '=', record.product_id.id), 
                                ('date', '>=', start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                ('date', '<=', end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                ('state', 'in', ('done', 'processed')),
                                '|',
                                ('picking_type_id.name', '=', 'Receipts'),
                                ('location_dest_id', '=', record.order_point_id.location_id.id)
                            ])
                    process_time = stock_move_ids.filtered(lambda r:r.process_time).mapped('process_time')
                    processed_days = 0
                    for lines in process_time:
                        line = lines.split(' ')
                        days    = int(line[0])
                        hours   = int(line[2])
                        minutes = int(line[4])
                        processed_days += days
                        if hours > 0 or minutes > 0:
                            processed_days += 1
                    record.process_day = processed_days
                    if len(stock_move_ids) > 0:
                        record.avg_lead_time = record.process_day / len(stock_move_ids)

    @api.depends('par_level', 'run_rate_data', 'par_level_data')
    def _get_run_rate(self):
        for record in self:
            stock_move_obj = self.env['stock.move']
            stock_quant_obj = self.env['stock.quant']
            virtual_scrapped_location = self.env.ref('stock.stock_location_scrapped').id
            virtual_inventory_adjustment = self.env.ref('stock.location_inventory').id
            virtual_product_usage = self.env.ref('product_usage.stock_location_product_usage').id
            if record.par_level and record.par_level_data != 0:
                move_qty_location = stock_move_obj.search(
                                        [('product_id', '=', record.product_id.id), 
                                            ('state', 'in', ('done', 'processed')),
                                            '|','|',
                                            ('picking_type_id.name', '=', 'Delivery Orders'),
                                            ('picking_type_id.name', '=', 'Internal Transfer Out'),
                                            ('location_dest_id', 'in', (virtual_product_usage, virtual_inventory_adjustment, virtual_scrapped_location))
                                        ]
                                    )
                total_qty = 0.0
                for move in move_qty_location:
                    total_qty += move.product_uom_qty
                if record.par_level_data != 0:
                    record.run_rate = total_qty / record.par_level_data
                    record.avg_sales_daily = math.floor(record.run_rate)
            if record.run_rate_data:
                if record.start_date and record.product_id and record.based_on_run_rate and record.location_id and record.run_rate_data > 0:
                    start_date = datetime.strptime(record.start_date, DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days=int(record.run_rate_data))
                    end_date = datetime.strptime(record.start_date, DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days=1)
                    move_qty_location = stock_move_obj.search(
                            [('product_id', '=', record.product_id.id), 
                                ('date', '>=', start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                ('date', '<=', end_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                ('state', 'in', ('done', 'processed')),
                                '|','|',
                                ('picking_type_id.name', '=', 'Delivery Orders'),
                                ('picking_type_id.name', '=', 'Internal Transfer Out'),
                                ('location_dest_id', 'in', (virtual_product_usage, virtual_inventory_adjustment, virtual_scrapped_location))
                            ])
                    total_qty = 0.0
                    for move in move_qty_location:
                        if move.product_uom_qty > 0:
                            total_qty += move.product_uom_qty
                    if total_qty > 0:
                        record.run_rate = total_qty / record.run_rate_data
                        record.avg_sales_daily = math.floor(record.run_rate)

    # @api.multi
    # def check_reordering_rules_qty(self):
    #     all_reordering_rules = self.search([])
    #     stock_move_obj = self.env['stock.move']
    #     stock_quant_obj = self.env['stock.quant']

    #     for reorder in all_reordering_rules:
    #         move_qty_location = stock_move_obj.search(
    #             [('product_id', '=', reorder.product_id.id), ('location_id', '=', reorder.location_id.id)])
    #         all_qty_by_location = stock_quant_obj.search(
    #             [('product_id', '=', reorder.product_id.id), ('location_id', '=', reorder.location_id.id)])

    #         total_qty = 0.0
    #         total_onhand_qty = 0.0

    #         for move in move_qty_location:
    #             total_qty += move.product_uom_qty
    #         if reorder.run_rate_data != 0:
    #             reorder.run_rate = total_qty / reorder.run_rate_data
    #             reorder.run_rate_copy = total_qty / reorder.run_rate_data

    #         # qty on hand
    #         for quant in all_qty_by_location:
    #             total_onhand_qty += quant.qty

    #         reorder.qty_on_hand = total_onhand_qty
    #         reorder.qty_on_hand_copy = total_onhand_qty

    #         if reorder.run_rate != 0:
    #             reorder.stock_days = reorder.qty_on_hand / reorder.run_rate
    #             reorder.stock_days_copy = reorder.qty_on_hand / reorder.run_rate

    #         if reorder.based_on_run_rate:
    #             if reorder.run_rate != 0:
    #                 reorder.product_min_qty = reorder.qty_on_hand / reorder.run_rate
    #         if reorder.par_level_type == 'fixed_stock':
    #             if reorder.run_rate != 0:
    #                 reorder.safe_stock = (total_onhand_qty - reorder.par_level_data) / reorder.run_rate
    #                 reorder.safe_stock_copy = (total_onhand_qty - reorder.par_level_data) / reorder.run_rate
    #         if reorder.par_level_type == 'coefficient_stock':
    #             reorder.safe_stock = reorder.run_rate * reorder.par_level_data
    #             reorder.safe_stock_copy = reorder.run_rate * reorder.par_level_data
    #         if reorder.par_level_type == 'minimal_days':
    #             reorder.safe_stock = reorder.par_level_data
    #             reorder.safe_stock_copy = reorder.par_level_data

    # @api.multi
    # @api.onchange('par_level_type')
    # def onchange_par_level_type(self):
    #     # all_reordering_rules = self.search([])
    #     stock_move_obj = self.env['stock.move']
    #     stock_quant_obj = self.env['stock.quant']

    #     move_qty_location = stock_move_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

    #     all_qty_by_location = stock_quant_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

    #     total_qty = 0.0
    #     total_onhand_qty = 0.0

    #     for move in move_qty_location:
    #         total_qty += move.product_uom_qty
    #     if self.run_rate_data != 0:
    #         self.run_rate_copy = total_qty / self.run_rate_data

    #     # qty on hand
    #     for quant in all_qty_by_location:
    #         total_onhand_qty += quant.qty

    #     self.qty_on_hand = total_onhand_qty
    #     self.qty_on_hand_copy = total_onhand_qty

    #     if self.run_rate != 0:
    #         self.stock_days = self.qty_on_hand / self.run_rate
    #         self.stock_days_copy = self.qty_on_hand / self.run_rate

    #     if self.based_on_run_rate:
    #         if self.run_rate != 0:
    #             self.product_min_qty = self.run_rate

    #     if self.par_level_type == 'fixed_stock':
    #         if self.run_rate != 0:
    #             self.safe_stock = (total_onhand_qty - self.par_level_data) / self.run_rate
    #             self.safe_stock_copy = (total_onhand_qty - self.par_level_data) / self.run_rate
    #     if self.par_level_type == 'coefficient_stock':
    #         self.safe_stock = self.run_rate * self.par_level_data
    #         self.safe_stock_copy = self.run_rate * self.par_level_data
    #     if self.par_level_type == 'minimal_days':
    #         self.safe_stock = self.par_level_data
    #         self.safe_stock_copy = self.par_level_data

    @api.onchange('par_level', 'run_rate_data', 'par_level_data')
    def check_reordering_rules_qty(self):
        # all_reordering_rules = self.search([])
        stock_move_obj = self.env['stock.move']
        stock_quant_obj = self.env['stock.quant']
        if self.start_date and self.product_id and self.based_on_run_rate and self.run_rate_data > 0:
            start_date = datetime.strptime(self.start_date, DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days=int(self.run_rate_data))
            move_qty_location = stock_move_obj.search(
                    [('product_id', '=', self.product_id.id), 
                    ('date', '>=', start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                    ('date', '<=', date.today().strftime(DEFAULT_SERVER_DATE_FORMAT))
                    ])
            total_qty = 0.0
            for move in move_qty_location:
                total_qty += move.product_uom_qty
            if total_qty > 0:
                self.run_rate_copy = total_qty / self.run_rate_data


        all_qty_by_location = stock_quant_obj.search(
                [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

        total_onhand_qty = 0.0

        # qty on hand
        for quant in all_qty_by_location:
            total_onhand_qty += quant.qty

        self.qty_on_hand = total_onhand_qty
        self.qty_on_hand_copy = total_onhand_qty

        if self.run_rate != 0:
            self.stock_days = self.qty_on_hand / self.run_rate
            self.stock_days_copy = self.qty_on_hand / self.run_rate

        if self.based_on_run_rate and self.run_rate != 0:
            self.product_min_qty = self.run_rate

        if self.par_level_data != 0 and self.par_level:
            self.product_min_qty = (self.run_rate * self.par_level_data) + self.run_rate

        # if self.par_level_type == 'fixed_stock':
        #     if self.run_rate != 0:
        #         self.safe_stock = (total_onhand_qty - self.par_level_data) / self.run_rate
        #         self.safe_stock_copy = (total_onhand_qty - self.par_level_data) / self.run_rate
        # if self.par_level_type == 'coefficient_stock':
        #     self.safe_stock = self.run_rate * self.par_level_data
        #     self.safe_stock_copy = self.run_rate * self.par_level_data

        # if self.par_level_type == 'minimal_days':
        #     self.safe_stock = self.par_level_data
        #     self.safe_stock_copy = self.par_level_data


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    # based_on_run_rate = fields.Boolean(string="Based on Run Rate")
    # run_rate_data = fields.Integer(string="Run Rate Data")
    # run_rate = fields.Float(string="Run Rate")
    # run_rate_copy = fields.Float(string="Run Rate")
    # stock_days = fields.Float(string="Stock Days")
    # stock_days_copy = fields.Float(string="Stock Days")
    # qty_on_hand = fields.Float(string="Current Stock Level")
    # qty_on_hand_copy = fields.Float(string="Current Stock Level")

    # par_level = fields.Boolean(string="Par Level")
    # par_level_type = fields.Selection([('fixed_stock', 'Fixed Stock'), ('coefficient_stock', 'Coefficient Stock'), ('minimal_days', 'Minimal Days')], string="Par Level Type")
    # safe_stock = fields.Float(string="Safe stock")
    # safe_stock_copy = fields.Float(string="Safe stock")
    # par_level_data = fields.Float(string="Par Level Data")

    # @api.multi
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     res = super(StockWarehouseOrderpoint, self).onchange_product_id()
    #     for line in self:
    #         if line.product_id:
    #             line.qty_on_hand = line.product_id.qty_available
    #             line.qty_on_hand_copy = line.product_id.qty_available
    #     # all_reordering_rules = self.search([])
    #     stock_move_obj = self.env['stock.move']
    #     stock_quant_obj = self.env['stock.quant']

    #     move_qty_location = stock_move_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

    #     all_qty_by_location = stock_quant_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

    #     total_qty = 0.0
    #     total_onhand_qty = 0.0

    #     for move in move_qty_location:
    #         total_qty += move.product_uom_qty
    #     if self.run_rate_data != 0:
    #         self.run_rate = total_qty / self.run_rate_data
    #         self.run_rate_copy = total_qty / self.run_rate_data

    #     # qty on hand
    #     for quant in all_qty_by_location:
    #         total_onhand_qty += quant.qty
    #     self.qty_on_hand = total_onhand_qty
    #     self.qty_on_hand_copy = total_onhand_qty
    #     if self.run_rate != 0:
    #         self.stock_days = self.qty_on_hand / self.run_rate
    #         self.stock_days_copy = self.qty_on_hand / self.run_rate

    #     if self.based_on_run_rate:
    #         if self.run_rate != 0:
    #             self.product_min_qty = self.qty_on_hand / self.run_rate

    #     if self.par_level_type == 'fixed_stock':
    #         if self.run_rate != 0:
    #             self.safe_stock = (total_onhand_qty - self.par_level_data) / self.run_rate
    #             self.safe_stock_copy = (total_onhand_qty - self.par_level_data) / self.run_rate
    #     if self.par_level_type == 'coefficient_stock':
    #         self.safe_stock = self.run_rate * self.par_level_data
    #         self.safe_stock_copy = self.run_rate * self.par_level_data
    #     if self.par_level_type == 'minimal_days':
    #         self.safe_stock = self.par_level_data
    #         self.safe_stock_copy = self.par_level_data
    #     return res


    # @api.multi
    # @api.onchange('par_level_type')
    # def onchange_par_level_type(self):
    #     all_reordering_rules = self.search([])
    #     stock_move_obj = self.env['stock.move']
    #     stock_quant_obj = self.env['stock.quant']

    #     move_qty_location = stock_move_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

    #     all_qty_by_location = stock_quant_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

        
    #     total_qty = 0.0
    #     total_onhand_qty = 0.0

    #     for move in move_qty_location:
    #         total_qty += move.product_uom_qty
        
    #     if self.run_rate_data != 0:
    #         self.run_rate = total_qty / self.run_rate_data
    #         self.run_rate_copy = total_qty / self.run_rate_data

    #     # qty on hand
    #     for quant in all_qty_by_location:
    #         total_onhand_qty += quant.qty

    #     self.qty_on_hand = total_onhand_qty
    #     self.qty_on_hand_copy = total_onhand_qty

    #     if self.run_rate != 0:
    #         self.stock_days = self.qty_on_hand / self.run_rate
    #         self.stock_days_copy = self.qty_on_hand / self.run_rate

    #     if self.based_on_run_rate:
    #         if self.run_rate != 0:
    #             self.product_min_qty = self.qty_on_hand / self.run_rate


    #     if self.par_level_type == 'fixed_stock':
    #         if self.run_rate != 0:
    #             self.safe_stock = (total_onhand_qty - self.par_level_data) / self.run_rate
    #             self.safe_stock_copy = (total_onhand_qty - self.par_level_data) / self.run_rate
        
    #     if self.par_level_type == 'coefficient_stock':
    #         self.safe_stock = self.run_rate * self.par_level_data
    #         self.safe_stock_copy = self.run_rate * self.par_level_data
        
    #     if self.par_level_type == 'minimal_days':
    #         self.safe_stock = self.par_level_data
    #         self.safe_stock_copy = self.par_level_data

    # @api.multi
    # def check_reordering_rules_qty(self):
    #     all_reordering_rules = self.search([])
    #     stock_move_obj = self.env['stock.move']
    #     stock_quant_obj = self.env['stock.quant']

    #     for reorder in all_reordering_rules:
    #         move_qty_location = stock_move_obj.search(
    #             [('product_id', '=', reorder.product_id.id), ('location_id', '=', reorder.location_id.id)])
    #         all_qty_by_location = stock_quant_obj.search(
    #             [('product_id', '=', reorder.product_id.id), ('location_id', '=', reorder.location_id.id)])

    #         total_qty = 0.0
    #         total_onhand_qty = 0.0

    #         for move in move_qty_location:
    #             total_qty += move.product_uom_qty
            
    #         if reorder.run_rate_data != 0:
    #             reorder.run_rate = total_qty / reorder.run_rate_data
    #             reorder.run_rate_copy = total_qty / reorder.run_rate_data

    #         # qty on hand
    #         for quant in all_qty_by_location:
    #             total_onhand_qty += quant.qty

    #         reorder.qty_on_hand = total_onhand_qty
    #         reorder.qty_on_hand_copy = total_onhand_qty

    #         if reorder.run_rate != 0:
    #             reorder.stock_days = reorder.qty_on_hand / reorder.run_rate
    #             reorder.stock_days_copy = reorder.qty_on_hand / reorder.run_rate

    #         if reorder.based_on_run_rate:
    #             if reorder.run_rate != 0:
    #                 reorder.product_min_qty = reorder.qty_on_hand / reorder.run_rate


    #         if reorder.par_level_type == 'fixed_stock':
    #             if reorder.run_rate != 0:
    #                 reorder.safe_stock = (total_onhand_qty - reorder.par_level_data) / reorder.run_rate
    #                 reorder.safe_stock_copy = (total_onhand_qty - reorder.par_level_data) / reorder.run_rate
            
    #         if reorder.par_level_type == 'coefficient_stock':
    #             reorder.safe_stock = reorder.run_rate * reorder.par_level_data
    #             reorder.safe_stock_copy = reorder.run_rate * reorder.par_level_data
            
    #         if reorder.par_level_type == 'minimal_days':
    #             reorder.safe_stock = reorder.par_level_data
    #             reorder.safe_stock_copy = reorder.par_level_data

    # @api.onchange('run_rate_data','par_level_data')
    # def check_reordering_rules_qty(self):
    #     all_reordering_rules = self.search([])
    #     stock_move_obj = self.env['stock.move']
    #     stock_quant_obj = self.env['stock.quant']

    #     move_qty_location = stock_move_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

    #     all_qty_by_location = stock_quant_obj.search(
    #             [('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)])

        
    #     total_qty = 0.0
    #     total_onhand_qty = 0.0

    #     for move in move_qty_location:
    #         total_qty += move.product_uom_qty
        
    #     if self.run_rate_data != 0:
    #         self.run_rate = total_qty / self.run_rate_data
    #         self.run_rate_copy = total_qty / self.run_rate_data

    #     # qty on hand
    #     for quant in all_qty_by_location:
    #         total_onhand_qty += quant.qty

    #     self.qty_on_hand = total_onhand_qty
    #     self.qty_on_hand_copy = total_onhand_qty

    #     if self.run_rate != 0:
    #         self.stock_days = self.qty_on_hand / self.run_rate
    #         self.stock_days_copy = self.qty_on_hand / self.run_rate

    #     if self.based_on_run_rate:
    #         if self.run_rate != 0:
    #             self.product_min_qty = self.qty_on_hand / self.run_rate


    #     if self.par_level_type == 'fixed_stock':
    #         if self.run_rate != 0:
    #             self.safe_stock = (total_onhand_qty - self.par_level_data) / self.run_rate
    #             self.safe_stock_copy = (total_onhand_qty - self.par_level_data) / self.run_rate
        
    #     if self.par_level_type == 'coefficient_stock':
    #         self.safe_stock = self.run_rate * self.par_level_data
    #         self.safe_stock_copy = self.run_rate * self.par_level_data
        
    #     if self.par_level_type == 'minimal_days':
    #         self.safe_stock = self.par_level_data
    #         self.safe_stock_copy = self.par_level_data




    # @api.multi
    # def write(self, vals):
    #     if 'run_rate_copy' in vals:
    #         vals['run_rate']=vals['run_rate_copy']
    #     if 'safe_stock_copy' in vals:
    #         vals['safe_stock']=vals['safe_stock_copy']
    #     if 'stock_days_copy' in vals:
    #         vals['stock_days']=vals['stock_days_copy']
    #     if 'qty_on_hand_copy' in vals:
    #         vals['qty_on_hand']=vals['qty_on_hand_copy']

    #     # Dont allow changing the company_id when account_move_line already exist
        

    #     return super(StockWarehouseOrderpoint, self).write(vals)



    # @api.model
    # def create(self, vals):
    #     if 'run_rate_copy' in vals:
    #         vals['run_rate']=vals['run_rate_copy']
    #     if 'safe_stock_copy' in vals:
    #         vals['safe_stock']=vals['safe_stock_copy']
    #     if 'stock_days_copy' in vals:
    #         vals['stock_days']=vals['stock_days_copy']
    #     if 'qty_on_hand_copy' in vals:
    #         vals['qty_on_hand']=vals['qty_on_hand_copy']
    #     return super(StockWarehouseOrderpoint, self).create(vals)

