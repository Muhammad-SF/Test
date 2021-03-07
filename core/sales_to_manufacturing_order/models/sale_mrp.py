# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
move_dest_ids = set()
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    from_planing = fields.Boolean(string='From Planing')

class ProductsTemplate(models.Model):
    _inherit = 'product.template'
    
    is_mo_plaining = fields.Boolean(string='Manufacturing Plan')

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    sale_id = fields.Many2one('sale.order' , 'Sales Order')
    move_dest_id = fields.Many2one('stock.move' , 'Destination Move')

    def _generate_finished_moves(self):
        # assign raw move into finish.?
        res = super(MrpProduction, self)._generate_finished_moves()
        return res 

    def _generate_raw_move(self, bom_line, line_data):
        # skip route for raw material
        moves = super(MrpProduction, self)._generate_raw_move(bom_line, line_data)
        moves.filtered(lambda x: x.raw_material_production_id and x.raw_material_production_id.mrp_plan_id).write({'from_planing': True})
        return moves

    @api.multi
    def _adjust_procure_method(self):
        # skip route when mo from planning
        planing_raw_ids = self.move_raw_ids.filtered(lambda x:x.from_planing)
        if planing_raw_ids:
            return False
        else:
            return super(MrpProduction, self)._adjust_procure_method()

