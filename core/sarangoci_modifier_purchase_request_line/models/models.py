# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class purchase_order(models.Model):
    _inherit = "purchase.order"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        type_id = None
        if self.env.user.branch_id:
            type_id = self.env.user.branch_id.warehouse_id
        else:
            return super(purchase_order, self)._default_picking_type()
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', type_id.id)])
        if types:
            return types[:1]
        else:
            return super(purchase_order,self)._default_picking_type()

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True,
                                      default=_default_picking_type,
                                      help="This will determine picking type of incoming shipment")

class purchase_request(models.Model):
    _inherit = "purchase.request"

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        type_id = None
        if self.env.user.branch_id:
            type_id = self.env.user.branch_id.warehouse_id
        else:
            return super(purchase_request, self)._default_picking_type()
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', type_id.id)])
        if types:
            return types[:1]
        else:
            return super(purchase_request,self)._default_picking_type()



    @api.multi
    def button_to_approve(self):
        lines = self.line_ids
        for line in lines:
            if line.branch_id != lines[0].branch_id:
                raise UserError(_('Branch of purchase order should be same.'))
        res = super(purchase_request, self).button_to_approve()
        return res

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True,
                                      default=_default_picking_type,
                                      help="This will determine picking type of incoming shipment")

class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    received_quantity = fields.Float(compute='_get_received_quantity')
    branch_id = fields.Many2one('res.branch', 'Branch',related='request_id.branch_id')

    # @api.model
    # def _get_default_branch(self):
    #     return self.request_id.branch_id

    def _get_received_quantity(self):
        for record in self:
            if record.purchase_lines:
                for po_line in record.purchase_lines:
                    if po_line.qty_received:
                        record.received_quantity += po_line.qty_received


