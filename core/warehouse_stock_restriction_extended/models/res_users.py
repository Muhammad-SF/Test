# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class WarehouseStockRestriction(models.Model):
    _name = 'warehouse.stock.restriction'

    user_id = fields.Many2one('res.users', string='User', default=lambda self:self.env.user.id)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string='Locations')
    picking_type_ids = fields.Many2many('stock.picking.type', string='Operations')
    filter_warehouse_ids = fields.Many2many('stock.warehouse', 'warehouse_restriction_stock_warehouse_rel', 'warehouse_id', 'restriction_id', 
                        compute='_get_filter_data', store=False)

    @api.depends('user_id')
    def _get_filter_data(self):
        for record in self:
            stock_warehouse_ids = self.env['stock.warehouse'].search([('branch_id', '=', record.user_id.branch_id.id), 
                                    ('company_id', '=', record.user_id.company_id.id)])
            if stock_warehouse_ids:
                record.filter_warehouse_ids = [(6, 0, stock_warehouse_ids.ids)]
            else:
                record.filter_warehouse_ids = [(6, 0, [])]

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        """
        Make warehouse compatible with company
        """
        location_ids = []
        if self.warehouse_id:
            location_obj = self.env['stock.location']
            store_location_id = self.warehouse_id.view_location_id.id
            addtional_ids = location_obj.search([('location_id', 'child_of', store_location_id), ('usage', '=', 'internal'), ('branch_id', '=', self.user_id.branch_id.id), 
                                    ('company_id', '=', self.user_id.company_id.id)])
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

    @api.onchange('is_admin')
    def _check_is_admin(self):
        print self.env.user.id
        if self.is_admin:
            self.restrict_locations=False

    @api.multi
    def write(self, vals):
        print self.env.user.id
        if self.id == 1:
            vals['is_admin'] = 1
        if 'is_admin' in vals:
            vals['restrict_locations'] = False
        res = super(ResUsers, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        if self.id == 1:
            vals['is_admin'] = 1
        if vals.get('is_admin'):
            vals['restrict_locations'] = False
        return super(ResUsers, self).create(vals)
        
    @api.depends('warehouse_location_operation_ids', 'warehouse_location_operation_ids.picking_type_ids')
    def _get_picking_type_ids(self):
        for record in self:
            picking_type_ids = record.warehouse_location_operation_ids.mapped('picking_type_ids').ids
            record.default_picking_type_ids = [(6, 0, picking_type_ids)]

class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations:
            domain.extend([('id', 'in', user.warehouse_location_operation_ids.mapped('warehouse_id.id'))])
        return super(Warehouse, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations:
            domain.extend([('id', 'in', user.warehouse_location_operation_ids.mapped('warehouse_id.id'))])
        return super(Warehouse, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations:
            domain.extend([('picking_type_id', 'in', user.warehouse_location_operation_ids.mapped('picking_type_ids').ids)])
        return super(Picking, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations:
            domain.extend([('picking_type_id', 'in', user.warehouse_location_operation_ids.mapped('picking_type_ids').ids)])
        return super(Picking, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations:
            domain.extend([('picking_type_id', 'in', user.warehouse_location_operation_ids.mapped('picking_type_ids').ids)])
        return super(StockMove, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations:
            domain.extend([('picking_type_id', 'in', user.warehouse_location_operation_ids.mapped('picking_type_ids').ids)])
        return super(StockMove, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

# class MaterialRequest(models.Model):
#     _inherit = 'std.material.request'


# class MaterialRequestLine(models.Model):
#     _inherit = 'std.item.mr'

