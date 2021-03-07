from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

# class mrp_consumed_detail(models.Model):
#     _inherit = 'mrp.consumed.detail'
#
#     source_loc_id   = fields.Many2one('stock.location','Source Location')


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    location_id = fields.Many2one('stock.location', 'Work Center Location')
    stock_location_id = fields.Many2one('stock.location', string="Stock Location")

    @api.onchange('stock_location_id')
    def onchange_stock_location(self):
        if self.stock_location_id:
            for pm in self.planned_materials:
                pm.location_id = self.stock_location_id.id

    @api.model
    def create(self, vals):
        res = super(mrp_production, self).create(vals)
        if res:
            for rec in res.move_raw_ids:
                if res.stock_location_id:
                    rec.location_id = res.stock_location_id
        return res

    @api.multi
    def _compute_picking_out_type(self, line):
        picking_type_id = self.env['stock.picking.type']
        if line.location_id:
            condition = [('code', '=', 'internal')]
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', line.location_id.id)], limit=1)
            if warehouse:
                condition.append(('warehouse_id', '=', warehouse.id))
            picking_type_id = self.env['stock.picking.type'].search(condition, limit=1)
            if not picking_type_id:
                picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', self.env.user.company_id.id)], limit=1)
            if picking_type_id:
                return picking_type_id and picking_type_id.id or False
        else:
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', self.env.user.company_id.id)], limit=1)
            if picking_type_id:
                return picking_type_id and picking_type_id.id or False

    def get_source_location_id(self, dest_loc_id):
        picking_type_in_id = False
        if dest_loc_id:
            condition = [('code', '=', 'internal')]
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', dest_loc_id.id)], limit=1)
            if warehouse:
                condition.append(('warehouse_id', '=', warehouse.id))
            picking_type_id = self.env['stock.picking.type'].search(condition, limit=1)
            if not picking_type_id:
                picking_type_id = self.env['stock.picking.type'].search(
                    [('code', '=', 'internal'), ('warehouse_id.company_id', '=', self.env.user.company_id.id)], limit=1)
            if picking_type_id:
                picking_type_in_id = picking_type_id or False
        else:
            picking_type_id = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'), ('warehouse_id.company_id', '=', self.env.user.company_id.id)], limit=1)
            if picking_type_id:
                picking_type_in_id = picking_type_id or False
        return picking_type_in_id

    @api.multi
    def create_internal_transfer(self):
        lines = []
        ctx = dict(self.env.context or {})
        action = self.env.ref('internal_transfer_manufacturing.action_mrp_internal_transfer').read()[0]
        action.pop('id', None)
        dest_loc_id = False
        source_loc_id = False
        #if self.location_id:
        #    dest_loc_id = self.location_id.id
        #    picking_type_in_id = self.get_source_location_id(self.location_id)

        #    if picking_type_in_id and picking_type_in_id.default_location_dest_id:
         #       dest_loc_id = picking_type_in_id.default_location_dest_id.id
        #else:
        #    raise ValidationError('Please select production location.')

        for line in self.move_raw_ids:
            line_source_loc_id = False
            picking_out_id = self._compute_picking_out_type(line)

            if picking_out_id:
                picking_out_id_obj = self.env['stock.picking.type'].browse(int(picking_out_id))
                if picking_out_id_obj.default_location_src_id:
                    source_loc_id = picking_out_id_obj.default_location_src_id.id

            # if source_loc_id:
            #     line_source_loc_id = source_loc_id
            # else:
            #     line_source_loc_id = line.location_id and line.location_id.id or False

            inter_line = {'product_id': line.product_id and line.product_id.id or False,
                          'product_qty': line.product_uom_qty,
                          'uom_id': line.product_uom.id or line.product_id.uom_id.id or False,
                          # 'source_loc_id': line_source_loc_id,
                          'dest_loc_id': line.location_id.id or False,
                          }
            lines.append((0, 0, inter_line))
            
        ctx = {'default_type': 'stock_wo',
               'default_mrp_id': self and self.id or False,
               'default_schedule_date': fields.Date.today(),
               'default_dest_loc_id': dest_loc_id,
               'default_line_ids': lines if lines else False,
               'default_state': 'draft',
               'default_lines_loaded_from_mo': True,
               # 'default_picking_type_in_id':picking_type_in_id.id,
               # 'default_picking_type_out_id': picking_out_id,
               }
        action['context'] = ctx
        # res = self.env.ref('internal_transfer_manufacturing.view_mrp_internal_transfer_form', False)
        # action['views'] = [(res and res.id or False, 'form')]
        transfer_ids = self.env['mrp.transfer'].search([('mrp_id', '=', self.id)])
        print(transfer_ids)
        if len(transfer_ids) > 1:
            action['domain'] = [('id', 'in', transfer_ids.ids)]
        elif len(transfer_ids) == 1:
            res = self.env.ref('internal_transfer_manufacturing.view_mrp_internal_transfer_form', False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = transfer_ids.id
        else:
            res = self.env.ref('internal_transfer_manufacturing.view_mrp_internal_transfer_form', False)
            action['views'] = [(res and res.id or False, 'form')]
        return action

    # @api.multi
    # def create_internal_transfer(self):
    #     return {
    #         'name': 'Internal Transfer',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mrp.transfer',
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'res_id': False,
    #         'views': [(False, 'form')],
    #         'context': {'default_type': 'stock_mo',
    #                     'default_mrp_id': self.id or False,
    #                     'default_schedule_date': fields.Date.today(),
    #                     'default_dest_loc_id': self.location_id.id or False,
    #                     'default_line_ids': [(0, 0, {'product_id': line.product_id.id,
    #                                                  'product_qty': line.product_uom_qty,
    #                                                  'uom_id': line.product_uom.id or line.product_id.uom_id.id,
    #                                                  'source_loc_id': line.location_id.id or False}) for line in self.move_raw_ids]
    #                     },
    #         'target': 'new',
    #     }

    # def _generate_raw_move(self, bom_line, line_data):
    #     move = super(mrp_production, self)._generate_raw_move(bom_line, line_data)
    #     if self.stock_location_id:
    #         move.location_id = self.stock_location_id
    #     return move

    @api.onchange('routing_id')
    def onchange_routing_id(self):
        if self.routing_id and self.routing_id.operation_ids:
            for operation in self.routing_id.operation_ids:
                if operation.workcenter_id and operation.workcenter_id.location_id:
                    self.location_id = operation.workcenter_id.location_id.id
                    self.stock_location_id = operation.workcenter_id.location_id.id
                    break
