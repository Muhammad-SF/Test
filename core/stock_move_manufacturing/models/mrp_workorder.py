from odoo import models, fields, api


class mrp_workorder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def _compute_picking_out_type(self, production_id):
        picking_type_id = self.env['stock.picking.type']
        if production_id and production_id.location_id:
            condition = [('code', '=', 'internal')]
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', production_id.location_id.id)], limit=1)
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

    @api.multi
    def create_internal_transfer(self):
        lines = []
        ctx = dict(self.env.context or {})
        action = self.env.ref('internal_transfer_manufacturing.action_mrp_internal_transfer').read()[0]
        action.pop('id', None)
        for line in self.workorder_bomlines:
            inter_line = {  'product_id': line.name and line.name.id or False,
                            'product_qty': line.product_qty,
                            'parent_type': False,
                            'parent_state': False,
                            'uom_id': line.product_uom_id and line.product_uom_id.id or line.name.uom_id and line.name.uom_id.id or False,
                            'source_loc_id': self.production_id.location_id and self.production_id.location_id.id or False,
                            'picking_type_out_id': self._compute_picking_out_type(self.production_id)
                        }
            lines.append((0, 0, inter_line))
        ctx = { 'default_type': 'wo_wo',
                'default_workorder_id': self and self.id or False,
                'default_schedule_date': fields.Date.today(),
                'default_source_loc_id': self.production_id.location_id and self.production_id.location_id.id or False,
                # 'default_dest_loc_id': self.workcenter_id and self.workcenter_id.location_id and self.workcenter_id.location_id.id or False,
                'default_line_ids': lines if lines else False,
                'default_state': 'draft',
            }
        action['context'] = ctx
        transfer_ids = self.env['mrp.transfer'].search([('workorder_id', '=', self.id)])
        if len(transfer_ids) >= 1:
            action['domain'] = [('id', 'in',  transfer_ids.ids)]
        else:
            res = self.env.ref('internal_transfer_manufacturing.view_mrp_internal_transfer_form', False)
            action['views'] = [(res and res.id or False, 'form')]
        return action
