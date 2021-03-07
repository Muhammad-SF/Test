
from odoo import models, fields, api, _
from odoo import http
# from lxml import etree

 
class ResUsers(models.Model):
    _inherit = 'res.users'

    is_admin = fields.Boolean(string='is Administrator')
    # uid = fields.Many2one('res.users', string='uid',compute='_get_current_user')
    uid = fields.Char(string='uid',compute='_get_current_user')


    @api.depends('uid')
    def _get_current_user(self):
        for a in self:
            a.uid = a.env.user.id


# class Warehouse(models.Model):
#     _inherit = 'stock.warehouse'

#     @api.model
#     def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('id', 'in', user.warehouse_location_operation_ids.mapped('warehouse_id.id'))])
#         return super(Warehouse, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('id', 'in', user.warehouse_location_operation_ids.mapped('warehouse_id.id'))])
#         return super(Warehouse, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

# class Picking(models.Model):
#     _inherit = 'stock.picking'

#     @api.model
#     def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('picking_type_id', 'in', user.warehouse_location_operation_ids.mapped('picking_type_ids').ids)])
#         return super(Picking, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('picking_type_id', 'in', user.warehouse_location_operation_ids.mapped('picking_type_ids').ids)])
#         return super(Picking, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

# class StockLocation(models.Model):
#     _inherit = 'stock.location'

#     @api.model
#     def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('id', 'in', user.stock_location_ids.ids)])
#         return super(StockLocation, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('id', 'in', user.stock_location_ids.ids)])
#         return super(StockLocation, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)



# class StockPickingType(models.Model):
#     _inherit = 'stock.picking.type'

#     @api.model
#     def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('id', 'in', user.default_picking_type_ids.ids)])
#         return super(StockPickingType, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         user = self.env.user
#         domain = domain or []
#         if not user.is_admin and user.restrict_locations:
#             domain.extend([('id', 'in', user.default_picking_type_ids.ids)])
#         return super(StockPickingType, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
