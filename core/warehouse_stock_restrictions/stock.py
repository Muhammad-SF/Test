# -*- coding: utf-8 -*-

from odoo import http
from odoo import models, fields, api, _
from odoo.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restrict Location')

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Default Warehouse Operations')

class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        domain = domain or []
        if user.stock_location_ids and not user.has_group('base.group_system') and self.env.context.get('location_filter'):
            domain.extend([('id', 'in', user.stock_location_ids.ids)])
        return super(StockLocation, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env.user
        domain = domain or []
        if user.stock_location_ids and not user.has_group('base.group_system') and self.env.context.get('location_filter'):
            domain.extend([('id', 'in', user.stock_location_ids.ids)])
        return super(StockLocation, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        domain = domain or []
        if user.default_picking_type_ids and not user.has_group('base.group_system') and self.env.context.get('picking_filter'):
            domain.extend([('id', 'in', user.default_picking_type_ids.ids)])
        return super(StockPickingType, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env.user
        domain = domain or []
        if user.default_picking_type_ids and not user.has_group('base.group_system') and self.env.context.get('picking_filter'):
            domain.extend([('id', 'in', user.default_picking_type_ids.ids)])
        return super(StockPickingType, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    # @api.multi
    # def name_get(self):
    #     """ Display 'Warehouse_name: PickingType_name' """
    #     # TDE TODO remove context key support + update purchase
    #     res = super(StockPickingType, self).name_get()
    #     if not self.env.context.get('params'):
    #         res = []
    #         for picking_type in self:
    #             if ('IN' in picking_type.name.split() or 'In' in picking_type.name.split()) \
    #                 and picking_type.default_location_dest_id:
    #                 name = picking_type.default_location_dest_id.name_get()[0][1] + ': ' + picking_type.name
    #             elif ('OUT' in picking_type.name.split() or 'Out' in picking_type.name.split()) \
    #                 and picking_type.default_location_src_id:
    #                 name = picking_type.default_location_src_id.name_get()[0][1] + ': ' + picking_type.name
    #             elif (picking_type.default_location_dest_id == 0 and picking_type.default_location_src_id != 0) :
    #                 name = picking_type.default_location_src_id.name_get()[0][1] + ': ' + picking_type.name
    #             elif (picking_type.default_location_src_id == 0 and picking_type.default_location_dest_id != 0):
    #                 name = picking_type.default_location_dest_id.name_get()[0][1] + ': ' + picking_type.name
    #             else :
    #                 name = picking_type.warehouse_id.name + ': ' + picking_type.name
    #             res.append((picking_type.id, name))
    #         return res
    #     else:
    #         return res

class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.one
    @api.constrains('state', 'location_id', 'location_dest_id')
    def check_user_location_rights(self):
        if self.state == 'draft':
            return True
        user_locations = self.env.user.stock_location_ids
        if self.env.user.restrict_locations:
            message = _(
                'Invalid Location. You cannot process this move since you do '
                'not control the location "%s". '
                'Please contact your Adminstrator.')
            if self.location_id not in user_locations:
                raise Warning(message % self.location_id.name)
            elif self.location_dest_id not in user_locations:
                raise Warning(message % self.location_dest_id.name)


