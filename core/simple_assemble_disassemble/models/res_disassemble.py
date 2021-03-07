# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from dateutil import tz
import pytz

class ResDisassemble(models.Model):
    _name = 'res.disassemble'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _description = 'Product Disassemble'

    # assemble_id           = fields.Many2one('res.assemble', 'Assemble')
    move_id               = fields.Many2one('stock.move', 'Stock Move')
    material_id           = fields.One2many('disassemble.materials', 'disassemble_id', 'Disassemble', readonly=True, states={'draft': [('readonly', False)]} )
    # material_form_id      = fields.One2many('disassemble.products.form', 'disassemble_id', 'Products to Form', readonly=True, states={'draft': [('readonly', False)]})
    name                  = fields.Char(string='Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', True)]}, index=True, default='New')
    product_id            = fields.Many2one('product.template', 'Product', readonly=True, states={'draft': [('readonly', False)]})
    product_product_id    = fields.Many2one('product.product', compute='_compute_product_id', string='Product (2)')
    quantity_pro          = fields.Integer('Quantity', readonly=True, states={'draft': [('readonly', False)]}, default=1)
    date_disassemble      = fields.Datetime('Date', readonly=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now())
    stock_production_prod = fields.Many2one('stock.production.lot', 'Serial Number/ Lot', readonly=True, states={'draft': [('readonly', False)]})
    location_src_id       = fields.Many2one('stock.location','Location', readonly=True, states={'draft': [('readonly', False)]})
    state                 = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('cancel','Cancelled')
    ], string='Status', default='draft')
    material_id_pending = fields.One2many('disassemble.materials', 'disassemble_id', 'Disassemble')
    total_line_cost = fields.Float('Total Cost')
    tracking = fields.Selection(related="product_id.tracking")
    lot_ids = fields.Many2many("stock.production.lot", compute="_compute_lot_ids")
    account_move_ids = fields.Many2many('account.move')
    move_count = fields.Integer(compute='_get_account_move_count')

    def convert_to_utc(self, utc_datetime):
        timezone_tz = 'Asia/Jakarta'
        if self.env.user and self.env.user.tz:
            timezone_tz = pytz.timezone(self.env.user.tz)
        else:
            timezone_tz = pytz.timezone('Asia/Jakarta')
        date_from =  datetime.datetime.strftime(pytz.utc.localize(
                    datetime.datetime.strptime(utc_datetime, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(timezone_tz),"%Y-%m-%d %H:%M:%S")
        return date_from

    @api.multi
    def _get_account_move_count(self):
        for record in self:
            self.move_count = len(record.account_move_ids)

    @api.multi
    def action_view_journal_entry(self):
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id', 'in', self.account_move_ids.ids)]
        return action

    @api.depends('product_id', 'location_src_id')
    @api.multi
    def _compute_lot_ids(self):
        for rec in self:
            quant_ids = self.env['stock.quant'].search(
                [('product_id', '=', rec.product_id.id), ('location_id', '=', rec.location_src_id.id),
                 ('lot_id', '!=', False)])
            if quant_ids:
                rec.lot_ids = quant_ids.mapped('lot_id')

    @api.multi
    def write(self, vals):
        if self.state == 'pending' and vals.get('material_id_pending'):
            line_total = 0.0
            for line in vals.get('material_id_pending'):
                line_total += line[2]['cost_price'] if line[2] and 'cost_price' in line[2] else 0.0
            if line_total != self.total_line_cost:
                raise UserError('Allocation cost must be equal to Total Cost of Disassemble Product (%s)' %self.total_line_cost)
        return super(ResDisassemble, self).write(vals)


    # @api.onchange('assemble_id')
    # def _onchange_assemble_id(self):
    #     for record in self:
    #         if record.assemble_id:
    #             assemble_quant_available = record.assemble_id.quant_available
    #             if assemble_quant_available > record.assemble_id.quantity_pro:
    #                 assemble_quant_available = record.assemble_id.quantity_pro
    #
    #             record.product_id            = record.assemble_id.product_id
    #             record.stock_production_prod = record.assemble_id.stock_production_prod
    #             record.location_src_id       = record.assemble_id.location_src_id
    #             record.quantity_pro          = assemble_quant_available
    #
    #             # materials = record.material_id.browse([])
    #             # for line in record.assemble_id.material_id:
    #             #     line_data = {
    #             #         'assemble_id' : line.id,
    #             #         'product_id'  : line.product_id and line.product_id.id,
    #             #         'stock_lot'   : line.stock_lot and line.stock_lot.id,
    #             #     }
    #             #     materials += record.material_id.new(line_data)
    #             # record.material_id = materials


    # @api.onchange('quantity_pro')
    # def _onchange_quantity_pro(self):
    #     for record in self:
    #         if self.assemble_id and self.assemble_id.quantity_pro:
    #             assemble_quant_available = self.assemble_id.quant_available
    #             if assemble_quant_available > self.assemble_id.quantity_pro:
    #                 assemble_quant_available = self.assemble_id.quantity_pro
    #
    #             if record.quantity_pro > assemble_quant_available:
    #                 raise UserError('Maximum quantity can disassemble using %s is %s' % (self.assemble_id.name, assemble_quant_available))


    @api.depends('product_id')
    def _compute_product_id(self):
        for record in self:
            product = self.env['product.product'].search([
                ('product_tmpl_id', '=', record.product_id.id)
            ], limit=1)
            record.product_product_id = product.id

    @api.onchange('product_id', 'quantity_pro')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            if self.product_id.material_ids and len(self.product_id.material_ids.ids):
                materials = self.material_id.browse([])
                for material in self.product_id.material_ids:
                    line_data = {
                        'product_id'      : material.product_id and material.product_id.id,
                        'qty_pro'         : material.material_quantity * self.quantity_pro,
                        # 'allocation_cost' : material.allocation_cost,
                    }
                    materials += self.material_id.new(line_data)
                self.material_id = materials

            product_ids   = self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)]).ids
            lot_ids       = self.env['stock.production.lot'].search([('product_id', 'in', product_ids)]).ids
            res['domain'] = {'stock_production_prod': [('id','in',lot_ids)]}
            data = []
            for line in self.product_id.material_ids:
                data.append((0, 0, {
                    'product_id': line.product_id.id,
                    'qty_pro': line.material_quantity * self.quantity_pro
                }))
            self.material_id = data
        return res

    # @api.onchange('material_id')
    # @api.depends('material_id.qty_pro')
    # def onchange_material_id(self):
    #     # Calculating the product_data from the materials
    #     product_data = {}
    #     for line in self.material_id:
    #         if line.product_id.id not in product_data:
    #             product_data.update({line.product_id.id: line.qty_pro})
    #         else:
    #             product_data.update({line.product_id.id: line.qty_pro + product_data.get(line.product_id.id)})
    #
    #     # Find the products that can be formed using the above materials
    #     product_template_ids = self.env['product.template'].search([
    #         ('id', '!=', self.product_id.id),
    #         ('material_ids.product_id', 'in', product_data.keys())
    #     ])
    #
    #     result = []
    #     for template in product_template_ids:
    #         data, check_list = {}, []
    #         # Check new product can be formed using the material
    #         for line in template.material_ids:
    #             if line.product_id.id in product_data and product_data.get(line.product_id.id) >= line.material_quantity:
    #                 check_list.append(True)
    #                 if line.product_id.id not in data:
    #                     data.update({line.product_id.id: line.material_quantity})
    #                 else:
    #                     data.update({line.product_id.id: line.material_quantity + data.get(line.product_id.id)})
    #             else:
    #                 check_list.append(False)
    #         # Check new product can be formed using the materials quantity
    #         product_ok = False
    #         product_count = 1
    #         if all(check_list):
    #             while(product_count):
    #                 check_list2 = []
    #                 for product_id in data:
    #                     if product_data.get(product_id) >= data.get(product_id) * product_count:
    #                         check_list2.append(True)
    #                     else:
    #                         check_list2.append(False)
    #                 if all(check_list2):
    #                     product_ok = True
    #                     product_count += 1
    #                     continue
    #                 else:
    #                     product_count -= 1
    #                     break
    #
    #         # Adding the product to products to form
    #         if product_ok:
    #             materials = ''
    #             for line in template.material_ids:
    #                 materials += line.product_id.name + ' x '+ str(line.material_quantity) + '\n'
    #             product_id = self.env['product.product'].search([('product_tmpl_id','=',template.id)])
    #             if product_id:
    #                 result.append((0,0,{'product_id': product_id.id, 'materials': materials, 'possible_qty': product_count, 'possible_qty_dynamic': product_count}))
    #     self.material_form_id = result

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('res.disassemble') or 'New'
        result = super(ResDisassemble, self).create(vals)
        return result

    # @api.multi
    # def validate_product_to_form(self):
    #     for record in self:
    #         # Total materials
    #         total_product_data = {}
    #         for line in record.material_id:
    #             if line.product_id.id not in total_product_data:
    #                 total_product_data.update({line.product_id.id: line.qty_pro})
    #             else:
    #                 total_product_data.update({line.product_id.id: line.qty_pro + total_product_data.get(line.product_id.id)})
    #         available_product_data = total_product_data.copy()
    #
    #         # Consumed materials
    #         consumed_product_data = {}
    #         for line in record.material_form_id:
    #             for line2 in line.product_id.material_ids:
    #                 if line2.product_id.id not in consumed_product_data:
    #                     consumed_product_data.update({line2.product_id.id: line2.material_quantity * line.quantity})
    #                 else:
    #                     consumed_product_data.update({line2.product_id.id: consumed_product_data.get(line2.product_id.id) + (line2.material_quantity * line.quantity)})
    #
    #         # Available materials
    #         for product_id in consumed_product_data:
    #             available_product_data.update({product_id: available_product_data.get(product_id) - consumed_product_data.get(product_id)})
    #
    #         for product_id in available_product_data:
    #             if available_product_data.get(product_id) < 0.0:
    #                 product_obj = self.env['product.product'].sudo().browse(product_id)
    #                 message = 'Error!\nProducts to Form configuration is incorrect\n\n'
    #                 message += 'Product            : %s' % product_obj.name
    #                 message += '\nTotal Materials  : %s' % total_product_data.get(product_id)
    #                 message += '\nMaterials Needed : %s' % consumed_product_data.get(product_id)
    #                 message += '\nPlease reconfigure to proceed disassemble.'
    #                 raise UserError(message)

    @api.multi
    def action_process(self):
        for record in self:
            if record.location_src_id and record.location_src_id.id:
                available_qty = record.product_product_id.with_context(location=record.location_src_id.id)._product_available().get(record.product_product_id.id, {}).get('qty_available')
            else:
                available_qty = record.product_product_id.qty_available

            if record.quantity_pro > available_qty:
                raise UserError('Quantity greater than the on hand quantity (%s)' % available_qty)

            dest_location = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)

            # Reducing qty of main product
            move_data = {
                'product_id'       : record.product_product_id.id,
                'product_uom_qty'  : record.quantity_pro,
                'product_uom'      : record.product_product_id.uom_id.id,
                'name'             : record.product_product_id.name,
                'date_expected'    : record.date_disassemble or fields.Datetime.now(),
                'procure_method'   : 'make_to_stock',
                'location_id'      : record.location_src_id.id,
                'location_dest_id' : dest_location.id,
                'origin'           : record.name,
                'restrict_lot_id'  : record.stock_production_prod.id or False,
                'date'             : record.date_disassemble,
            }
            move = self.env['stock.move'].create(move_data)
            move.action_confirm()
            move.action_assign()

            cost_price   = 0
            reserved_qty = 0
            for quant in move.reserved_quant_ids:
                cost_price   += quant.inventory_value
                reserved_qty += quant.qty

            total_line_cost = 0.0

            for material in record.material_id:
                component_line = self.env['component.materials'].search([
                    ('component_id', '=', record.product_id.id),
                    ('product_id', '=', material.product_id.id),
                ], limit=1)
                if component_line and component_line.allocation_cost:
                    material.cost_price = 0
                    total_line_cost += (component_line.allocation_cost / 100) * cost_price
                else:
                    material.cost_price = 0

            record.write({
                'move_id' : move and move.id or False,
                'state'   : 'pending',
                'total_line_cost' : total_line_cost
            })
        return True

    @api.multi
    def action_calculate(self):
        for record in self:
            # Step1: Unreserve others
            disassembles = self.search([
                ('product_id', '=', record.product_id and record.product_id.id),
                ('state', '=', 'pending')
            ])
            for disassemble in disassembles:
                if disassemble.move_id and disassemble.move_id.id:
                    disassemble.move_id.do_unreserve()

            record.move_id.action_assign()

            cost_price   = 0
            reserved_qty = 0
            for quant in record.move_id.reserved_quant_ids:
                cost_price   += quant.inventory_value
                reserved_qty += quant.qty

            if record.quantity_pro > reserved_qty:
                raise UserError('Quantity (%s) greater than the reserved quantity (%s)' % (record.quantity_pro, reserved_qty))

            for material in record.material_id:
                component_line = self.env['component.materials'].search([
                    ('component_id', '=', record.product_id.id),
                    ('product_id', '=', material.product_id.id),
                ], limit=1)
                if component_line and component_line.allocation_cost:
                    material.cost_price = (component_line.allocation_cost / 100) * cost_price
                else:
                    material.cost_price = 0

        return True

    @api.multi
    def action_disassemble(self):
        if not self.material_id:
            raise UserError('Can not disassemble without materials')

        if self.location_src_id and self.location_src_id.id:
            available_qty = self.product_product_id.with_context(location=self.location_src_id.id)._product_available().get(self.product_product_id.id, {}).get('qty_available')
        else:
            available_qty = self.product_product_id.qty_available

        if self.quantity_pro > available_qty:
            raise UserError('Quantity greater than the on hand quantity (%s)' % available_qty)

        # self.validate_product_to_form()
        dest_location = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)

        for record in self:
            debit_moves = self.env['stock.move'].browse([])

            # Reducing qty of main product
            if record.move_id and record.move_id.id:
                record.move_id.with_context(from_disassemble=True,disassemble_id=record.id,date_assemble=record.date_disassemble).action_done()
            else:
                move_data = {
                    'product_id'       : record.product_product_id.id,
                    'product_uom_qty'  : record.quantity_pro,
                    'product_uom'      : record.product_product_id.uom_id.id,
                    'name'             : record.product_product_id.name,
                    'date_expected'    : record.date_disassemble or fields.Datetime.now(),
                    'procure_method'   : 'make_to_stock',
                    'location_id'      : record.location_src_id.id,
                    'location_dest_id' : dest_location.id,
                    'origin'           : record.name,
                    'restrict_lot_id'  : record.stock_production_prod.id or False,
                    'date'             : record.date_disassemble
                }
                move_id = self.env['stock.move'].create(move_data)
                move_id.action_confirm()
                move_id.with_context(from_disassemble=True,disassemble_id=record.id,date_assemble=record.date_disassemble).action_done()
                record.move_id = move_id

            cost_price     = 0
            transfered_qty = 0
            for quant in record.move_id.quant_ids:
                cost_price     += quant.inventory_value
                transfered_qty += quant.qty

            if record.quantity_pro > transfered_qty:
                raise UserError('Quantity greater than the reserved quantity (%s)' % transfered_qty)

            # increasing material qty
            material_cost_price = 0
            for material in record.material_id:
                if material.qty_pro > 0:
                    material_cost_price += material.cost_price

            if float_compare(material_cost_price, cost_price, 0) != 0:
                raise UserError('You need to fully allocate cost to product')

            # Calculating the product_data from the materials
            # product_data = {}
            # for line in self.material_id:
            #     if line.product_id.id not in product_data:
            #         product_data.update({line.product_id.id: line.qty_pro})
            #     else:
            #         product_data.update({line.product_id.id: line.qty_pro + product_data.get(line.product_id.id)})

            # # Processing materials
            # for line in record.material_form_id:
            #     if line.quantity:
            #         # reduce material qty in dict
            #         for line2 in line.product_id.product_tmpl_id.material_ids:
            #             product_data.update({line2.product_id.id: product_data.get(line2.product_id.id) - (line2.material_quantity * line.quantity)})
            #         # increase product formed
            #         stock_move = {
            #             'product_id': line.product_id.id,
            #             'product_uom_qty': line.quantity,
            #             'product_uom': line.product_id.uom_id.id,
            #             'name': line.product_id.name,
            #             'date_expected': fields.Datetime.now(),
            #             'procure_method': 'make_to_stock',
            #             'location_id': dest_location.id,
            #             'location_dest_id': record.location_src_id.id,
            #             'origin': record.name,
            #         }
            #         move = self.env['stock.move'].create(stock_move)
            #         move.action_confirm()
            #         move.action_done()

            # increasing material qty
            for material in self.material_id:
                if material.product_id and material.product_id.id:
                    if material.qty_pro > 0:
                        product_obj = material.product_id
                        stock_move = {
                            'product_id'       : product_obj.id,
                            'product_uom_qty'  : material.qty_pro,
                            'product_uom'      : product_obj.uom_id.id,
                            'name'             : product_obj.name,
                            'date_expected'    : record.date_disassemble or fields.Datetime.now(),
                            'procure_method'   : 'make_to_stock',
                            'location_id'      : dest_location.id,
                            'location_dest_id' : record.location_src_id.id,
                            'origin'           : record.name,
                            'restrict_lot_id'  : material.stock_lot.id or False,
                            'price_unit'       : material.cost_price / material.qty_pro,
                            'date'             : record.date_disassemble
                        }
                        move_id = self.env['stock.move'].create(stock_move)
                        move_id.action_confirm()
                        move_id.with_context(from_disassemble=True,disassemble_id=record.id,date_assemble=record.date_disassemble).action_done()
                        debit_moves += move_id
                        material.move_id = move_id

            # record.create_journal_entry(debit_moves)

        self.write({'state': 'done'})
        return True

    @api.multi
    def create_journal_entry(self, debit_moves):
        self.ensure_one()

        account_move_lines = []
        credit_total = 0
        for quant in self.move_id.quant_ids:
            credit_total += quant.inventory_value

        # TODO: Calculation credit move data
        for move in debit_moves:
            debit_value = move.price_unit * move.product_uom_qty

            debit_data = {
                'name'           : move.product_id.name,
                'product_id'     : move.product_id.id,
                'quantity'       : move.product_uom_qty,
                'product_uom_id' : move.product_id.uom_id.id,
                'ref'            : 'Increased %s' % (move.product_id.name,),
                'credit'         : 0,
                'debit'          : debit_value,
                'account_id'     : move.product_id.categ_id.property_stock_valuation_account_id.id,
            }
            account_move_lines.append((0, 0, debit_data))

        # TODO: Calculation debit move data
        credit_data = {
            'name'           : self.product_product_id.name,
            'product_id'     : self.product_product_id.id,
            'quantity'       : self.quantity_pro,
            'product_uom_id' : self.product_product_id.uom_id.id,
            'ref'            : 'Disassemble %s' % (self.product_product_id.name,),
            'credit'         : credit_total if credit_total > 0 else 0,
            'debit'          : 0,
            'account_id'     : self.product_product_id.categ_id.property_stock_valuation_account_id.id,
        }
        account_move_lines.append((0, 0, credit_data))

        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': self.product_product_id.categ_id.property_stock_journal.id,
            'date': fields.Date.today(),
            'line_ids': account_move_lines,
            # 'asset_id': self.id,
            'ref': self.name,
        })
        move.post()

        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