class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    sale_mrp_id = fields.Many2one('sale.order', 'Sales Order')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    mrp_count = fields.Integer(string='Manufacturing', compute='_compute_mrp_count')
    plan_count = fields.Integer(string='Planing', compute='_compute_plan_count')

    def _prepare_procurement_group(self):
        res = super(SaleOrder, self)._prepare_procurement_group()
        res.update({'sale_mrp_id': self.id})
        return res

    @api.multi
    def action_view_production(self):
        production = self.env['mrp.production'].search([('sale_id', '=', self.id)])
        return {
            'name': _('Manufacturing'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.production',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', production.ids)],
        }

    @api.multi
    def action_view_planing(self):
        planing = self.env['mrp.plan'].search([('sale_id', '=', self.id)])
        return {
            'name': _('Planning'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'mrp.plan',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', planing.ids)],
        }

    @api.multi
    def _compute_mrp_count(self):
        for order in self:
            production = self.env['mrp.production'].search([('sale_id', '=', order.id)])
            order.mrp_count = len(production)

    @api.multi
    def _compute_plan_count(self):
        for order in self:
            planing = self.env['mrp.plan'].search([('sale_id', '=', order.id)])
            order.plan_count = len(planing)


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    def _prepare_mo_vals(self, bom):
        res = super(ProcurementOrder, self)._prepare_mo_vals(bom)
        res.update({'sale_id': self.group_id.sale_mrp_id.id if self.group_id.sale_mrp_id else False})
        return res

    def create_mo_from_plan(self, bom_line, mrp_plan, sale_id, qty):
        mrp_production_id = self.env['mrp.production'].create({
            'mrp_plan_id': mrp_plan.id,
            'sale_id': sale_id and sale_id.id or False,
            'product_id': bom_line.product_id.id,
            'product_qty': qty,
            'bom_id': bom_line.product_id.bom_ids[0].id,
            'date_planned_start': fields.Datetime.now(),
            'deadline_end': fields.Datetime.now(),
            'user_id': self.env.uid,
            'product_uom_id': bom_line.product_id.uom_id.id,
            'routing_id': bom_line.product_id.bom_ids[0].routing_id and bom_line.product_id.bom_ids[
                0].routing_id.id or False,
        })
        self.env['mrp.order'].create({
            'mrp_plan_id': mrp_plan.id,
            'mrp_production_id': mrp_production_id.id,
            'qty_to_produce': mrp_production_id.product_qty,
            'date_planned_end': mrp_production_id.deadline_end,
        })

    @api.multi
    def make_mo(self):
        res = super(ProcurementOrder, self).make_mo()
        for procurement in self.filtered(lambda x: x.production_id.sale_id and x.product_id.is_mo_plaining):
            _logger.info('>>>>>>>>> inside method')
            sale_temp_id = procurement.production_id.sale_id
            if sale_temp_id:
                sale_id = self.env['sale.order'].browse(int(sale_temp_id))
                _logger.info('>>>>>>>>> browsable sale id: %s', str(sale_id))
            else:
                sale_id = procurement.production_id.sale_id
            _logger.info('>>>>>>>>> after condition: %s', str(sale_id))
            qty = procurement.production_id.product_qty
            plan_exist = self.env['mrp.plan'].search([('sale_id', '=', sale_id.id)], limit=1)
            if not plan_exist:
                plan_vals = {
                    'name': 'Manufacturing Plan - %s' %(sale_id.name),
                    'date': fields.Datetime.now()
                    #'sale_id': sale_id and int(sale_id.id) or False
                    # 'mrp_order_ids': [(0, 0, {
                    #     'name': procurement.production_id.name,
                    #     'mrp_production_id': procurement.production_id and procurement.production_id.id or False,
                    #     'product_id': procurement.product_id and procurement.product_id.id or False,
                    #     'date_planned_start':procurement.production_id.date_planned_start,
                    #     'state': procurement.production_id.state,
                    #     'qty_to_produce': procurement.production_id.product_qty,
                    #     'qty_produce': 0.0,
                    #     'date_planned_end': fields.Datetime.now(),
                    # })]
                }
                _logger.info('>>>>>>>>> plan values: %s', str(plan_vals))
                mrp_plan = self.env['mrp.plan'].create(plan_vals)
                if mrp_plan:
                    query = _("UPDATE mrp_plan SET sale_id=%s WHERE id=%s") % (str(sale_id.id), str(mrp_plan.id))
                    self.env.cr.execute(query)

                    plan_order_values = {
                        'name': procurement.production_id.name,
                        'mrp_production_id': procurement.production_id and procurement.production_id.id or False,
                        'product_id': procurement.product_id and procurement.product_id.id or False,
                        'date_planned_start':procurement.production_id.date_planned_start,
                        'state': procurement.production_id.state,
                        'qty_to_produce': procurement.production_id.product_qty,
                        'qty_produce': 0.0,
                        'date_planned_end': fields.Datetime.now(),
                        'mrp_plan_id': mrp_plan.id,
                    }
                    self.env['mrp.order'].create(plan_order_values)
                if mrp_plan and procurement.product_id.bom_ids:
                    for bom_line in procurement.product_id.bom_ids[0].bom_line_ids.filtered(lambda x: x.product_id.bom_ids):
                        if bom_line.product_id.bom_ids:
                            for next_prod in bom_line.product_id.bom_ids[0].bom_line_ids.filtered(lambda x: x.product_id.bom_ids):
                                self.create_mo_from_plan(next_prod, mrp_plan, sale_id, (bom_line.product_qty / bom_line.bom_id.product_qty) * next_prod.product_qty * qty)
                        self.create_mo_from_plan(bom_line, mrp_plan, sale_id,(bom_line.product_qty / bom_line.bom_id.product_qty) * qty)

            else:
                plan_line_vals = {
                    'name': procurement.production_id.name,
                    'mrp_production_id': procurement.production_id and procurement.production_id.id or False,
                    'product_id': procurement.product_id and procurement.product_id.id or False,
                    'date_planned_start':procurement.production_id.date_planned_start,
                    'state': procurement.production_id.state,
                    'qty_to_produce': procurement.production_id.product_qty,
                    'qty_produce': 0.0,
                    'date_planned_end': fields.Datetime.now(),
                    'mrp_plan_id': plan_exist and plan_exist.id or False
                }
                self.env['mrp.order'].create(plan_line_vals)
                if plan_exist and procurement.product_id.bom_ids:
                    for bom_line in procurement.product_id.bom_ids[0].bom_line_ids.filtered(lambda x: x.product_id.bom_ids):
                        if bom_line.product_id.bom_ids:
                            for next_prod in bom_line.product_id.bom_ids[0].bom_line_ids.filtered(lambda x: x.product_id.bom_ids):
                                self.create_mo_from_plan(next_prod, plan_exist,sale_id,(bom_line.product_qty / bom_line.bom_id.product_qty) * next_prod.product_qty * qty)
                        self.create_mo_from_plan(bom_line, plan_exist,sale_id,(bom_line.product_qty / bom_line.bom_id.product_qty) * qty)
        return res 