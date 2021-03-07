# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class PackOperation(models.Model):
    _inherit = "mrp.plan"

    sale_id = fields.Many2many('sale.order','mrp_plan_sale_order_rel','mrp_plan_id','sale_order_id',string="Sale Order Reference",domain=[('state', 'not in', ['draft','cancel'])])


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    MRP_SETTINGS = [
        ('mp', 'Auto Create Manufacturing Plan'),
        ('mo', 'Auto Create Manufacturing Order'),
        ('none', 'None'),
    ]

    #create_mo_from_so = fields.Boolean(string='Create MO from SO', default=False)
    mo_creation_settings = fields.Selection(MRP_SETTINGS, string='Sales to Manufacturing', default='none')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    #description = fields.Text('Description')
    manufacturing_order_count = fields.Integer(string='Manufacturing', compute='_compute_production_ids')
    
    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            order.order_line._action_procurement_create()
            order.order_line._action_mo_create_from_so()
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True
        
    @api.multi
    @api.depends('procurement_group_id')
    def _compute_production_ids(self):
        for order in self:
            manufacturin_orders = self.env['mrp.production'].search([('sale_id', 'in', order.id)]) if order else []
            order.manufacturing_order_count = len(manufacturin_orders)
            
            
    @api.multi
    def action_view_mo(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        '''plans = self.env['mrp.plan'].search([('sale_id','in',self.id)])
        order_ids = []
        for plan in plans:
            for mrp_order_id in plan.mrp_order_ids:
                order_ids.append(mrp_order_id.id) 
        productions_ids = self.env['mrp.production'].search([('mrp_order_ids','in',order_ids)])
        if productions_ids:
            action['domain'] = [('id', 'in', productions_ids.ids)]'''
        productions_ids = self.env['mrp.production'].search([('sale_id','in',self.id)])
        if productions_ids:
            action['domain'] = [('id', 'in', productions_ids.ids)]
        return action

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _get_product_bom_for_auto_mo(self, company_id, product_id):
        return self.env['mrp.bom'].with_context(company_id=company_id.id,force_company=company_id.id)._bom_find(product=product_id)

    def _get_date_planned(self):
        format_date_planned = fields.Datetime.from_string(self.order_id.confirmation_date)
        date_planned = format_date_planned - relativedelta(days=self.product_id.produce_delay or 0.0)
        date_planned = date_planned - relativedelta(days=self.company_id.manufacturing_lead)
        return date_planned

    def _prepare_mo_vals(self):
        bom = self._get_product_bom_for_auto_mo(company_id=self.company_id, product_id=self.product_id)
        if not bom:
            raise UserError(_('You must define a BOM for product %s') % str(self.product_id.display_name))
        location_id = False
        stock_location_id = False
        if bom.routing_id and bom.routing_id.operation_ids:
            for operation in bom.routing_id.operation_ids:
                if operation.workcenter_id and operation.workcenter_id.location_id:
                    location_id = operation.workcenter_id.location_id.id
                    stock_location_id = operation.workcenter_id.location_id.id
                    break
        return {
            'origin': self.order_id.name,
            'product_id': self.product_id.id,
            'product_qty': self.product_uom_qty,
            'product_uom_id': self.product_uom.id,
            'bom_id': bom.id,
            'date_planned_start': fields.Datetime.to_string(self._get_date_planned()),
            'date_planned_finished': self.order_id.confirmation_date,
            'company_id': self.company_id.id,
            'location_id': location_id,
            'stock_location_id': stock_location_id,
            'sale_id':[(6, 0, [self.order_id.id])],###addd
        }

    @api.multi
    def _action_mo_create_from_so(self):
        mrp_order_wizard_lines = []
        so_order = False

        # Get product lines that use to create MP
        for line in self:
            if line.product_id.product_tmpl_id.mo_creation_settings:
                if line.product_id.product_tmpl_id.mo_creation_settings == 'mp':
                    mrp_order_wizard_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty,
                    }))
                    so_order = line.order_id
                if line.product_id.product_tmpl_id.mo_creation_settings == 'mo':
                    mo_values = line._prepare_mo_vals()
                    self.env['mrp.production'].create(mo_values)

        if len(mrp_order_wizard_lines) > 0 and so_order:
            add_id = self.env['mrp.order.wizard'].sudo().create({
                'line_ids': mrp_order_wizard_lines
            })
            if add_id:
                mp_id = self.env['mrp.plan'].sudo().create({
                    'name': 'Plan created from SO #: ' + str(so_order.name),
                    'sale_id': [(6, 0, [so_order.id])],
                    'add_id': add_id.id,
                    'date': datetime.now()
                })
                if mp_id:
                    add_id.confirm_from_so(mp_id=mp_id)
                    #mp_id.button_confirm()

