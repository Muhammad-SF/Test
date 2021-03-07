# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp import api, fields, models, _

from odoo.addons.base import res
from odoo.exceptions import UserError
import math
from lxml import etree

# import odoo.addons.decimal_precision as dp


class WorkCenterGroup(models.Model):
    _name = 'work.center.group'
    _description = "Work Center Group"
    _order = "id desc"

    name = fields.Char(string="Group Name")
    code = fields.Char(string="Group Code")
    company_id = fields.Many2one('res.company', 'Company',  default=lambda self: self.env['res.company']._company_default_get('mrp.production'), required=True)
    group_line_ids = fields.One2many('work.center.group.line', 'work_group_id', string='Work center Group line')


class WorkCenterGroupline(models.Model):
    _name = 'work.center.group.line'

    work_group_id = fields.Many2one('work.center.group', string='Work center Group')
    center_id = fields.Many2one('mrp.workcenter', string="Work Center")


class WorkCenterOperation(models.Model):
    _inherit = 'mrp.routing.workcenter'

    wc_group_id = fields.Many2one('work.center.group', string="Work Center Group")
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', required=False)


class WorkMrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        
        workorders = self.env['mrp.workorder']
        workorders_bomlines = self.env['mrp.workorder.bomlines']
        bom_qty = bom_data['qty']
        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0
        for operation in bom.routing_id.operation_ids:
            group_wc = [wc.center_id.id for wc in operation.wc_group_id.group_line_ids]
            free_center = []
            workcenter_id = False
            workcenter_id = operation.workcenter_id
            if not operation.workcenter_id:
                occupied_wo = workorders.search([('state', 'not in', ['done','cancel']),('workcenter_id.id', 'in', group_wc)])
                free_wo = group_wc
                if occupied_wo:
                    for each_wo in occupied_wo:
                        if each_wo.workcenter_id.id in free_wo:
                            free_wo.remove(each_wo.workcenter_id.id)
                
                if free_wo:
                     workcenter_id = self.env['mrp.workcenter'].browse(free_wo[0])
                
                elif not free_wo:
                    data = {}
                    fr_list = []
                    for fr in occupied_wo:
                        data = {
                            'workcenter_id': fr.workcenter_id,
                            'date_end': fr.date_planned_finished
                        }
                        fr_list.append(data)
                    newlist = sorted(fr_list, key=lambda k: k['date_end'])
                    print("========newlist===",newlist)
                    if len(newlist) > 0:
                        workcenter_id = newlist[0].get('workcenter_id')

            new_wo = {
                'name': operation.name,
                'production_id': self.id,
                'operation_id': operation.id,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'is_sequence': operation.is_sequence,
                'sequence_run': operation.sequence_run,
            }
            # # create workorder
            if workcenter_id:
                cycle_number = math.ceil(bom_qty / workcenter_id.capacity)  # TODO: float_round UP
                duration_expected = (workcenter_id.time_start +
                                     workcenter_id.time_stop +
                                     cycle_number * operation.time_cycle * 100.0 / workcenter_id.time_efficiency)
                new_wo.update({
                    'workcenter_id': workcenter_id.id,
                    'duration_expected': duration_expected,
                    'capacity': workcenter_id.capacity,
                    })

            workorder = workorders.create(new_wo)
            
            # Create Work Order BOM Lines
            if bom.bom_line_ids:
                for bom_lines in bom.bom_line_ids:
                    if bom_lines.operation_id and bom_lines.operation_id.name == operation.name:
                        workorder_bom_lines = workorders_bomlines.create({
                            'name': bom_lines.product_id.id,
                            'product_qty': bom_lines.product_qty * self.product_qty / bom_lines.bom_id.product_qty,
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
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_lot_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    wc_group_id = fields.Many2one('work.center.group', related='operation_id.wc_group_id')
    wc_list_lines_ids = fields.Many2many('mrp.workcenter', string='WC Center List',
                                         compute='_get_wc_lines_from_wc_group')
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', required=False,
                                    states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    def _get_wc_lines_from_wc_group(self):
        wc_list = []
        for workorder in self:
            if workorder.wc_group_id and workorder.wc_group_id.group_line_ids:
                for group_line in workorder.wc_group_id.group_line_ids:
                    if group_line.center_id.id not in wc_list:
                        wc_list.append(group_line.center_id.id)
            else:
                wc_list = self.env['mrp.workcenter'].search([]).ids

            workorder.wc_list_lines_ids = [(6, 0, wc_list)]