ResDisassemble()

class DisassembleMaterials(models.Model):
    _name = 'disassemble.materials'

    disassemble_id  = fields.Many2one('res.disassemble', 'Materials')
    product_id      = fields.Many2one('product.product', 'Product')
    qty_pro         = fields.Integer('Quantity')
    stock_lot       = fields.Many2one('stock.production.lot', 'Serial Number/ Lot')
    move_id         = fields.Many2one('stock.move', 'Stock Move')
    cost_price      = fields.Float('Cost Price')
    disassemble_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', related='disassemble_id.state', default='draft')
    # assemble_id    = fields.Many2one('assemble.materials', 'Assemble Line')

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            lot_ids = self.env['stock.production.lot'].search([
                ('product_id', '=', self.product_id.id)
            ]).ids
            res['domain'] = {'stock_lot': [('id', 'in', lot_ids)]}
        return res

DisassembleMaterials()

class DisassembleProcuctsForm(models.Model):
    _name = 'disassemble.products.form'

    @api.depends('possible_qty','quantity')
    def compute_possible_qty(self):
        for record in self:
            record.possible_qty_dynamic = record.possible_qty - record.quantity

    disassemble_id       = fields.Many2one('res.disassemble', 'Materials')
    product_id           = fields.Many2one('product.product', 'Product')
    materials            = fields.Text('Materials')
    possible_qty         = fields.Integer('Possible Quantity')
    possible_qty_dynamic = fields.Integer(compute='compute_possible_qty', string='Dynamic Possible Quantity')
    quantity             = fields.Integer('Quantity')

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {}
        if self.product_id:
            lot_ids = self.env['stock.production.lot'].search([('product_id','=',self.product_id.id)]).ids
            res['domain'] = {'stock_lot': [('id','in',lot_ids)]}
        return res

    @api.onchange('quantity')
    def onchange_quantity(self):
        if self.quantity > self.possible_qty:
            self.quantity = 0
            return {
                'warning': {
                    'title': "Warning!",
                    'message': "You can not set more than the possible quantity",
                }
            }