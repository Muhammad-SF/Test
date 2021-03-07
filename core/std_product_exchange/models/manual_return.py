# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class ManualReturn(models.Model):
    _name = "manual.return"
    _inherit = ['mail.thread']
    _description = "Product Exchange"

    name = fields.Char(string="Product Exchange", required=True, copy=False, index=True, default=lambda self: _('New'))
    out_picking_ids = fields.One2many('stock.picking', 'out_manual_return_id', 'Outgoing')
    in_picking_ids = fields.One2many('stock.picking', 'in_manual_return_id', 'Incoming')
    origin = fields.Char('Source Document', index=True, help="Reference of the document")
    min_date = fields.Datetime('Scheduled Date', index=True, track_visibility='onchange',
                               help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    max_date = fields.Datetime('Max. Expected Date', index=True, help="Scheduled time for the last part of the shipment to be processed")
    location_id = fields.Many2one('stock.location', "Source Location Zone", readonly=True)
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location Zone", readonly=True)
    manual_lines = fields.One2many('manual.return.line', 'manual_return_id', string="Lines")
    in_picking_type_id = fields.Many2one('stock.picking.type', 'In Picking Type', required=True)
    out_picking_type_id = fields.Many2one('stock.picking.type', 'Out Picking Type', required=True)
    in_picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], related='in_picking_type_id.code', readonly=True)
    out_picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], related='out_picking_type_id.code', readonly=True)

    partner_id = fields.Many2one('res.partner', 'Partner')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('stock.picking'),
                                 index=True, required=True)
    state = fields.Selection([
                            ('draft', 'Draft'),
                            ('confirm', 'Confirm'),
                            ('done', 'Done'),
                            ], default="draft", string="Status")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('manual.return') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('manual.return') or _('New')
        res = super(ManualReturn, self).create(vals)
        print('res.manual_linesres.manual_lines', res.manual_lines)
        if len(res.manual_lines) > 0:
            return res
        else:
            raise ValidationError(_("Please Add Product line"))

    def action_confirm(self):
        return self.write({'state': 'confirm'})

    def action_done(self):
        self.create_stock_picking()
        return self.write({'state': 'done'})

    @api.multi
    def create_stock_picking(self):
        self.location_id = self.env.ref('stock.stock_location_stock').id
        self.location_dest_id = self.env.ref('stock.stock_location_suppliers').id
        stock_picking_obj = self.env['stock.picking']
        picking_data = {
            'location_id': self.location_id.id,
            'partner_id': self.partner_id.id,
            'location_dest_id': self.location_dest_id.id,
            'move_type': 'direct',
            'picking_type_id': self.out_picking_type_id.id,
            'company_id': self.company_id.id,
            'origin': self.name,
            'owner_id': ''
        }
        stock_picking_id = stock_picking_obj.create(picking_data)
        if stock_picking_id:
            move_data = stock_picking_id.move_lines
            for se_line in self.manual_lines:
                new_move = move_data.new()
                new_move.product_id = se_line.product_id.id
                new_move.onchange_product_id()
                new_move.product_uom_qty = se_line.product_uom_qty or 0.0
                new_move.picking_id = stock_picking_id.id
                new_move.ordered_qty = None
                new_move.picking_type_id = self.out_picking_type_id.id
                new_move.company_id = self.company_id.id
                new_move.location_id = self.location_id.id
                new_move.location_dest_id = self.location_dest_id.id
                new_move.manual_return_id = self.id
                stock_picking_id.move_lines = stock_picking_id.move_lines | new_move
            stock_picking_id.action_confirm()
            # stock_picking_id.action_assign()
            # stock_picking_id.do_new_transfer()
            print 'xaxaaaadadadad', move_data
            self.out_picking_ids = [(6, 0, stock_picking_id.ids)]

    def action_view_picking(self):
        out_picking = self.mapped('out_picking_ids')
        action = self.env.ref('stock.action_picking_tree').read()[0]
        if len(out_picking) > 1:
            action['domain'] = [('id', 'in', out_picking.ids)]
        elif len(out_picking) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = out_picking.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_return(self):
        if self.in_picking_ids:
            in_picking = self.mapped('in_picking_ids')
            action = self.env.ref('stock.action_picking_tree').read()[0]
            if len(in_picking) > 1:
                action['domain'] = [('id', 'in', in_picking.ids)]
            elif len(in_picking) == 1:
                action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
                action['res_id'] = in_picking.ids[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
        self.location_id = self.env.ref('stock.stock_location_suppliers').id
        self.location_dest_id = self.env.ref('stock.stock_location_stock').id
        stock_picking_obj = self.env['stock.picking']
        picking_data = {
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'move_type': 'direct',
            'picking_type_id': self.in_picking_type_id.id,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'owner_id': '',
        }
        stock_picking_id = stock_picking_obj.create(picking_data)
        if stock_picking_id:
            move_data = stock_picking_id.move_lines
            for se_line in self.manual_lines:
                new_move = move_data.new()
                new_move.product_id = se_line.product_id.id
                new_move.onchange_product_id()
                new_move.product_uom_qty = se_line.product_uom_qty or 0.0
                new_move.picking_id = stock_picking_id.id
                new_move.ordered_qty = None
                new_move.picking_type_id = self.in_picking_type_id.id
                new_move.company_id = self.company_id.id
                new_move.procure_method = 'make_to_stock'
                new_move.location_id = self.location_id.id
                new_move.in_manual_return_id = self.id
                new_move.location_dest_id = self.location_dest_id.id
                stock_picking_id.move_lines = stock_picking_id.move_lines | new_move
            stock_picking_id.action_confirm()
            # stock_picking_id.action_assign()
            # stock_picking_id.do_new_transfer()
            self.in_picking_ids = [(6, 0, stock_picking_id.ids)]


class ManualReturnLine(models.Model):
    _name = "manual.return.line"

    manual_return_id = fields.Many2one('manual.return', 'Product Exchange')
    product_id = fields.Many2one('product.product', required=True, string="Product")
    product_uom_qty = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0, required=True)
    product_uom = fields.Many2one(
        'product.uom', 'Unit of Measure', required=True)
    partner_id = fields.Many2one(related="manual_return_id.partner_id", string='Partner')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id.id
        self.product_uom_qty = 1.0
        return {'domain': {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}
