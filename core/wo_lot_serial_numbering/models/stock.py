from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime


class ProductionLotWorkOrderHistory(models.Model):
    _name = 'stock.production.lot.workorder.history'

    name = fields.Many2one('mrp.workorder', 'Work Order')
    date = fields.Datetime('Date & Time', default=fields.Datetime.now)
    production_lot_id = fields.Many2one('stock.production.lot', 'Production Lots')


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    CONSUMED_TYPE = [
        ('finished', 'Finished'),
        ('lost', 'Lost'),
        ('quantity', 'Quantity'),
        ('lost_quantity', 'Lost Quantity'),
    ]

    manufacturing_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order')
    workorder_history_ids = fields.One2many('stock.production.lot.workorder.history', 'production_lot_id', 'History Work Order')
    consumed_type = fields.Selection(CONSUMED_TYPE, 'Material Consumed Type')


class mrp_material_consumed(models.Model):
    _inherit = 'mrp.material.consumed'

    @api.depends('production_id', 'product_id.tracking', 'workorder_id', 'line_ids', 'state')
    def get_tracking_type(self):
        for rec in self:
            if rec.workorder_id.production_id.product_id.tracking == 'none':
                rec.tracking = False
            else:
                rec.tracking = True

    production_id = fields.Many2one('mrp.production', 'Manufacturing Order', related='workorder_id.production_id', store=True)
    finishedmaterial_stock_location_ids = fields.One2many('mrp.material.consumed.stock.lots.finished', 'consumed_id', 'Finished Goods Lots/Serial Numbers')
    lost_stock_location_ids = fields.One2many('mrp.material.consumed.stock.lots.lost', 'consumed_id',
                                              'Lost Goods Lots/Serial Numbers')
    product_id = fields.Many2one(related='production_id.product_id', string="Product", store=True)
    tracking = fields.Boolean(compute="get_tracking_type", string="Tracking", store=True)

    @api.multi
    def action_show_stock_lots_view_for_finished(self):
        return {
            'name': 'Lots/Serial Numbers',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.material.consumed.stock.lots.finished',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': False,
            'views': [(self.env.ref(
                "wo_lot_serial_numbering.mrp_material_consumed_stock_lots_form_view").id or False, 'form')],
            'context': {'default_consumed_id': self.id, 'default_is_popup_open': True},
            'target': 'new',
        }

    @api.multi
    def action_show_stock_lots_view_for_lost(self):
        return {
            'name': 'Lots/Serial Numbers',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.material.consumed.stock.lots.lost',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': False,
            'views': [(self.env.ref(
                "wo_lot_serial_numbering.mrp_material_consumed_stock_lots_lost_form_view").id or False, 'form')],
            'context': {'default_consumed_id': self.id, 'default_is_popup_open': True},
            'target': 'new',
        }

class mrp_material_consumed_stock_lots_finished(models.Model):
    _name = 'mrp.material.consumed.stock.lots.finished'

    name = fields.Many2one('stock.production.lot', 'Production Lots', domain="[('manufacturing_id','=', production_id), ('consumed_type', '=', 'finished')]")
    consumed_id = fields.Many2one('mrp.material.consumed', 'Material Consumption ID')
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order', related='consumed_id.workorder_id', store=True)
    production_id = fields.Many2one('mrp.production', 'Manufacturing Order', related='consumed_id.production_id', store=True)
    product_id = fields.Many2one('product.product', 'Product', related='workorder_id.product_id', store=True)
    is_popup_open = fields.Boolean('Is popup open?', default=False)

    @api.multi
    def save_information(self):
        consumed_id = False
        for res in self:
            finished_goods = int(res.consumed_id.finished_goods)
            consumed_id = res.consumed_id
            if res.name.manufacturing_id:
                if res.name.workorder_id and res.name.workorder_id != res.workorder_id:
                    workorder_history_line = {
                        'name': res.name.workorder_id.id,
                        'date': datetime.datetime.now(),
                        'production_lot_id': res.name.id,
                    }
                    self.env['stock.production.lot.workorder.history'].create(workorder_history_line)
                    res.name.write({'workorder_id': res.workorder_id.id})
                    finished_goods += 1
                    res.consumed_id.write({'finished_goods': int(finished_goods)})
            else:
                res.name.write({'manufacturing_id': res.production_id.id, 'workorder_id': res.workorder_id.id})
                finished_goods += 1
                res.consumed_id.write({'finished_goods': int(finished_goods)})
            if res.is_popup_open:
                return {
                    'name': 'Material Consumed',
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.material.consumed',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': consumed_id and consumed_id.id or False,
                    'views': [(self.env.ref(
                        "manufacturing_material_consumption.mrp_material_inherit_form_view_popup").id or False, 'form')],
                    'target': 'new',
                }


