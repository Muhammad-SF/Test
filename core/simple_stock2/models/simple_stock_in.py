# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    picking_id = fields.Many2one(
        'stock.picking',
        string='Stock Picking', required=False
    )

class simple_stock_in(models.Model):
    _name = 'simple.stock.in'
    _inherit = ['mail.thread', 'barcodes.barcode_events_mixin']
    _description = 'Simple Stock In'
    _order = 'name desc'

    name = fields.Char('Name', size=50, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('simple.stock.in'))
    location_id = fields.Many2one('stock.location', 'From', domain=[('usage','=','supplier')], required=True, default=lambda self: self._get_default_location_id())
    to_location_id = fields.Many2one('stock.location', 'To', domain=[('usage','=','internal')], required=True, default=lambda self: self._get_default_to_location_id())
    line_ids = fields.One2many('simple.stock.in.line', 'stock_id', 'Stock Lines')
    remark = fields.Text('Remark')
    create_uid = fields.Many2one('res.users', 'Creator', readonly=True)
    create_date = fields.Datetime('Creation Date', readonly=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    do_number = fields.Char('DO Number')
    date_range = fields.Date('Date Range')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], 'Status', readonly=True, default='draft')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.get('res.company')._company_default_get('crm.helpdesk'))
    total_unit_price = fields.Float(compute='_get_total_unit_price', string='Total Unit Price')
    company_currency = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency', readonly=True)

    latest_product = fields.Many2many('product.product',relation='simple_stock_in_product_product_rel',column1='stock_id',column2='product_id',string='Latest Product In')

    @api.one
    def action_confirm(self):
        self.write({'state': 'confirmed'})
        today = fields.Date.today()
        picking_obj = self.env.get('stock.picking')
        stock_move_obj = self.env.get('stock.move')
        stock_pack_op_obj = self.env.get('stock.pack.operation')
        picking_ids = []
        picking_in = self._get_picking_in()
        stock_change = self.env['stock.change.product.qty']
        # picking_vals = {
        #     'picking_type_id': picking_in.id,
        #     'date': today,
        #     'origin': self.name,
        #     'location_id': self.location_id.id,
        #     'location_dest_id': self.to_location_id.id,
        # }
        # picking = picking_obj.create(picking_vals)
        # picking_ids.append(picking.id)
        move_ids = []

        for line in self.line_ids:
            vals = {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom_id.id,
                'product_uom_qty': line.scan_qty,
                # 'product_uos': line.product_uom_id.id,
                'date': today,
                'date_expected': today,
                'location_id': self.location_id.id,
                'location_dest_id': self.to_location_id.id,
                # 'picking_id': picking.id,
                'partner_id': False,
                'move_dest_id': False,
                'state': 'draft',
                # 'company_id': picking.company_id.id,
                'picking_type_id': picking_in.id,
                'procurement_id': False,
                'origin': self.name,
                'route_ids': picking_in.warehouse_id and [
                    (6, 0, [x.id for x in picking_in.warehouse_id.route_ids])] or [],
                'warehouse_id': picking_in.warehouse_id.id,
                # 'invoice_state': 'none',
            }

            product = line.product_id
            product.qty_available = product.qty_available + line.scan_qty
            stock_change.create({
                'product_id' : product.id,
                'new_quantity' : product.qty_available
            }).change_product_qty()
            move = stock_move_obj.create(vals)
            move_ids.append(move.id)
        # todo_moves = stock_move_obj.browse(move_ids).action_confirm()
        # todo_moves.force_assign()
        for line in self.line_ids:
            pack_vals = {
                # 'picking_id': picking.id,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom_id.id,
                'product_qty': line.scan_qty,
                'qty_done': line.scan_qty,
                'location_id': self.location_id.id,
                'location_dest_id': self.to_location_id.id,
                'date': today,
            }
            if line.lot:
                pack_vals.update({
                    'lot_id': line.lot.id,
                })
            stock_pack_op_obj.create(pack_vals)

    @api.model
    def _get_picking_in(self):
        type_obj = self.env.get('stock.picking.type')
        user_obj = self.env.get('res.users')
        company_id = user_obj.browse(self._uid).company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
            if not types:
                raise UserError(_('Error!'), _("Make sure you have at least an outgoing picking type defined"))
        return types[0]

    def on_barcode_scanned(self, barcode):
        Lot = self.env['stock.production.lot']
        products = self.env['product.product'].search(['|',('barcode', '=', barcode),('default_code', '=', barcode)])
        if products:
            self.latest_product = products
            corresponding_line = self.line_ids.filtered(lambda r: r.barcode == barcode and r.location_id.id == self.to_location_id.id)
            if corresponding_line:
                corresponding_line[0].scan_qty += 1
            else:
                for product in products:
                    line_data = {
                        'product_id': product.id,
                        'barcode': product.barcode,
                        'product_uom_id': product.uom_id.id,
                        'location_id': self.to_location_id.id,
                        'scan_qty': 1,
                        'list_price': product.list_price,
                        'default_code': product.default_code,
                        'unit_price': product.standard_price,
                        'lot': False,
                    }
                    self.line_ids += self.line_ids.new(line_data)
            return
        elif not products:
            lot_id = Lot.search([('name','=',barcode)], limit=1)
            if lot_id:
                lot_product = lot_id.product_id
                self.line_ids.filtered(lambda r: r.product_id.id == lot_product.id)[0].lot = lot_id.id
                correct_lot_line = lot_id.quant_ids.filtered(lambda r: r.location_id.id == self.to_location_id.id)
                if correct_lot_line:
                    correct_lot_line[0].write({'qty': correct_lot_line[0].qty + 1})
                else:
                    quant_data = {
                        'product_id': lot_product.id,
                        'qty': 1,
                        'location_id':self.to_location_id.id,
                        'lot_id': lot_id.id,
                    }
                    new_quant = lot_id.quant_ids.create(quant_data)
                    lot_id.write({'quant_ids': [(4, new_quant.id)]})

                return
            elif not lot_id and self.latest_product:
                for latest_product in self.latest_product:
                    lot_data = {
                        'name' : barcode,
                        'product_id': latest_product.id,
                        'quant_ids' : [
                            (0, 0, {
                                'product_id': latest_product.id,
                                'qty': 1,
                                'location_id': self.to_location_id.id,
                            })],
                    }
                    new_lot = Lot.create(lot_data)
                    self.line_ids.filtered(lambda r: r.product_id.id == latest_product.id)[0].lot = new_lot.id
                return
        location = self.env['stock.location'].search([('barcode', '=', barcode)])
        if location:
            self.location_id = location[0]
            return

    @api.multi
    def _get_total_unit_price(self):
        for record in self:
            total_unit_price = 0.0
            for line in record.line_ids:
                if line.unit_price:
                    total_unit_price = total_unit_price + line.unit_price
            record.total_unit_price = total_unit_price

    @api.model
    def _get_default_location_id(self):
        locations = self.env.get('stock.location').search(
            ['|', ('name', '=', 'Vendors'), ('name', '=', 'Suppliers'), ('usage', '=', 'supplier')], )
        for location in locations:
            return location

    @api.model
    def _get_default_to_location_id(self):
        locations = self.env.get('stock.location').search(['|',('name','=','Stock'),('name','=','Location'),('location_id.name','=','WH'),('usage','=','internal')],)
        for location in locations:
            return location

