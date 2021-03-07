# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class WarehouseStockRestriction(models.Model):
    _name = 'warehouse.stock.restriction'

    user_id = fields.Many2one('res.users', string='User')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string='Locations')
    picking_type_ids = fields.Many2many('stock.picking.type', string='Operations')

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        """
        Make warehouse compatible with company
        """
        location_ids = []
        if self.warehouse_id:
            location_obj = self.env['stock.location']
            store_location_id = self.warehouse_id.view_location_id.id
            addtional_ids = location_obj.search([('location_id', 'child_of', store_location_id), ('usage', '=', 'internal')])
            for location in addtional_ids:
                if location.location_id.id not in addtional_ids.ids:
                    location_ids.append(location.id)
            self.location_ids = [(6, 0, location_ids)]
        else:
            self.location_ids = [(6, 0, [])]

    @api.onchange('location_ids')
    def change_location_ids(self):
        operation_ids = []
        if self.location_ids:
            for location_id in self.location_ids:
                picking_operation_ids = self.env['stock.picking.type'].search(['|', ('default_location_src_id', '=', location_id.id), 
                                ('default_location_dest_id', '=', location_id.id)])
                operation_ids.extend(picking_operation_ids.ids)
            self.picking_type_ids = [(6, 0, operation_ids)]
        else:
            self.picking_type_ids = [(6, 0, [])]

class ResUsers(models.Model):
    _inherit = 'res.users'

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations', compute='_get_stock_location_ids', store=True)

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Default Warehouse Operations', compute='_get_picking_type_ids', store=True)

    warehouse_location_operation_ids = fields.One2many('warehouse.stock.restriction', 'user_id', string='Warehouse Restrictions')

    @api.depends('warehouse_location_operation_ids', 'warehouse_location_operation_ids.location_ids')
    def _get_stock_location_ids(self):
        for record in self:
            location_ids = record.warehouse_location_operation_ids.mapped('location_ids').ids
            record.stock_location_ids = [(6, 0, location_ids)]

    @api.depends('warehouse_location_operation_ids', 'warehouse_location_operation_ids.picking_type_ids')
    def _get_picking_type_ids(self):
        for record in self:
            picking_type_ids = record.warehouse_location_operation_ids.mapped('picking_type_ids').ids
            record.default_picking_type_ids = [(6, 0, picking_type_ids)]