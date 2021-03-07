# -*- coding: utf-8 -*-

import logging
import threading
from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)


# noinspection PyAttributeOutsideInit
class OrderPoint(models.Model):
    _name = 'stock.warehouse.orderpoint'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'stock.warehouse.orderpoint']

    # @api.onchange('pr_material_req')
    # def _onchange_pr_material_req(self):
    #     self.pr_approving_matrix_id = []
    #     if self.pr_material_req in ['create_rfq', 'create_po']:
    #         return {'domain': {'pr_approving_matrix_id': [('matrix_type', '=', 'amount')]}}
    #     if self.pr_material_req == 'create_purchase_request':
    #         return {'domain': {'pr_approving_matrix_id': [('matrix_type', '=', 'sequence')]}}
    #     else:
    #         return {'domain': {'pr_approving_matrix_id': []}}

    # @api.multi
    # @api.depends('pr_material_req', 'location_id')
    # def get_pr_approving_mtrix(self):
    #     for rec in self:
    #         domain = []
    #         if rec.pr_material_req in ['create_rfq', 'create_po']:
    #             domain.append(('matrix_type', '=', 'amount'))
    #         if rec.pr_material_req == 'create_purchase_request':
    #             domain.append(('matrix_type', '=', 'sequence'))
    #         if rec.branch_id:
    #             domain.append(('branch_id', '=', rec.branch_id.id))
    #         rec.pr_approving_matrix_id = self.env['pr.approving.matrix'].search(domain, limit=1).id

    # @api.multi
    # @api.depends('pr_material_req', 'location_id')
    # def get_mr_approving_mtrix(self):
    #     for rec in self:
    #         if rec.pr_material_req == 'create_material_request' and rec.location_id:
    #             rec.mr_approving_matrix_id = self.env['mr.approval.matrix'].search([('warehouse_id', '=', rec.warehouse_id.id)], limit=1).id

    @api.model
    def _get_type_internal(self):
        IrValue = self.env['ir.values'].sudo()
        type_internal = IrValue.get_default('stock.config.settings', 'type_internal')
        return type_internal
        
    name = fields.Char('Name', copy=False, required=True, default='', track_visibility='onchange')
    sequence = fields.Char('Reference', copy=False, track_visibility='onchange')
    pr_material_req = fields.Selection([
        ('create_material_request', 'Create Material Request'),
        ('create_purchase_request', 'Create Purchase Request'),
        ('create_rfq', 'Create RFQ'),
        # ('create_po', 'Create Purchase Order'),
        ('create_internal_transfer', 'Create Internal Transfer')
    ], string="Action To Take", required=True)
    branch_id = fields.Many2one('res.branch', 'Branch', track_visibility='onchange')
    supplier_id = fields.Many2one('res.partner', string="Supplier", domain="[('supplier', '=', True)]", track_visibility='onchange')
    user_ids = fields.Many2many('res.users', string="Mail To", track_visibility='onchange')
    # mr_approving_matrix_id = fields.Many2one('mr.approval.matrix', string="MR Approving Matrix", track_visibility='onchange', compute="get_mr_approving_mtrix")
    # pr_approving_matrix_id = fields.Many2one('pr.approving.matrix', string="PR Approving Matrix", track_visibility='onchange', compute="get_pr_approving_mtrix")
    source_loc_id = fields.Many2one('stock.location', 'Source Location', domain=[('usage', '=', 'internal')], track_visibility='onchange')
    readonly = fields.Boolean()
    parent_location_id = fields.Many2one('stock.location', compute='get_parent_location_id', store=True, track_visibility='onchange')
    order_pt_line_ids = fields.One2many('stock.warehouse.orderpoint.line', 'order_point_id', string="Reordering Rule")
    product_min_qty = fields.Float(
        'Minimum Quantity', digits=dp.get_precision('Product Unit of Measure'), required=False,
        help="When the virtual stock goes below the Min Quantity specified for this field, Odoo generates "
             "a procurement to bring the forecasted quantity to the Max Quantity.")
    product_max_qty = fields.Float(
        'Maximum Quantity', digits=dp.get_precision('Product Unit of Measure'), required=False,
        help="When the virtual stock goes below the Min Quantity, Odoo generates "
             "a procurement to bring the forecasted quantity to the Quantity specified as Max Quantity.")

    type_internal = fields.Selection([('yes', 'Use Transit Location'), ('no', 'Direct Location')], 
                    string='Internal transfer type', default=_get_type_internal, readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(OrderPoint, self).default_get(fields)
        res['location_id'] = False
        return res

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        """ Finds location id for changed warehouse. """
        location_obj = self.env['stock.location']
        location_ids = location_obj.search([('usage', '=', 'internal')])
        total_warehouses = self.warehouse_id
        if total_warehouses:
            addtional_ids = []
            for warehouse in total_warehouses:
                store_location_id = warehouse.view_location_id.id
                addtional_ids.extend([y.id for y in location_obj.search(
                    [('location_id', 'child_of', store_location_id), ('usage', '=', 'internal')])])
            location_ids = addtional_ids
        elif self.company_id:
            total_warehouses = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)])
            addtional_ids = []
            for warehouse in total_warehouses:
                store_location_id = warehouse.view_location_id.id
                addtional_ids.extend([y.id for y in location_obj.search(
                    [('location_id', 'child_of', store_location_id), ('usage', '=', 'internal')])])
            location_ids = addtional_ids
        else:
            location_ids = [p.id for p in location_ids]
        return {
            'domain':
                {
                    'location_id': [('id', 'in', location_ids)]
                },
            'value':
                {
                    'location_id': False
                }
        }

    @api.multi
    @api.constrains('pr_material_req', 'product_id', 'company_id', 'branch_id', 'warehouse_id', 'location_id', 'approving_matrix_id')
    def constrains_duplicate(self):
        for res in self:
            domain = [('product_id', '=', res.product_id.id), ('company_id', '=', res.company_id.id),
                      ('pr_material_req', '=', res.pr_material_req), ('warehouse_id', '=', res.warehouse_id.id),
                      ('location_id', '=', res.location_id.id), ('id', '!=', res.id)
                      ]
            # if res.mr_approving_matrix_id:
            #     domain.append(('mr_approving_matrix_id', '=', res.mr_approving_matrix_id.id))
            # elif res.pr_approving_matrix_id:
            #     domain.append(('pr_approving_matrix_id', '=', res.pr_approving_matrix_id.id))
            if res.branch_id:
                domain.append(('branch_id', '=', res.branch_id.id))
            if self.search(domain):
                raise UserError(_('You can not create rule that has same value with the exisiting rules.'))

    @api.depends('warehouse_id')
    def get_parent_location_id(self):
        """
        Get warehouse Parent ID
        """
        for rec in self:
            if rec.warehouse_id:
                rec.parent_location_id = rec.warehouse_id.lot_stock_id.location_id.id

    @api.constrains('pr_material_req', 'source_loc_id')
    def constrains_source_location_on_internal_material(self):
        """
        Constrains on Source Location in Internal Transfer
        """
        if self.pr_material_req == 'create_internal_transfer' and self.location_id.id == self.source_loc_id.id:
            raise UserError(_('You can not select Same Location for Source and destination.!!!'))

    @api.onchange('pr_material_req')
    def onchange_pr_material_request(self):
        """
        Value to create readonly Pr Material Request
        """
        if self.pr_material_req in ('create_material_request', 'create_internal_transfer'):
            self.readonly = True
            # self.lead_type = 'net'
        else:
            self.readonly = False

    @api.model
    def create(self, vals):
        """
        Create
        """
        res = super(OrderPoint, self).create(vals)
        # if res.pr_material_req in ('create_material_request', 'create_internal_transfer'):
        #     res.lead_type = 'net'
        res.sequence = self.env['ir.sequence'].next_by_code('stock.orderpoint')
        return res

    @api.multi
    def write(self, vals):
        """
        Create
        """
        # if 'pr_material_req' in vals and vals['pr_material_req'] in (
        #         'create_material_request', 'create_internal_transfer'):
        #     self.lead_type = 'net'
        return super(OrderPoint, self).write(vals)

    @api.multi
    def check_product_quantity_reordering(self, location_id, product_id):
        """
        Check Reordering Rule
        """
        query = """
                select sum(sq.qty) from stock_quant as sq
                left join stock_location as sl on sl.id = sq.location_id
                where sl.usage = 'internal' and sq.product_id = %s and sq.location_id = %s
                """ % (product_id.id, location_id.id)
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        stock_product_qty = result[0]['sum'] or 0.0
        return stock_product_qty

    @api.multi
    def get_orderpoint_list(self):
        """
        Get Order Point List
        """
        stock_orderpoint = self.env['stock.warehouse.orderpoint'].sudo().search([
            ('pr_material_req', 'in', ['create_purchase_request', 'create_material_request', 'create_rfq',
                                       'create_internal_transfer'])]) or []
        stock_orderpoint_list = []
        for rec in stock_orderpoint or []:
            stock_product_qty = rec.check_product_quantity_reordering(product_id=rec.product_id,
                                                                      location_id=rec.location_id)
            if rec.product_min_qty >= stock_product_qty:
                stock_orderpoint_list.append(rec.id)
        return stock_orderpoint_list

    @api.model
    def reordering_scheduler(self):
        """
        Scheduler
        """
        _logger.info("====Reordering Rule Scheduler Start===")
        order_point_obj = self.env['stock.warehouse.orderpoint']
        purchase_obj = self.env['purchase.order']
        purchase_orderline_obj = self.env['purchase.order.line']
        purchase_request_obj = self.env['purchase.request']
        purchase_request_line_obj =self.env['purchase.request.line']
        material_request_obj = self.env['std.material.request']
        material_request_line_obj = self.env['std.item.mr']
        internal_transfer_obj = self.env['internal.transfer']
        internal_transfer_line_obj = self.env['internal.transfer.line']
        orderpoint_ids = order_point_obj.sudo().search([
            ('pr_material_req', 'in', ['create_purchase_request', 'create_material_request', 'create_rfq',
                                       'create_internal_transfer'])]) or []
        type_obj = self.env['stock.picking.type']
        mail_data_list = []
        user_list = []

        # for Material Request
        material_request_ids = orderpoint_ids.filtered(lambda x: x.pr_material_req == 'create_material_request')
        _logger.info("Reorder for Material Request : %s" % material_request_ids.mapped('name'))
        for material_line in material_request_ids:
            types = type_obj.search(
                            [('code', '=', 'internal'), ('warehouse_id', '=', material_line.warehouse_id.id)],
                            limit=1)
            material_request = material_request_obj.search([('requested_by', '=', self.env.user.id),
                                                            ('destination_location', '=', material_line.location_id.id),
                                                            ('status', 'in', ['draft', 'to_approve', 'approved'])])
            material_req_line = material_request.mapped('product_line').filtered(lambda x: x.product == material_line.product_id)
            if material_req_line:
                continue

            stock_product_qty = material_line.check_product_quantity_reordering(
                product_id=material_line.product_id,
                location_id=material_line.location_id)
            material_line_request_ids = material_line.mapped('order_pt_line_ids').filtered(
                lambda x: x.start_date <= fields.Date.today() <= x.end_date)

            for line in material_line_request_ids:
                if line.product_min_qty >= stock_product_qty:
                    max_current = (line.product_max_qty - stock_product_qty)
                    current_multiple = max_current % line.qty_multiple
                    product_qty = abs(max_current - current_multiple) or 0.0
                    schedule_date = date.today() + timedelta(days=line.lead_time_demand)
                    material_vals = {
                        'requested_by': self.env.user.id,
                        'picking_type': types.id or False,
                        'destination_location': material_line.location_id.id,
                        'schedule_date': schedule_date,
                    }
                    mr_name = material_request_obj.create(material_vals)
                    vals = {
                        'product': material_line.product_id.id or False,
                        'quantity': product_qty or 0.0,
                        'std_mr': mr_name.id,
                        'destination_location_id': material_line.location_id.id
                    }
                    material_request_line_obj.create(vals)

                    for usr in material_line.user_ids:
                        if usr not in user_list:
                            user_list.append(usr)
                        data = {
                            'user_id': usr.id,
                            'location_id': material_line.product_id.property_stock_inventory.id or '',
                            'product_id': material_line.product_id.id or '',
                            'action_name': "Material Request  #" + mr_name.request_reference,
                            'minimum_qty': line.product_min_qty,
                            'maximum_qty': line.product_max_qty,
                            'current_qty': stock_product_qty,
                            'product_qty': product_qty,
                            'stock_loc_id': material_line.location_id.id,
                            'warehouse_id': material_line.warehouse_id.id,
                            'company_id': material_line.company_id.id,
                            # 'lead_days': material_line.lead_days,
                            # 'lead_type': material_line.lead_type,
                            'reordering_rule': material_line.sequence
                        }
                        mail_data_list.append(data)

                    if not mr_name.source_document:
                        mr_name.source_document = 'Reordering Rules: ' + material_line.sequence
                    else:
                        mr_name.source_document = 'Reordering Rules: ' + mr_name.source_document + material_line.sequence

                    for mr in mr_name.product_line:
                        mr.onchange_product()
                    _logger.info("Material Request : %s" % mr_name.name)
        # for Purchase Request
        purchase_request_ids = orderpoint_ids.filtered(lambda x: x.pr_material_req == 'create_purchase_request')
        _logger.info("Reorder for Purchase Request : %s" % purchase_request_ids.mapped('name'))
        for purchase_line in purchase_request_ids:
            types = type_obj.search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', purchase_line.warehouse_id.id)],
                limit=1)
            purchase_requests = purchase_request_obj.search([('company_id', '=', purchase_line.company_id.id),
                                                             ('picking_type_id', 'in', types.ids),
                                                             ('state', 'in', ['draft', 'to_approve', 'approved'])])
            purchase_req_line = purchase_requests.mapped('line_ids').filtered(lambda x:
                                    x.product_id == purchase_line.product_id)
            if purchase_req_line:
                continue

            stock_product_qty = purchase_line.check_product_quantity_reordering(
                product_id=purchase_line.product_id,
                location_id=purchase_line.location_id)
            purchase_line_request_ids = purchase_line.mapped('order_pt_line_ids').filtered(
                lambda x: x.start_date <= fields.Date.today() <= x.end_date)

            for p_line in purchase_line_request_ids:
                if p_line.product_min_qty >= stock_product_qty:
                    # product_qty = abs(p_line.product_max_qty - stock_product_qty) or 0.0
                    pr_vals = {
                        'state': 'draft',
                        'picking_type_id': types.id or False,
                        'branch_id': purchase_line.branch_id and purchase_line.branch_id.id or False,
                    }
                    pr_name = purchase_request_obj.create(pr_vals)
                    max_current = (p_line.product_max_qty - stock_product_qty)
                    current_multiple = max_current % p_line.qty_multiple
                    product_qty = abs(max_current - current_multiple) or 0.0
                    schedule_date = date.today() + timedelta(days=p_line.lead_time_demand)
                    vals = {
                        'product_id': purchase_line.product_id.id or False,
                        'product_qty': product_qty or 0.0,
                        'request_id': pr_name.id,
                        'date_required': schedule_date,
                    }
                    purchase_request_line_obj.create(vals)

                    # create mail data
                    for usr in purchase_line.user_ids:
                        if usr not in user_list:
                            user_list.append(usr)
                        data = {
                            'user_id': usr.id,
                            'location_id': purchase_line.product_id.property_stock_inventory.id or '',
                            'product_id': purchase_line.product_id.id or '',
                            'action_name': "Purchase Request  #" + str(pr_name.name),
                            'minimum_qty': p_line.product_min_qty,
                            'maximum_qty': p_line.product_max_qty,
                            'current_qty': stock_product_qty,
                            'product_qty': product_qty,
                            'stock_loc_id': purchase_line.location_id.id,
                            'warehouse_id': purchase_line.warehouse_id.id,
                            'company_id': purchase_line.company_id.id,
                            # 'lead_days': purchase_line.lead_days,
                            # 'lead_type': purchase_line.lead_type,
                            'reordering_rule': purchase_line.sequence
                        }
                        mail_data_list.append(data)

                    if not pr_name.origin:
                        pr_name.origin = 'Reordering Rules: ' + purchase_line.sequence
                        pr_name.is_reorder = True
                    else:
                        pr_name.origin = 'Reordering Rules: ' + pr_name.origin + purchase_line.sequence
                    _logger.info("Purchase Request : %s" % pr_name.name)
        # for RFQ and Purchase Order
        rfq_po_request_ids = orderpoint_ids.filtered(lambda x:x.pr_material_req in ['create_rfq'])
        _logger.info("Reorder for RFQ : %s" % rfq_po_request_ids.mapped('name'))
        for po_rfw in rfq_po_request_ids:
            types = type_obj.search([('code', '=', 'incoming'),
                                     ('warehouse_id', '=', po_rfw.warehouse_id.id)], limit=1)
            purchase_orders = purchase_obj.search([('partner_id', '=', po_rfw.supplier_id.id),
                                                   ('picking_type_id', 'in', types.ids),
                                                   ('state', 'in',
                                                    ['draft', 'waiting_for_approval', 'sent', 'rfq_confirmed', 'rfq_approved'])])
            purchase_order_line = purchase_orders.mapped('order_line').filtered(
                lambda x: x.product_id == po_rfw.product_id)
            if purchase_order_line:
                continue

            stock_product_qty = self.check_product_quantity_reordering(product_id=po_rfw.product_id,
                                                                       location_id=po_rfw.location_id)
            rfq_po_request_line_ids = po_rfw.mapped('order_pt_line_ids').filtered(
                lambda x: x.start_date <= fields.Date.today() <= x.end_date)

            for r_line in rfq_po_request_line_ids:
                if r_line.product_min_qty >= stock_product_qty:
                    schedule_date = date.today() + timedelta(days=r_line.lead_time_demand)
                    rfq = {
                        'partner_id': po_rfw.supplier_id.id,
                        'state': 'draft',
                        'date_planned': schedule_date,
                        'branch_id': po_rfw.branch_id and po_rfw.branch_id.id or False,
                        'picking_type_id': types[0].id or False,
                    }
                    po_id = purchase_obj.create(rfq)
                    po_id.onchange_partner_id()

                    max_current = (r_line.product_max_qty - stock_product_qty)
                    current_multiple = max_current % r_line.qty_multiple
                    product_qty = abs(max_current - current_multiple) or 0.0
                    rfq_line = {
                        'product_id': po_rfw.product_id.id,
                        'name': po_rfw.product_id.name,
                        'product_qty': product_qty or 0.0,
                        'date_planned': schedule_date,
                        'order_id': po_id.id,
                        'product_uom': po_rfw.product_id.uom_po_id.id,
                        'price_unit': po_rfw.product_id.standard_price or 1
                        }
                    po_line_id = purchase_orderline_obj.create(rfq_line)
                    po_line_id.onchange_product_id()
                    po_line_id.product_qty = product_qty
                    po_line_id._onchange_quantity()
                    po_line_id.write({'date_planned': schedule_date})
                    for usr in po_rfw.user_ids:
                        if usr not in user_list:
                            user_list.append(usr)
                        data = {
                            'user_id': usr.id,
                            'location_id': po_rfw.product_id.property_stock_inventory.id or '',
                            'product_id': po_rfw.product_id.id or '',
                            'action_name': "RFQ  #" + po_id.name,
                            'minimum_qty': r_line.product_min_qty,
                            'maximum_qty': r_line.product_max_qty,
                            'current_qty': stock_product_qty,
                            'supplier_id': po_rfw.supplier_id.id,
                            'product_qty': product_qty,
                            'stock_loc_id': po_rfw.location_id.id,
                            'warehouse_id': po_rfw.warehouse_id.id,
                            'company_id': po_rfw.company_id.id,
                            # 'lead_days': po_rfw.lead_days,
                            # 'lead_type': po_rfw.lead_type,
                            'reordering_rule': po_rfw.sequence
                        }
                        mail_data_list.append(data)

                    if not po_id.origin:
                        po_id.origin = 'Reordering Rules: ' + po_rfw.sequence
                    else:
                        po_id.origin = 'Reordering Rules: ' + po_id.origin + po_rfw.sequence
                    _logger.info("RFQ : %s" % po_id.name)
        # for Internal Transfer
        internal_transfer_request_ids = orderpoint_ids.filtered(lambda x: x.pr_material_req == 'create_internal_transfer')
        _logger.info("Reorder for ICT : %s" % internal_transfer_request_ids.mapped('name'))

        IrValue = self.env['ir.values'].sudo()
        type_internal = IrValue.get_default('stock.config.settings', 'type_internal')
        if type_internal == 'yes':
            is_transit = True
        else:
            is_transit = False

        for internal in internal_transfer_request_ids:
            internal_transfers = internal_transfer_obj.search([('source_loc_id', '=', internal.source_loc_id.id),
                                                              ('dest_loc_id', '=', internal.location_id.id),
                                                              ('state', '=', 'draft')])
            transfer_line = internal_transfers.mapped('product_line_ids').filtered(lambda x:
                                                                                   x.product_id == internal.product_id)
            if transfer_line:
                continue

            stock_product_qty = self.check_product_quantity_reordering(product_id=internal.product_id,
                                                                        location_id=internal.location_id)
            internal_transfer_request_line_ids = internal.mapped('order_pt_line_ids').filtered(
                lambda x: x.start_date <= fields.Date.today() <= x.end_date)
            for i_line in internal_transfer_request_line_ids:
                if i_line.start_date <= fields.Date.today() <= i_line.end_date and i_line.product_min_qty >= stock_product_qty:
                    # product_qty = abs(i_line.product_max_qty - stock_product_qty) or 0.0
                    max_current = (i_line.product_max_qty - stock_product_qty)
                    current_multiple = max_current % i_line.qty_multiple
                    product_qty = abs(max_current - current_multiple) or 0.0
                    schedule_date = date.today() + timedelta(days=i_line.lead_time_demand)
                    it_data = {
                        'source_loc_id': internal.source_loc_id.id,
                        'dest_loc_id': internal.location_id.id,
                        'state': 'draft',
                        'source_doc': 'Reordering Rules: ' + internal.sequence,
                        'schedule_date': schedule_date,
                        'is_transit':is_transit,
                    }                    
                    it_id = internal_transfer_obj.create(it_data)
                    it_id.onchange_source_loc_id()
                    it_id.onchange_dest_loc_id()
                    vals = {
                        'product_id': internal.product_id.id or False,
                        'product_uom_qty': product_qty or 0.0,
                        'source_loc_id': internal.source_loc_id.id,
                        'transfer_id': it_id.id,
                        'dest_loc_id': internal.location_id.id,
                        'sub_source_loc_id': internal.source_loc_id.id,
                        'sub_dest_loc_id': internal.location_id.id
                    }
                    internal_transfer_line_obj.create(vals)
                    for usr in internal.user_ids:
                        if usr not in user_list:
                            user_list.append(usr)
                        data = {
                            'user_id': usr.id,
                            'location_id': internal.product_id.property_stock_inventory.id or '',
                            'product_id': internal.product_id.id or '',
                            'action_name': "Internal Transfer #" + str(it_id.name),
                            'minimum_qty': i_line.product_min_qty,
                            'maximum_qty': i_line.product_max_qty,
                            'current_qty': stock_product_qty,
                            'product_qty': product_qty,
                            'stock_loc_id': internal.location_id.id,
                            'source_loc_id': internal.source_loc_id.id,
                            'warehouse_id': internal.warehouse_id.id,
                            'company_id': internal.company_id.id,
                            # 'lead_days': internal.lead_days,
                            # 'lead_type': internal.lead_type,
                            'reordering_rule': internal.sequence
                        }
                        mail_data_list.append(data)

                    if not it_id.source_doc:
                        it_id.source_doc = 'Reordering Rules: ' + internal.sequence
                    elif it_id.source_doc and internal.sequence not in it_id.source_doc:
                        it_id.source_doc = 'Reordering Rules: ' + it_id.source_doc + internal.sequence
                    for it in it_id.product_line_ids:
                        it.product_id_change()
                    _logger.info("ICT : %s" % it_id.name)
        self._cr.execute("delete from reorder_mail_list")
        self._cr.execute("delete from user_mail_data")
        self._cr.execute("delete from user_location")
        self._cr.execute("delete from user_details")
        mailer_obj = self.env['reorder.mail.list']
        # create mail user data
        for ml in mail_data_list:
            mailer_obj.sudo().create(ml)
        # send mail function
        user_mail_obj = self.env['user.mail.data']
        for u in user_list:
            u_mail_id = user_mail_obj.search([('user_id', '=', u.id)])
            u_mail_id.send_reorder_mail()
        _logger.info("====Reordering Rule Scheduler End===")
        return True


