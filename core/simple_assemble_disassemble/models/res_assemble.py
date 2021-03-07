# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from dateutil import tz
import pytz

class ResAssemble(models.Model):
    _name = 'res.assemble'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _description = 'Product Assemble'

    material_id           = fields.One2many('assemble.materials', 'assemble_id', 'Materials', readonly=True, states={'draft': [('readonly', False)]})
    name                  = fields.Char(string='Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', True)]}, index=True, default='New')
    product_id            = fields.Many2one('product.template', 'Product',readonly=True, states={'draft': [('readonly', False)]})
    product_product_id    = fields.Many2one('product.product', compute='_compute_product_id', string='Product (2)')
    quantity_pro          = fields.Integer('Quantity', readonly=True, states={'draft': [('readonly', False)]},default=1)
    date_assemble         = fields.Datetime('Date', readonly=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now())
    stock_production_prod = fields.Many2one('stock.production.lot', 'Serial Number/ Lot', readonly=True, states={'draft': [('readonly', False)]})
    location_src_id       = fields.Many2one('stock.location', 'Location', readonly=True, states={'draft': [('readonly', False)]})
    move_id               = fields.Many2one('stock.move', 'Move')
    quant_available       = fields.Float('Quantity Available', compute='_compute_quant_available')
    state                 = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel','Cancelled')
    ], string='Status', default='draft')
    tracking = fields.Selection(related="product_id.tracking")
    account_move_ids = fields.Many2many('account.move',copy=False)
    move_count      = fields.Integer(compute='_get_account_move_count')

    @api.onchange('product_id','location_src_id')
    def get_domain_production(self):
        if self.product_id and self.location_src_id:
            quant_ids = self.env['stock.quant'].search(
                [('product_id', '=', self.product_product_id.id), ('location_id', '=', self.location_src_id.id),
                 ('lot_id', '!=', False)])
            return {'domain': {'stock_production_prod': [('id','in',quant_ids.ids)]}}
        else:
            return {'domain': {'stock_production_prod': []}}


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

    @api.multi
    def _compute_quant_available(self):
        for record in self:
            quant_available = 0
            if record.move_id and record.move_id.id:
                if record.location_src_id and record.location_src_id.id:
                    for quant in record.move_id.quant_ids:
                        if quant.location_id and quant.location_id.id == record.location_src_id.id:
                            quant_available += quant.qty
            record.quant_available = quant_available

    @api.depends('product_id')
    def _compute_product_id(self):
        for record in self:
            product = self.env['product.product'].search([
                ('product_tmpl_id','=',record.product_id.id)
            ], limit=1)
            record.product_product_id = product.id

    @api.onchange('product_id', 'quantity_pro')
    def onchange_product_id(self):
        if self.product_id:
            data = []
            for line in self.product_id.material_ids:
                data.append((0, 0, {'product_id': line.product_id.id, 'qty_pro': line.material_quantity * self.quantity_pro}))
            self.material_id = data

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('res.assemble') or 'New'
        result = super(ResAssemble, self).create(vals)
        return result

    @api.multi
    def action_assemble(self):
        move_obj = self.env['stock.move']

        if not self.material_id:
            raise UserError('Can not assemble without materials')

        for line in self.material_id:
            if line.qty_pro > line.product_id.qty_available:
                raise UserError('%s : Quantity greater than the on hand quantity (%s)' % (line.product_id.name, line.product_id.qty_available))

        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1).id
        if not picking_type_id:
            raise ValidationError(_('Please Setup for Internal Transfer location'))

        for record in self:
            credit_moves = move_obj.browse([])

            # Calculating the product_data from the materials
            product_data = {}
            for line in self.material_id:
                if line.product_id.id not in product_data:
                    product_data.update({line.product_id.id: line.qty_pro})
                else:
                    product_data.update({line.product_id.id: line.qty_pro + product_data.get(line.product_id.id)})

            # Step1: Checking material
            total_price = 0
            for line in record.material_id:
                line_product     = line.product_id
                line_product_qty = line.qty_pro
                if line_product.type == 'product':
                    available_qty = line_product.with_context(location=record.location_src_id.id)._product_available().get(line_product.id, {}).get('qty_available')
                    if available_qty < line_product_qty:
                        raise ValidationError(_('Material ' + line_product.name + ' have not enough stock.'))

                    move_data = {
                        'product_id'       : line_product.id,
                        'product_uom'      : line_product.uom_id.id,
                        'name'             : 'Deducted %s' % (line.product_id.name,),
                        'location_id'      : record.location_src_id.id,
                        'location_dest_id' : line_product.property_stock_production.id,
                        'product_uom_qty'  : line_product_qty,
                        'picking_type_id'  : picking_type_id,
                        'date'             : record.date_assemble
                        # 'restrict_lot_id'  : record.stock_production_prod.id or False,
                    }
                    move_id = move_obj.create(move_data)
                    move_id.action_confirm()
                    move_id.with_context(qty_lot_assemble_line=True).action_assign()
                    if move_id.picking_id:
                        move_id.picking_id.write({'min_date':record.date_assemble})
                        for pack in move_id.picking_id.pack_operation_product_ids:
                            if pack.product_qty != pack.qty_done:
                                if pack.pack_lot_ids:
                                    pack.qty_done = pack.product_qty
                                elif not pack.pack_lot_ids and line.stock_lot:
                                    pack.write({'pack_lot_ids': [(0, 0,
                                                                  {'lot_id': line.stock_lot.id, 'qty': line.qty_pro,
                                                                   'qty_to_do': line.qty_pro})],
                                                'qty_done': pack.product_qty})
                                else:
                                    pack.qty_done = pack.product_qty
                            elif pack.product_qty == pack.qty_done and pack.pack_lot_ids and line.stock_lot:
                                if line.stock_lot.id not in pack.pack_lot_ids.mapped('lot_id.id'):
                                    pack.pack_lot_ids.unlink()
                                    pack.write({'pack_lot_ids': [(0, 0,
                                                                  {'lot_id': line.stock_lot.id, 'qty': line.qty_pro,
                                                                   'qty_to_do': line.qty_pro})],
                                                'qty_done': pack.product_qty})
                    move_id.with_context(from_assemble=True,assemble_id=record.id).action_done()
                    move_id.quant_ids.write({'in_date':record.date_assemble})
                    line.move_id = move_id

                    credit_moves += move_id
                    for quant in move_id.quant_ids:
                        total_price += quant.inventory_value

            assemple_product = record.product_product_id
            if assemple_product.type == 'product':
                # increasing qty of main product
                move_data = {
                    'product_id'      : assemple_product.id,
                    'product_uom_qty' : record.quantity_pro,
                    'product_uom'     : assemple_product.uom_id.id,
                    'name'            : 'Produced %s' % (assemple_product.name),
                    'date_expected'   : record.date_assemble or fields.Datetime.now(),
                    'procure_method'  : 'make_to_stock',
                    'location_id'     : assemple_product.property_stock_production.id,
                    'location_dest_id': record.location_src_id.id,
                    'origin'          : record.name,
                    'restrict_lot_id' : record.stock_production_prod.id or False,
                    'price_unit'      : total_price / record.quantity_pro,
                    'date'            : record.date_assemble
                }
                move_id = self.env['stock.move'].create(move_data)
                move_id.with_context(qty_lot_assemble_line=True).action_assign()
                move_id.with_context(from_assemble=True,assemble_id=record.id,date_assemble=move_id.convert_to_utc(record.date_assemble)).action_done()
                record.move_id = move_id

                # record.create_journal_entry(credit_moves)

        self.write({'state': 'done'})
        return True

    @api.multi
    def create_journal_entry(self, credit_moves):
        self.ensure_one()

        account_move_lines = []
        credit_total = 0

        # TODO: Calculation credit move data
        for move in credit_moves:
            credit_value = 0
            for quant in move.quant_ids:
                credit_value += quant.inventory_value
            credit_total += credit_value

            credit_data = {
                'name'           : move.product_id.name,
                'product_id'     : move.product_id.id,
                'quantity'       : move.product_uom_qty,
                'product_uom_id' : move.product_id.uom_id.id,
                'ref'            : 'Deducted %s' % (move.product_id.name,),
                'credit'         : credit_value if credit_value > 0 else 0,
                'debit'          : 0,
                'account_id'     : move.product_id.categ_id.property_stock_valuation_account_id.id,
            }
            account_move_lines.append((0, 0, credit_data))

        # TODO: Calculation debit move data
        debit_data = {
            'name'           : self.product_product_id.name,
            'product_id'     : self.product_product_id.id,
            'quantity'       : self.quantity_pro,
            'product_uom_id' : self.product_product_id.uom_id.id,
            'ref'            : 'Assemble %s' % (self.product_product_id.name,),
            'credit'         : 0,
            'debit'          : credit_total if credit_total > 0 else 0,
            'account_id'     : self.product_product_id.categ_id.property_stock_valuation_account_id.id,
        }
        account_move_lines.append((0, 0, debit_data))

        move = self.env['account.move'].create({
            'name'       : '/',
            'journal_id' : self.product_id.categ_id.property_stock_journal.id,
            'date'       : fields.Date.today(),
            'line_ids'   : account_move_lines,
            # 'asset_id'   : self.id,
            'ref'        : self.name,
        })
        move.post()

        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