class simple_stock_in_line(models.Model):
    _name = 'simple.stock.in.line'
    _description = 'Simple Stock In Lines'

    stock_id = fields.Many2one('simple.stock.in', 'Stock')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    barcode = fields.Char(string='Serial Number')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')
    scan_qty = fields.Float('Scanned')
    total_snum = fields.Float('Total Serial Number')
    lot = fields.Many2one('stock.production.lot', 'Lot Number')
    available_qty = fields.Float(related='product_id.qty_available', string='Qty Available', readonly=True)
    location_id = fields.Many2one('stock.location', 'To', default=lambda self: self._get_default_location_id())
    create_uid = fields.Many2one('res.users', 'Creator', readonly=True)
    create_date = fields.Datetime('Creation Date', readonly=True)
    list_price = fields.Float(related='product_id.list_price', string='Sale Price', store=True)
    default_code = fields.Char(string='SKU')
    unit_price = fields.Float('Unit Price')

    @api.model
    def _resolve_location_id_from_context(self):
        """ Returns ID of section based on the value of 'section_id'
            context key, or None if it cannot be resolved to a single
            Sales Team.
        """
        context = self.env.context
        if type(context.get('default_location_id')) in (int, long):
            return context.get('default_location_id')
        if isinstance(context.get('default_location_id'), basestring):
            location_ids = self.env.get('stock.location').name_search(name=context['default_location_id'])
            if len(location_ids) == 1:
                return int(location_ids[0][0])
        return None

    @api.multi
    def _get_default_location_id(self):
        """ Gives default section by checking if present in the context """
        context = self.env.context
        for record in self:
            location_id = self._resolve_location_id_from_context() or False
            if not location_id:
                location_id = self.env.get('res.users').browse(self._uid).default_in_to.id or False
            record.location_id = location_id