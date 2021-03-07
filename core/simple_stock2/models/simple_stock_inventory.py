# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class simple_stock_inventory(models.Model):
    _name = 'simple.stock.inventory'
    _inherit = ['mail.thread', 'barcodes.barcode_events_mixin']
    _description = 'Simple Stock Inventory'
    _order = 'name desc'

    name = fields.Char('Name', size=50, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('simple.stock.inventory'))
    date = fields.Date('Date', default=lambda self: fields.Date.today())
    scan_location_id = fields.Many2one('stock.location', domain=[('usage','=','internal')], string='Scanned Location', required=True)
    line_ids = fields.One2many('simple.stock.inventory.line', 'inventory_id', string='Inventory Details')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], 'Status', readonly=True, default='draft')

    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirmed'})

        for record in self:
            inventory_obj = self.env['stock.inventory']
            line_obj = self.env['stock.inventory.line']

            inventory_vals = {
                'name': record.name,
                'date': record.date,
                'scan_location_id': record.scan_location_id.id,
                'state': 'confirm',
            }
            inventory = inventory_obj.create(inventory_vals)

            for line in self.line_ids:
                vals = {
                    'inventory_id': inventory.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'product_qty': line.product_qty,
                    'location_id': record.scan_location_id.id,
                }
                line_obj.create(vals)

            inventory.action_done()

            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.inventory',
                'target': 'current',
                'res_id': inventory.id,
                'type': 'ir.actions.act_window'
            }

    def on_barcode_scanned(self, barcode):
        products = self.env['product.product'].search(['|',('barcode', '=', barcode),('default_code', '=', barcode)])
        if products:
            corresponding_line = self.line_ids.filtered(lambda r: r.barcode == barcode or r.default_code == barcode)
            if corresponding_line:
                corresponding_line[0].product_qty += 1
            else:
                for product in products:
                    line_data = {
                        'product_id': product.id,
                        'barcode': product.barcode,
                        'product_uom_id': product.uom_id.id,
                        'product_qty': 1,
                        'default_code': product.default_code,
                    }
                    self.line_ids += self.line_ids.new(line_data)
            return

class simple_stock_inventory_line(models.Model):
    _name = 'simple.stock.inventory.line'
    _description = 'Simple Stock Inventory Line'

    inventory_id = fields.Many2one('simple.stock.inventory')
    product_id = fields.Many2one('product.product', string='Product')
    barcode = fields.Char(string='Serial Number')
    default_code = fields.Char(string='SKU')
    product_uom_id = fields.Many2one('product.uom', string='UoM')
    product_qty = fields.Float('Scan Quantity')