class mrp_material_consumed_stock_lots_lost(models.Model):
    _name = 'mrp.material.consumed.stock.lots.lost'

    name = fields.Many2one('stock.production.lot', 'Production Lots', domain="[('manufacturing_id','=', production_id), ('consumed_type', '=', 'lost')]")
    consumed_id = fields.Many2one('mrp.material.consumed', 'Material Consumption ID')
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order', related='consumed_id.workorder_id', store=True)
    production_id = fields.Many2one('mrp.production', 'Manufacturing Order', related='consumed_id.production_id', store=True)
    product_id = fields.Many2one('product.product', 'Product', related='workorder_id.product_id', store=True)
    is_popup_open = fields.Boolean('Is popup open?', default=False)

    @api.multi
    def save_information(self):
        consumed_id = False
        for res in self:
            lost_goods = int(res.consumed_id.lost_goods)
            consumed_id = res.consumed_id
            if res.name.manufacturing_id:
                if res.name.workorder_id and res.name.workorder_id != res.workorder_id:
                    workorder_history_line = {
                        'name': res.name.workorder_id.id,
                        'date': datetime.datetime.now(),
                        'production_lot_id': res.name.id,
                    }
                    self.env['stock.production.lot.workorder.history'].create(workorder_history_line)
                    res.name.write({'workorder_id': res.workorder_id.id})
                    lost_goods += 1
                    res.consumed_id.write({'lost_goods': int(lost_goods)})
            else:
                res.name.write({'manufacturing_id': res.production_id.id, 'workorder_id': res.workorder_id.id})
                lost_goods += 1
                res.consumed_id.write({'lost_goods': int(lost_goods)})
            if res.is_popup_open:
                return {
                    'name': 'Material Consumed',
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.material.consumed',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': consumed_id and consumed_id.id or False,
                    'views': [(self.env.ref(
                        "manufacturing_material_consumption.mrp_material_inherit_form_view_popup").id or False, 'form')],
                    'target': 'new',
                }