ResAssemble()

class AssembleMaterials(models.Model):
    _name = 'assemble.materials'

    assemble_id = fields.Many2one('res.assemble', 'Materials')
    product_id  = fields.Many2one('product.product', 'Product')
    qty_pro     = fields.Integer('Quantity')
    stock_lot   = fields.Many2one('stock.production.lot', 'Serial Number/ Lot')
    move_id     = fields.Many2one('stock.move', 'Stock Move')

AssembleMaterials()

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def assemble_form_view(self):
        ctx = dict()
        form_id = self.env['ir.model.data'].sudo().get_object_reference('simple_assemble_disassemble', 'res_assemble_form_view')[1]
        ctx.update({
            'default_product_id': self.id,
        })
        action = {
            'type'      : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'res.assemble',
            'views'     : [(form_id, 'form')],
            'view_id'   : form_id,
            'target'    : 'new',
            'context'   : ctx,
        }
        return action

ProductTemplate()

from collections import namedtuple
class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_pack_ops(self, quants, forced_qties):
        """ Prepare pack_operations, returns a list of dict to give at create """
        # TDE CLEANME: oh dear ...
        valid_quants = quants.filtered(lambda quant: quant.qty > 0)
        _Mapping = namedtuple('Mapping', ('product', 'package', 'owner', 'location', 'location_dst_id'))

        all_products = valid_quants.mapped('product_id') | self.env['product.product'].browse(p.id for p in forced_qties.keys()) | self.move_lines.mapped('product_id')
        computed_putaway_locations = dict(
            (product, self.location_dest_id.get_putaway_strategy(product) or self.location_dest_id.id) for product in all_products)

        product_to_uom = dict((product.id, product.uom_id) for product in all_products)
        picking_moves = self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel'))
        for move in picking_moves:
            # If we encounter an UoM that is smaller than the default UoM or the one already chosen, use the new one instead.
            if move.product_uom != product_to_uom[move.product_id.id] and move.product_uom.factor > product_to_uom[move.product_id.id].factor:
                product_to_uom[move.product_id.id] = move.product_uom
        if len(picking_moves.mapped('location_id')) > 1:
            raise UserError(_('The source location must be the same for all the moves of the picking.'))
        if len(picking_moves.mapped('location_dest_id')) > 1:
            raise UserError(_('The destination location must be the same for all the moves of the picking.'))

        pack_operation_values = []
        # find the packages we can move as a whole, create pack operations and mark related quants as done
        top_lvl_packages = valid_quants._get_top_level_packages(computed_putaway_locations)
        for pack in top_lvl_packages:
            pack_quants = pack.get_content()
            pack_operation_values.append({
                'picking_id': self.id,
                'package_id': pack.id,
                'product_qty': 1.0,
                'location_id': pack.location_id.id,
                'location_dest_id': computed_putaway_locations[pack_quants[0].product_id],
                'owner_id': pack.owner_id.id,
            })
            valid_quants -= pack_quants

        # Go through all remaining reserved quants and group by product, package, owner, source location and dest location
        # Lots will go into pack operation lot object
        qtys_grouped = {}
        lots_grouped = {}
        for quant in valid_quants:
            key = _Mapping(quant.product_id, quant.package_id, quant.owner_id, quant.location_id, computed_putaway_locations[quant.product_id])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += quant.qty
            if quant.product_id.tracking != 'none' and quant.lot_id:
                lots_grouped.setdefault(key, dict()).setdefault(quant.lot_id.id, 0.0)
                lots_grouped[key][quant.lot_id.id] += quant.qty
        # Do the same for the forced quantities (in cases of force_assign or incomming shipment for example)
        for product, qty in forced_qties.items():
            if qty <= 0.0:
                continue
            key = _Mapping(product, self.env['stock.quant.package'], self.owner_id, self.location_id, computed_putaway_locations[product])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += qty

        # Create the necessary operations for the grouped quants and remaining qtys
        Uom = self.env['product.uom']
        product_id_to_vals = {}  # use it to create operations using the same order as the picking stock moves
        for mapping, qty in qtys_grouped.items():
            uom = product_to_uom[mapping.product.id]
            val_dict = {
                'picking_id': self.id,
                'product_qty': mapping.product.uom_id._compute_quantity(qty, uom),
                'product_id': mapping.product.id,
                'package_id': mapping.package.id,
                'owner_id': mapping.owner.id,
                'location_id': mapping.location.id,
                'location_dest_id': mapping.location_dst_id,
                'product_uom_id': uom.id,
                'pack_lot_ids': [
                    # Only config in here for qty with context
                    (0, 0, {'lot_id': lot, 'qty': self.env.context.get('qty_lot_assemble_line',False) and lots_grouped[mapping][lot] or 0.0, 'qty_todo': lots_grouped[mapping][lot]})
                    for lot in lots_grouped.get(mapping, {}).keys()],
            }
            product_id_to_vals.setdefault(mapping.product.id, list()).append(val_dict)

        for move in self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')):
            values = product_id_to_vals.pop(move.product_id.id, [])
            pack_operation_values += values
        return pack_operation_values

    # Config qty done of pack operation
    @api.multi
    def do_prepare_partial(self):
        res = super(stock_picking, self).do_prepare_partial()
        for pack in self.pack_operation_product_ids:
            if pack.product_id.tracking != 'none':
                pack.write({'qty_done': sum(pack.pack_lot_ids.mapped('qty'))})
        return res

class account_move(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self,vals):
        if (self._context.get('from_disassemble', False) or self._context.get('from_assemble', False)) and self._context.get('date_assemble',False):
            vals.update({'date':self._context.get('date_assemble',False)})
        res = super(account_move, self).create(vals)
        if (self._context.get('from_disassemble',False) or self._context.get('from_assemble',False)) and res:
            if self._context.get('assemble_id', False):
                self.env['res.assemble'].browse(self._context.get('assemble_id', False)).write({'account_move_ids':[(4,res.id)]})
            if self._context.get('disassemble_id',False):
                self.env['res.disassemble'].browse(self._context.get('assemble_id', False)).write({'account_move_ids': [(4, res.id)]})
        return res