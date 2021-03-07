# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import orm

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_procurement_group_by_line(self, line):
        result = super(SaleOrder, self)._prepare_procurement_group_by_line(line)
        # for compatibility with sale_quotation_sourcing
        # if line._get_procurement_group_key()[0] == 8:
        if line.warehouse_id:
                result['name'] += '/' + line.warehouse_id.name
        return result

    SO_STATES = {
        'cancel': [('readonly', True)],
        'progress': [('readonly', True)],
        'manual': [('readonly', True)],
        'shipping_except': [('readonly', True)],
        'invoice_except': [('readonly', True)],
        'done': [('readonly', True)],
    }

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        'Default Warehouse',
        states=SO_STATES,
        help="If no source warehouse is selected on line, "
             "this warehouse is used as default. ")

class SaleOrderLine(orm.Model):
    _inherit = 'sale.order.line'

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        'Source Warehouse',
        help="If a source warehouse is selected, "
             "it will be used to define the route. "
             "Otherwise, it will get the warehouse of "
             "the sale order")

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        result = super(SaleOrderLine, self)._prepare_order_line_procurement(group_id=group_id)
        for line in self:
            if line.warehouse_id:
                result['warehouse_id'] = line.warehouse_id.id
        return result

    @api.multi
    def _get_procurement_group_key(self):
        """ Return a key with priority to be used to regroup lines in multiple
        procurement groups

        """
        priority = 8
        key = super(SaleOrderLine, self)._get_procurement_group_key()
        # Check priority
        if key[0] >= priority:
            return key
        return (priority, self.warehouse_id.id)