class OrderPointLine(models.Model):
    _name = 'stock.warehouse.orderpoint.line'

    order_point_id = fields.Many2one('stock.warehouse.orderpoint')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    product_max_qty = fields.Float('Maximum QTY')
    product_min_qty = fields.Float('Minimum QTY')
    qty_multiple = fields.Float('Qty Multiple', default=1)


class InternalTransferLine(models.Model):
    _inherit = 'internal.transfer.line'

    sub_source_loc_id = fields.Many2one('stock.location', 'Source Location', domain=[('usage', '=', 'internal')])
    sub_dest_loc_id = fields.Many2one('stock.location', 'Destination Location', domain=[('usage', '=', 'internal')])


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    # source_origin = fields.Char('Source Doc')
    is_reorder = fields.Boolean('Is Re-Order', default=False, copy=False)


class ProcurementOrderpointConfirm(models.TransientModel):
    _inherit = 'procurement.orderpoint.compute'
    _description = 'Compute Minimum Stock Rules'

    @api.multi
    def procure_calculation(self):
        threaded_calculation = threading.Thread(target=self._procure_calculation_orderpoint, args=())
        threaded_calculation.start()
        self.env['stock.warehouse.orderpoint'].reordering_scheduler()
        return {'type': 'ir.actions.act_window_close'}
