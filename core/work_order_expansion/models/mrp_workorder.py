import logging

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_round
from datetime import datetime

_logger = logging.getLogger(__name__)


class MrpWorkorderBOMLines(models.Model):
    _name = 'mrp.workorder.bomlines'
    _description = 'MRP Workorder BOM Lines'

    def _get_default_product_uom_id(self):
        return self.env['product.uom'].search([], limit=1, order='id').id

    name = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Product Quantity', default=1.0,
                               digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one('product.uom', string='Product Unit of Measure',
                                     default=_get_default_product_uom_id,
                                     help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")
    sequence = fields.Integer(string='Sequence', default=1, help="Gives the sequence order when displaying.")
    work_order_id = fields.Many2one('mrp.workorder', string='Associated Work Order')
    actual_usage = fields.Integer(string='Actual Usage')
    bomline_id = fields.Many2one('mrp.bom.line', string="MRP BOm Line", compute="get_bomline_id")
    is_wip = fields.Boolean(string='Is WIP', compute="get_is_wip_value", default=False)

    @api.depends('name')
    def get_bomline_id(self):
        for rec in self:
            for line in rec.work_order_id.production_id.bom_id.bom_line_ids:
                if line.product_id.id == rec.name.id:
                    rec.bomline_id = line.id

    @api.depends('name')
    def get_is_wip_value(self):
        for rec in self:
            if rec.work_order_id.production_id and rec.work_order_id.production_id.bom_id:
                bom_id = rec.work_order_id.production_id.bom_id
                if bom_id.bom_line_ids:
                    for line in bom_id.bom_line_ids:
                        if line.product_id.display_name == rec.name.display_name:
                            if line.is_wip:
                                rec.is_wip = True

class MrpWorkorderExtended(models.Model):
    _inherit = 'mrp.workorder'
    _order = 'date_planned_start desc'

    workorder_bomlines = fields.One2many('mrp.workorder.bomlines', 'work_order_id', string='Bill of Material')
    workorder_id = fields.Char(string='WO Number', required=True, copy=False, readonly=True, index=True,
                               default=lambda self: _('New'))
    is_sequence = fields.Boolean('Is Sequence')
    sequence_run = fields.Integer('Sequence')

    # duration_expected = fields.Float( 'Expected Duration', digits=(16, 2), help="Expected duration (in minutes)", compute='get_duration_expected', store=True)
    compute_qty_production = fields.Float("", compute="get_compute_qty_production", default=0.0)
    material_request_count = fields.Float(string='RFQ Count', compute="_get_total_material_request_count")

    @api.multi
    def _get_total_material_request_count(self):
        for workorder in self:
            material_request_ids = self.env['std.material.request'].sudo().search([('source_document', '=', workorder.workorder_id)])
            workorder.material_request_count = len(material_request_ids)

    @api.multi
    def action_view_material_requests(self):
        material_request_ids = self.env['std.material.request'].sudo().search([('source_document', '=', self.workorder_id)])
        action = self.env.ref('std_material_request.std_planning_action').read()[0]
        if len(material_request_ids) > 1:
            action['domain'] = [('id', 'in', material_request_ids.ids)]
        elif len(material_request_ids) == 1:
            action['views'] = [(self.env.ref('std_material_request.material_request_form_view').id, 'form')]
            action['res_id'] = material_request_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def create_material_request(self):
        for workorder in self:
            if not len(workorder.workorder_bomlines) > 0:
                raise UserError(
                    _('No Planned Materials available to create material request !'))
            else:
                destination_location = self.env.ref('stock.stock_location_stock',
                                                    raise_if_not_found=False) and self.env.ref(
                    'stock.stock_location_stock', raise_if_not_found=False).id or False

                if workorder.workcenter_id and workorder.workcenter_id.location_id:
                    destination_location = workorder.workcenter_id.location_id.id

                if not destination_location:
                    raise UserError(
                        _('Cannot create Material Request because there is no destination location available to pass !'))

                imd = self.env['ir.model.data']
                action = imd.xmlid_to_object('std_material_request.std_planning_action')
                list_view_id = imd.xmlid_to_res_id('std_material_request.material_request_tree_view')
                form_view_id = imd.xmlid_to_res_id('std_material_request.material_request_form_view')
                result = {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [(form_view_id, 'form')],
                    'view_id': form_view_id,
                    'target': 'self',
                    'context': {
                        'default_request_reference': '/',
                        'default_requested_by': self.env.user.partner_id.id,
                        'default_destination_location': destination_location,
                        # 'default_schedule_date': datetime.date.today(),
                        'default_source_document': workorder.workorder_id,
                        'default_state': 'draft',
                        'default_product_line': [(0, 0, {
                            'descript': line.name and line.name.display_name or '',
                            'quantity': line.product_qty,
                            'request_date': datetime.today().strftime('%Y-%m-%d'),
                            'product_unit_measure': line.product_uom_id and line.product_uom_id.id or False,
                            'product': line.name and line.name.id or False,
                            'status': 'draft',

                        }) for line in workorder.workorder_bomlines]
                    },
                    'res_model': action.res_model,
                }

                return result


    @api.depends('qty_production')
    def get_compute_qty_production(self):
        for rec in self:
            if rec.qty_production:
                for line in rec.workorder_bomlines:
                    line.write({
                                   'product_qty': line.bomline_id.product_qty * rec.qty_production / line.bomline_id.bom_id.product_qty})

    # @api.depends('date_planned_start', 'date_planned_finished')
    # def get_duration_expected(self):
    #     for record in self:
    #         if record.date_planned_start and record.date_planned_finished:
    #             date_planned_start = datetime.strptime(record.date_planned_start, DEFAULT_SERVER_DATETIME_FORMAT)
    #             date_planned_finished = datetime.strptime(record.date_planned_finished, DEFAULT_SERVER_DATETIME_FORMAT)
    #             if date_planned_finished > date_planned_start:
    #                 time = (date_planned_finished - date_planned_start).total_seconds() / (60)
    #                 record.update({
    #                     'duration_expected': time
    #                 })

    @api.model
    def create(self, vals):
        if vals.get('workorder_id', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['workorder_id'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']).next_by_code('mrp.workorder') or _('New')
            else:
                vals['workorder_id'] = self.env['ir.sequence'].next_by_code('mrp.workorder') or _('New')
        result = super(MrpWorkorderExtended, self).create(vals)
        result._add_workorder_sequence_number()
        return result

    @api.multi
    def write(self, values):
        if ('date_planned_start' in values or 'date_planned_finished' in values) and any(
                workorder.state == 'done' for workorder in self):
            raise UserError(_('You can not change the finished work order.'))
        if 'workorder_id' in values and values.get('workorder_id', 'New') == 'New':
            values['workorder_id'] = self.env['ir.sequence'].next_by_code('mrp.workorder') or 'New'
        return super(MrpWorkorderExtended, self).write(values)

    @api.multi
    def _add_workorder_sequence_number(self):
        for workorder in self:
            if workorder.production_id and workorder.production_id.routing_id:
                if workorder.production_id.routing_id.operation_ids:
                    for operation in workorder.production_id.routing_id.operation_ids:
                        if operation.workcenter_id.id == workorder.workcenter_id.id and workorder.name == operation.name:
                            workorder.write({'is_sequence': True, 'sequence_run': operation.sequence_run})

                                # query = _("UPDATE mrp_workorder SET is_sequence=true AND sequence_run=%s WHERE id=%s") % (int(operation.sequence_run), int(workorder.id))
                                # print str(query)
                                # self._cr.execute(query)
        return True

    @api.multi
    def button_start(self):
        # _logger.info('>>>>>>>>>>>>>>>>>>>>>> %s', self.is_sequence)
        if self.is_sequence == True:
            work_order = self.search([('production_id', '=', self.production_id.id), ('is_sequence', '=', True),
                                      ('sequence_run', '<', self.sequence_run), ('state', 'in', ['pending', 'ready'])])
            if work_order:
                raise UserError(_("Can't Start Working this Order"))
        result = super(MrpWorkorderExtended, self).button_start()
        return result

    @api.multi
    def button_finish(self):
        result = super(MrpWorkorderExtended, self).button_finish()
        return result

    @api.multi
    def record_production(self):
        self.ensure_one()
        # if self.qty_producing <= 0:
        #     raise UserError(_('Please set the quantity you produced in the Current Qty field. It can not be 0!'))

        # if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id:
        #     raise UserError(_('You should provide a lot for the final product'))

        # Update quantities done on each raw material line
        raw_moves = self.move_raw_ids.filtered(
            lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.bom_line_id)
        for move in raw_moves:
            if move.unit_factor:
                rounding = move.product_uom.rounding
                move.quantity_done += float_round(self.qty_producing * move.unit_factor, precision_rounding=rounding)

        # Transfer quantities from temporary to final move lots or make them final
        for move_lot in self.active_move_lot_ids:
            # Check if move_lot already exists
            if move_lot.quantity_done <= 0:  # rounding...
                move_lot.sudo().unlink()
                continue
            # if not move_lot.lot_id:
            #     raise UserError(_('You should provide a lot for a component'))
            # Search other move_lot where it could be added:
            lots = self.move_lot_ids.filtered(
                lambda x: (x.lot_id.id == move_lot.lot_id.id) and (not x.lot_produced_id) and (not x.done_move))
            if lots:
                lots[0].quantity_done += move_lot.quantity_done
                lots[0].lot_produced_id = self.final_lot_id.id
                move_lot.sudo().unlink()
            else:
                move_lot.lot_produced_id = self.final_lot_id.id
                move_lot.done_wo = True

        # One a piece is produced, you can launch the next work order
        if self.next_work_order_id.state == 'pending':
            self.next_work_order_id.state = 'ready'
        if self.next_work_order_id and self.final_lot_id and not self.next_work_order_id.final_lot_id:
            self.next_work_order_id.final_lot_id = self.final_lot_id.id

        self.move_lot_ids.filtered(
            lambda move_lot: not move_lot.done_move and not move_lot.lot_produced_id and move_lot.quantity_done > 0
        ).write({
            'lot_produced_id': self.final_lot_id.id,
            'lot_produced_qty': self.qty_producing
        })

        # If last work order, then post lots used
        # TODO: should be same as checking if for every workorder something has been done?
        if not self.next_work_order_id:
            production_moves = self.production_id.move_finished_ids.filtered(
                lambda x: (x.state not in ('done', 'cancel')))
            for production_move in production_moves:
                if production_move.product_id.id == self.production_id.product_id.id and production_move.product_id.tracking != 'none':
                    move_lot = production_move.move_lot_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
                    if move_lot:
                        move_lot.quantity += self.qty_producing
                        move_lot.quantity_done += self.qty_producing
                    else:
                        move_lot.create({'move_id': production_move.id,
                                         'lot_id': self.final_lot_id.id,
                                         'quantity': self.qty_producing,
                                         'quantity_done': self.qty_producing,
                                         'workorder_id': self.id,
                                         })
                elif production_move.unit_factor:
                    rounding = production_move.product_uom.rounding
                    production_move.quantity_done += float_round(self.qty_producing * production_move.unit_factor,
                                                                 precision_rounding=rounding)
                else:
                    production_move.quantity_done += self.qty_producing  # TODO: UoM conversion?
        # Update workorder quantity produced
        self.qty_produced = self.qty_producing

        # Set a qty producing
        if self.qty_produced >= self.production_id.product_qty:
            self.qty_producing = 0
        elif self.production_id.product_id.tracking == 'serial':
            self.qty_producing = 1.0
            self._generate_lot_ids()
        else:
            self.qty_producing = self.production_id.product_qty - self.qty_produced
            self._generate_lot_ids()

        self.final_lot_id = False
        self.button_finish()
        return True


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']
        workorders_bomlines = self.env['mrp.workorder.bomlines']
        bom_qty = bom_data['qty']
        print("============_workorders_create=================Work Center Group===")
        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in bom.routing_id.operation_ids:
            # create workorder
            duration_expected = 0.0
            cycle_number = float_round(bom_qty / operation.workcenter_id.capacity, precision_digits=0,
                                       rounding_method='UP')
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            # if operation.workcenter_id.capacity:
            #     cycle_number = math.ceil(bom_qty / operation.workcenter_id.capacity)  # TODO: float_round UP
            # if operation.workcenter_id.time_efficiency:
            #     duration_expected = (operation.workcenter_id.time_start +
            #                          operation.workcenter_id.time_stop +
            #                          cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            workorder = workorders.create({
                'name': operation.name,
                'is_sequence': operation.is_sequence,
                'sequence_run': operation.sequence_run,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'operation_id': operation.id,
                'duration_expected': duration_expected,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'capacity': operation.workcenter_id.capacity,
            })

            # Create Work Order BOM Lines
            if bom.bom_line_ids:
                for bom_lines in bom.bom_line_ids:
                    if bom_lines.operation_id and bom_lines.operation_id.name == operation.name:
                        workorder_bom_lines = workorders_bomlines.create({
                            'name': bom_lines.product_id.id,
                            'product_qty': bom_lines.product_qty * self.product_qty,
                            'product_uom_id': bom_lines.product_uom_id.id,
                            'sequence': bom_lines.sequence,
                            'work_order_id': workorder.id,
                        })

            if workorders:
                workorders[-1].next_work_order_id = workorder.id
            workorders += workorder

            # assign moves; last operation receive all unassigned moves (which case ?)
            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(
                lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_lot_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders

        # @api.onchange('product_qty')
        # def onchange_product_qty(self):
        #     workorders_bomlines = self.env['mrp.workorder.bomlines']
        #     if self.product_qty:
        #         for line in self.bom_line_ids:
        #             local = workorders_bomlines.update({'qty_production': line.product_qty * self.product_qty})
        #             print("!@@!!@!@!@!!@@!@!!@", local)