class mrp_material_consumed_line(models.Model):
    _inherit = 'mrp.material.consumed.line'

    production_id = fields.Many2one('mrp.production', 'Manufacturing Order', related='workorder_id.production_id',
                                    store=True)
    qty_stock_location_ids = fields.One2many('mrp.material.consumed.stock.quantity', 'consumed_id', 'Quantity Lots/Serial Numbers')
    lost_qty_stock_location_ids = fields.One2many('mrp.material.consumed.stock.lots.lost', 'consumed_id',
                                              'Lost Quantity Lots/Serial Numbers')
    is_enable_qty_field = fields.Boolean('Enable Quantity field', default=False)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id.tracking == 'none':
            self.is_enable_qty_field = True
        else:
            self.is_enable_qty_field = False

    @api.multi
    def action_show_stock_lots_view_for_quantity(self):
        return {
            'name': 'Lots/Serial Numbers',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.material.consumed.stock.quantity',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': False,
            'views': [(self.env.ref(
                "wo_lot_serial_numbering.mrp_material_consumed_stock_lots_quantity_form_view").id or False, 'form')],
            'context': {'default_consumed_id': self.id, 'default_is_popup_open': True},
            'target': 'new',
        }

    @api.multi
    def action_show_stock_lots_view_for_lost_quantity(self):
        return {
            'name': 'Lots/Serial Numbers',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.material.consumed.stock.lost.quantity',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': False,
            'views': [(self.env.ref(
                "wo_lot_serial_numbering.mrp_material_consumed_stock_lots_lost_quantity_form_view").id or False, 'form')],
            'context': {'default_consumed_id': self.id, 'default_is_popup_open': True},
            'target': 'new',
        }

    class mrp_material_consumed_stock_quantity(models.Model):
        _name = 'mrp.material.consumed.stock.quantity'

        name = fields.Many2one('stock.production.lot', 'Production Lots', domain="[('manufacturing_id','=', production_id), ('consumed_type', '=', 'quantity')]")
        consumed_id = fields.Many2one('mrp.material.consumed.line', 'Material Consumption Line ID')
        workorder_id = fields.Many2one('mrp.workorder', 'Work Order', related='consumed_id.workorder_id', store=True)
        production_id = fields.Many2one('mrp.production', 'Manufacturing Order', related='consumed_id.production_id',
                                        store=True)
        product_id = fields.Many2one('product.product', 'Product', related='consumed_id.product_id', store=True)
        is_popup_open = fields.Boolean('Is popup open?', default=False)
        material_consumed_id = fields.Many2one('mrp.material.consumed', related='consumed_id.material_consumed_id', store=True)
        finished_stock_lots = fields.Many2one('mrp.material.consumed.stock.lots.finished', 'S/N to produce', domain="[('consumed_id','=', material_consumed_id)]")

        @api.multi
        def save_information(self):
            consumed_id = False
            for res in self:
                quantity = int(res.consumed_id.quantity)
                consumed_id = res.consumed_id
                if res.name.manufacturing_id:
                    if res.name.workorder_id and res.name.workorder_id != res.workorder_id:
                        workorder_history_line = {
                            'name': res.name.workorder_id.id,
                            'date': datetime.datetime.now(),
                            'production_lot_id': res.name.id,
                        }
                        self.env['stock.production.lot.workorder.history'].create(workorder_history_line)
                        res.name.write({'workorder_id': res.workorder_id.id})
                        quantity += 1
                        res.consumed_id.write({'quantity': int(quantity)})
                else:
                    res.name.write({'manufacturing_id': res.production_id.id, 'workorder_id': res.workorder_id.id})
                    quantity += 1
                    res.consumed_id.write({'quantity': int(quantity)})
                if res.is_popup_open:
                    return {
                        'name': 'Material Consumed',
                        'type': 'ir.actions.act_window',
                        'res_model': 'mrp.material.consumed',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_id': consumed_id and consumed_id.material_consumed_id and consumed_id.material_consumed_id.id or False,
                        'views': [(self.env.ref(
                            "manufacturing_material_consumption.mrp_material_inherit_form_view_popup").id or False,
                                   'form')],
                        'target': 'new',
                    }

    class mrp_material_consumed_stock_lost_quantity(models.Model):
        _name = 'mrp.material.consumed.stock.lost.quantity'

        name = fields.Many2one('stock.production.lot', 'Production Lots', domain="[('manufacturing_id','=', production_id), ('consumed_type', '=', 'lost_quantity')]")
        consumed_id = fields.Many2one('mrp.material.consumed.line', 'Material Consumption ID')
        workorder_id = fields.Many2one('mrp.workorder', 'Work Order', related='consumed_id.workorder_id', store=True)
        production_id = fields.Many2one('mrp.production', 'Manufacturing Order', related='consumed_id.production_id',
                                        store=True)
        product_id = fields.Many2one('product.product', 'Product', related='consumed_id.product_id', store=True)
        is_popup_open = fields.Boolean('Is popup open?', default=False)

        @api.multi
        def save_information(self):
            consumed_id = False
            for res in self:
                lost_quantity = int(res.consumed_id.lost_quantity)
                consumed_id = res.consumed_id
                if res.name.manufacturing_id:
                    if res.name.workorder_id and res.name.workorder_id != res.workorder_id:
                        workorder_history_line = {
                            'name': res.name.workorder_id.id,
                            'date': datetime.datetime.now(),
                            'production_lot_id': res.name.id,
                        }
                        self.env['stock.production.lot.workorder.history'].create(workorder_history_line)
                        res.name.write({'workorder_id': res.workorder_id.id})
                        lost_quantity += 1
                        res.consumed_id.write({'lost_quantity': int(lost_quantity)})
                else:
                    res.name.write({'manufacturing_id': res.production_id.id, 'workorder_id': res.workorder_id.id})
                    lost_quantity += 1
                    res.consumed_id.write({'lost_quantity': int(lost_quantity)})
                if res.is_popup_open:
                    return {
                        'name': 'Material Consumed',
                        'type': 'ir.actions.act_window',
                        'res_model': 'mrp.material.consumed',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_id': consumed_id and consumed_id.material_consumed_id and consumed_id.material_consumed_id.id or False,
                        'views': [(self.env.ref(
                            "manufacturing_material_consumption.mrp_material_inherit_form_view_popup").id or False,
                                   'form')],
                        'target': 'new',
                    }

    # class mrp_material_consumed_stock_lots_lost(models.Model):
    #     _name = 'mrp.material.consumed.stock.lots.lost'
    #
    #     name = fields.Many2one('stock.production.lot', 'Production Lots',
    #                            domain="[('manufacturing_id','=', production_id), ('consumed_type', '=', 'lost')]")
    #     consumed_id = fields.Many2one('mrp.material.consumed', 'Material Consumption ID')
    #     workorder_id = fields.Many2one('mrp.workorder', 'Work Order', related='consumed_id.workorder_id', store=True)
    #     production_id = fields.Many2one('mrp.production', 'Manufacturing Order', related='consumed_id.production_id',
    #                                     store=True)
    #     product_id = fields.Many2one('product.product', 'Product', related='workorder_id.product_id', store=True)
    #     is_popup_open = fields.Boolean('Is popup open?', default=False)
    #
    #     @api.multi
    #     def save_information(self):
    #         consumed_id = False
    #         for res in self:
    #             lost_goods = int(res.consumed_id.lost_goods)
    #             consumed_id = res.consumed_id
    #             if res.name.manufacturing_id:
    #                 if res.name.workorder_id and res.name.workorder_id != res.workorder_id:
    #                     workorder_history_line = {
    #                         'name': res.name.workorder_id.id,
    #                         'date': datetime.datetime.now(),
    #                         'production_lot_id': res.name.id,
    #                     }
    #                     self.env['stock.production.lot.workorder.history'].create(workorder_history_line)
    #                     res.name.write({'workorder_id': res.workorder_id.id})
    #                     lost_goods += 1
    #                     res.consumed_id.write({'lost_goods': int(lost_goods)})
    #             else:
    #                 res.name.write({'manufacturing_id': res.production_id.id, 'workorder_id': res.workorder_id.id})
    #                 lost_goods += 1
    #                 res.consumed_id.write({'lost_goods': int(lost_goods)})
    #         if res.is_popup_open:
    #             return {
    #                 'name': 'Material Consumed',
    #                 'type': 'ir.actions.act_window',
    #                 'res_model': 'mrp.material.consumed',
    #                 'view_mode': 'form',
    #                 'view_type': 'form',
    #                 'res_id': consumed_id and consumed_id.id or False,
    #                 'views': [(self.env.ref(
    #                     "manufacturing_material_consumption.mrp_material_inherit_form_view_popup").id or False,
    #                            'form')],
    #                 'target': 'new',
    #             }
    #         else:
    #             return True