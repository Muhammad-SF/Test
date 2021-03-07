# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _
from odoo.addons import decimal_precision as dp


class ScrapReturnLine(models.TransientModel):
    _name = 'stock.return.line'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float("Quantity", digits=dp.get_precision('Product Unit of Measure'), required=True)
    wizard_id = fields.Many2one('scrap.return', string="Wizard")
    move_id = fields.Many2one('stock.move', "Move")



class ScrapReturn(models.TransientModel):
    _name = 'scrap.return'

    product_return_moves = fields.One2many('stock.return.line', 'wizard_id', 'Moves')
    move_dest_exists = fields.Boolean('Chained Move Exists', readonly=True)
    original_location_id = fields.Many2one('stock.location')
    parent_location_id = fields.Many2one('stock.location')
    location_id = fields.Many2one(
        'stock.location', 'Return Location',
        domain="['|', ('id', '=', original_location_id), '&', ('return_location', '=', True), ('id', 'child_of', parent_location_id)]")

    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', list())) > 1:
            raise exceptions.UserError("You may only return one scrap at a time!")
        res = super(ScrapReturn, self).default_get(fields)

        Quant = self.env['stock.quant']
        move_dest_exists = False
        product_return_moves = []
        stock_scrap_obj = self.env['stock.scrap'].browse(
            self.env.context.get('active_id'))
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if stock_scrap_obj:
            if stock_scrap_obj.state != 'done':
                raise exceptions.UserError(_("You may only return Done scrap."))
            if stock_scrap_obj.move_id.scrapped:
                if stock_scrap_obj.move_id.move_dest_id:
                    move_dest_exists = True
                quantity = sum(quant.qty for quant in Quant.search([
                    ('history_ids', 'in', stock_scrap_obj.move_id.id),
                    ('qty', '>', 0.0), ('location_id', 'child_of', stock_scrap_obj.move_id.location_dest_id.id)
                ]).filtered(
                    lambda quant: not quant.reservation_id or quant.reservation_id.origin_returned_move_id != stock_scrap_obj.move_id)
                               )
                quantity = stock_scrap_obj.move_id.product_id.uom_id._compute_quantity(quantity, stock_scrap_obj.move_id.product_uom)
                product_return_moves.append(
                    (0, 0, {'product_id': stock_scrap_obj.move_id.product_id.id,
                            'quantity': quantity, 'move_id': stock_scrap_obj.move_id.id}))
            if not product_return_moves:
                raise exceptions.UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': product_return_moves})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': move_dest_exists})
            if 'parent_location_id' in fields and stock_scrap_obj.move_id.location_id.usage == 'internal':
                res.update({'parent_location_id': stock_scrap_obj.move_id.picking_type_id.warehouse_id and stock_scrap_obj.move_id.picking_type_id.warehouse_id.view_location_id.id or stock_scrap_obj.move_id.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': stock_scrap_obj.move_id.location_id.id})
            if 'location_id' in fields:
                location_id = stock_scrap_obj.move_id.location_id.id
                if stock_scrap_obj.move_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = stock_scrap_obj.move_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
                res['location_id'] = location_id
        return res

    @api.multi
    def _create_returns(self):
        stock_scrap_obj = self.env['stock.scrap'].browse(
            self.env.context.get('active_id'))
        move = stock_scrap_obj.move_id.copy({
            'location_id': stock_scrap_obj.move_id.location_dest_id.id, #self.location_id.id,
            'location_dest_id': self.location_id.id,
        })
        quants = self.env['stock.quant'].quants_get_preferred_domain(
            move.product_qty, move,
            domain=[
                ('qty', '>', 0),
                ('lot_id', '=', stock_scrap_obj.lot_id.id),
                ('package_id', '=', stock_scrap_obj.package_id.id)],
            preferred_domain_list=stock_scrap_obj._get_preferred_domain())
        self.env['stock.quant'].quants_reserve(quants, move)
        move.action_done()
        stock_scrap_obj.write({'return_stock_move_id': move.id,
                               'state': 'return',
                               })
        return move

    @api.multi
    def create_returns(self):
        stock_scrap_obj = self.env['stock.scrap'].browse(
            self.env.context.get('active_id'))
        for wizard in self:
            new_picking_id = wizard._create_returns()
        return {'type': 'ir.actions.act_window_close'}

ScrapReturn()