class add_mrp_order_wizard(models.Model):
    _inherit = 'mrp.order.wizard'

    @api.multi
    def confirm_from_so(self, mp_id):
        
        if mp_id:
            mrp_plan = self.env['mrp.plan'].browse(int(mp_id.id))
            MRP_PRDODUCTION = self.env['mrp.production']
            MRP_ORDER = self.env['mrp.order']
            for line in self.line_ids:
                product = line.product_id
                wiz_qty = line.quantity

                if product.bom_ids:
                    location_id = False
                    stock_location_id = False
                    if product.bom_ids[0].routing_id and product.bom_ids[0].routing_id.operation_ids:
                        for operation in product.bom_ids[0].routing_id.operation_ids:
                            if operation.workcenter_id and operation.workcenter_id.location_id:
                                location_id = operation.workcenter_id.location_id.id
                                stock_location_id = operation.workcenter_id.location_id.id
                                break

                    '''origin = ''
                    for sale in mp_id.sale_id:
                        origin = sale.name'''
                    mrp_production_created_id = MRP_PRDODUCTION.create({
                        'mrp_plan_id': mrp_plan.id,
                        'product_id': product.id,
                        'product_qty': wiz_qty,
                        'bom_id': product.bom_ids[0].id,
                        'date_planned_start': fields.Datetime.now(),
                        'deadline_end': fields.Datetime.now(),
                        'user_id': self._uid,
                        'product_uom_id': product.uom_id.id,
                        'routing_id': product.bom_ids[0].routing_id and product.bom_ids[0].routing_id.id or False,
                        'location_id': location_id,
                        'stock_location_id': stock_location_id,
                        #'origin':origin,###addd
                        'origin':mp_id.plan_id,###addd
                        'sale_id':[(6, 0, mp_id.sale_id.ids)] or False,###addd
                    })
                    MRP_ORDER.create({
                        'mrp_plan_id': mrp_plan.id,
                        'mrp_production_id': mrp_production_created_id.id,
                        'qty_to_produce': mrp_production_created_id.product_qty,
                        'date_planned_end': mrp_production_created_id.deadline_end,
                    })
                    # Function for multi level BOMs
                    if product.bom_ids[0].bom_line_ids:
                        self.create_mo_for_multi_bom(product.bom_ids[0].bom_line_ids, mrp_plan, wiz_qty)

                    if mrp_production_created_id.move_raw_ids:
                        for move_raw_id in mrp_production_created_id.move_raw_ids:
                            self.create_mrp_production_rescursive_from_so(move_raw_id, mp_id)

    def create_mrp_production_rescursive_from_so(self, move_raw_id, mp_id):
        if mp_id:
            mrp_plan = self.env['mrp.plan'].browse(int(mp_id.id))
            MRP_PRDODUCTION = self.env['mrp.production']
            MRP_ORDER = self.env['mrp.order']
            product = move_raw_id.product_id
            product_uom_qty = move_raw_id.product_uom_qty
            if product.bom_ids:
                location_id = False
                stock_location_id = False
                if product.bom_ids[0].routing_id and product.bom_ids[0].routing_id.operation_ids:
                    for operation in product.bom_ids[0].routing_id.operation_ids:
                        if operation.workcenter_id and operation.workcenter_id.location_id:
                            location_id = operation.workcenter_id.location_id.id
                            stock_location_id = operation.workcenter_id.location_id.id
                            break
                '''####addd####
                origin = ''
                for sale in mp_id.sale_id:
                    origin = sale.name
                ####faddd####'''
                mrp_production_created_id = MRP_PRDODUCTION.create({
                    'mrp_plan_id': mrp_plan.id,
                    'product_id': product.id,
                    'product_qty': product_uom_qty,
                    'bom_id': product.bom_ids[0].id,
                    'date_planned_start': fields.Datetime.now(),
                    'deadline_end': fields.Datetime.now(),
                    'user_id': self._uid,
                    'product_uom_id': product.uom_id.id,
                    'routing_id': product.bom_ids[0].routing_id and product.bom_ids[0].routing_id.id or False,
                    'location_id': location_id,
                    'stock_location_id': stock_location_id,
                    #'origin':origin,#########addd
                    'origin':mp_id.plan_id,
                    'sale_id':[(6, 0, mp_id.sale_id.ids)] or False,###addd
                })
                MRP_ORDER.create({
                    'mrp_plan_id': mrp_plan.id,
                    'mrp_production_id': mrp_production_created_id.id,
                    'qty_to_produce': mrp_production_created_id.product_qty,
                    'date_planned_end': mrp_production_created_id.deadline_end or fields.Datetime.now(),
                })
                if mrp_production_created_id.move_raw_ids:
                    for move_raw_id in mrp_production_created_id.move_raw_ids:
                        self.create_mrp_production_rescursive_from_so(move_raw_id, mp_id)

    def create_mo_for_multi_bom(self, bom_line, mrp_plan, wiz_qty):
        mrp_production_obj = self.env['mrp.production']
        mrp_order_obj = self.env['mrp.order']
        for bl in bom_line:
            no_bom_qty = (wiz_qty*bl.product_qty)/ bl.bom_id.product_qty
            if bl.product_id.bom_ids:
                if bl.product_id.generate_wip_setting == True and bl.product_id.mo_creation_settings == 'none':
                    pass
                else:
                    location_id = False
                    stock_location_id = False
                    if bl.product_id.bom_ids[0].routing_id and bl.product_id.bom_ids[0].routing_id.operation_ids:
                        for operation in bl.product_id.bom_ids[0].routing_id.operation_ids:
                            if operation.workcenter_id and operation.workcenter_id.location_id:
                                location_id = operation.workcenter_id.location_id.id
                                stock_location_id = operation.workcenter_id.location_id.id
                                break

                    mrp_production_created_id = mrp_production_obj.create({
                        'mrp_plan_id': mrp_plan.id,
                        'product_id': bl.product_id.id,
                        'product_qty': no_bom_qty,
                        'bom_id': bl.product_id.bom_ids[0].id if bl.product_id.bom_ids else False,
                        'date_planned_start': fields.Datetime.now(),
                        'deadline_end': fields.Datetime.now(),
                        'user_id': self._uid,
                        'product_uom_id': bl.product_id.uom_id.id,
                        'routing_id': bl.product_id.bom_ids[0].routing_id and bl.product_id.bom_ids[
                            0].routing_id.id if bl.product_id.bom_ids else False,
                        'location_id': location_id,
                        'stock_location_id': stock_location_id,
                        'origin': mrp_plan.plan_id,
                        #'origin': origin,###addd
                        'sale_id':[(6, 0, mrp_plan.sale_id.ids)] or False,###addd
                    })
                    mrp_order_obj.create({
                        'mrp_plan_id': mrp_plan.id,
                        'mrp_production_id': mrp_production_created_id.id,
                        'qty_to_produce': mrp_production_created_id.product_qty,
                        'date_planned_end': mrp_production_created_id.deadline_end,
                    })

            #if bl.product_id.bom_ids:
            if bl.product_id.bom_ids:
                if bl.product_id.generate_wip_setting == True and bl.product_id.mo_creation_settings == 'none':
                    pass
                else:
                    for b_line in bl.product_id.bom_ids:
                        self.create_mo_for_multi_bom(b_line.bom_line_ids,mrp_plan,mrp_production_created_id.product_qty)

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    #sale_id = fields.Many2one('sale.order', string="Sale Order Reference")
    sale_id = fields.Many2many('sale.order','mrp_production_sale_order_rel','mrp_production_id','sale_order_id',string="Sale Order Reference",domain=[('state', 'not in', ['draft','cancel'])])
    
    
