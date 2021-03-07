# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import Warning, ValidationError
# from odoo.addons.livechat_ext.models import res_user
from __builtin__ import True
import logging
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    mr_id = fields.Many2one('std.material.request', compute='_compute_mr_id', string='Sourced Document')

    def _compute_mr_id(self):
        for record in self:
            internal_transfer = self.env['internal.transfer'].search([('name', '=', record.origin)])
            if internal_transfer and internal_transfer.mr_id:
                record.mr_id = internal_transfer.mr_id.id


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    mr_id = fields.Many2one('std.material.request', string='Sourced Document', readonly=True)


#inherited internal transfer so we can count how many internal transfer done for MR.
class InternalTransfer(models.Model):
    _inherit = 'internal.transfer'

    mr_id = fields.Many2one('std.material.request', string='Sourced Document', readonly=True)

class CancelReasonWizard(models.TransientModel):
    _inherit = 'cancel.reason.wizard'

    @api.multi
    def cancel_internal_receipt(self):
        internal_transfer_id = self.env['internal.transfer'].browse([self._context.get('active_id')])
        internal_transfer_id.write({'state': 'cancel', 'cancel_reason': self.cancel_reason})
        internal_transfer_id.picking_ids.action_cancel()
        std_item_mr_lines_ids = self.env['std.item.mr.lines'].search([('internal_transfer_ref', '=', internal_transfer_id.id)])
        if std_item_mr_lines_ids:
            std_item_mr_lines_ids.write({'state_intt': 'cancel', 'cancel_reason': self.cancel_reason})

class MRInternalTransferWizard(models.TransientModel):
    _name = 'mr.internal.transfer'

    warehouse_id = fields.Many2one('stock.location', string="Sourced Location")
    internal_transfer_receipt = fields.One2many('mr.internal.transfer.receipt', 'mr_internal_transfer')
    is_split_line = fields.Boolean(string='Is Split Line ?', default=False)
    is_create_internal_transfer = fields.Boolean(string='Is Create Internal Transfer ?', compute='_get_is_create_internal_transfer')
    is_transit = fields.Boolean(string='Is Transit')

    @api.depends('warehouse_id', 'internal_transfer_receipt', 'internal_transfer_receipt.qty_transfer')
    def _get_is_create_internal_transfer(self):
        for record in self:
            len_of_line = len(record.internal_transfer_receipt)
            qty_transfer_lines = len(record.internal_transfer_receipt.filtered(lambda r: r.qty_transfer > 0))
            if len_of_line == qty_transfer_lines and len(record.internal_transfer_receipt) != 0:
                record.is_create_internal_transfer = True
            else:
                record.is_create_internal_transfer = False

    @api.multi
    def create_rfq(self):
        transfer_line = []
        for line in self.internal_transfer_receipt:
            transfer_line.append((0,0, {
                'name' : line.description,
                'product_id' :  line.product_id.id,
                'product_uom_qty' : line.qty_transfer, 
                'price_unit' : line.product_id.lst_price or 0.0,
                'uom_id' : line.uom_id.id,
                'source_loc_id': self.warehouse_id.id,
                'dest_loc_id': self.env.context.get('dest_loc_id'),
            }))
        values = {
            'partner_id' : self.env.context.get('partner_id'),
            'schedule_date' : self.env.context.get('schedule_date'),
            'source_loc_id' : self.warehouse_id.id,
            'dest_loc_id' : self.env.context.get('dest_loc_id'),
            'product_line_ids' : transfer_line,
            'mr_id' : self.env.context.get('active_id'),
            'source_doc': self.env.context.get('origin')
        }
        transfer_id = self.env['internal.transfer'].create(values)
        transfer_id.onchange_source_loc_id()
        transfer_id.onchange_dest_loc_id()
        return


class InternalTransferReceiptWizard(models.TransientModel):
    _name = 'mr.internal.transfer.receipt'

    @api.model
    def _getDomain(self):
        stock_location = self.product_id.stock_location.filtered(lambda r: r.available_qty>=1)
        location_ids = []
        if stock_location:
            location_ids = [x for x in stock_location.stock_location_id.id]
        return [('id', 'in', location_ids)]

    mr_id = fields.Many2one('std.material.request', 'Material Request')
    product_id = fields.Many2one('product.product', 'Product')
    current_quantity = fields.Float(string='Current Quantity')
    description = fields.Char()
    process_qty = fields.Float('Quantity to Process')
    qty_transfer = fields.Float('Quantity to Transfer' ,required=True)
    uom_id = fields.Many2one('product.uom', 'UOM')
    source_loc_id = fields.Many2one('stock.location', string='Source Location', domain=_getDomain) 
    filter_location_ids = fields.Many2many('stock.location', compute='_get_locations', store=False)
    mr_internal_transfer = fields.Many2one('mr.internal.transfer')
    destination_location_id = fields.Many2one('stock.location', string='Destination Location')
    is_split_line = fields.Boolean(string='Is Split Line?', compute="_get_is_split_line" ,default=False, store=False)

    @api.model
    def create(self, vals):
        if ('current_quantity' in vals) and ('qty_transfer' in vals):
            if vals['qty_transfer'] > vals['current_quantity']:
                raise ValidationError(_('The quantity on location selected is less then your request'))
        if ('process_qty' in vals) and ('qty_transfer' in vals):
            if vals['qty_transfer'] > vals['process_qty']:
                raise ValidationError(_('You are not allow to request more than quantity process'))
        res = super(InternalTransferReceiptWizard, self).create(vals)
        return res

    @api.model
    def write(self, vals):
        current_qty  =  float(vals['current_quantity']) if ('current_quantity' in vals) else float(self.current_quantity) 
        qty_transfer =  float(vals['qty_transfer']) if ('qty_transfer' in vals) else float(self.qty_transfer) 
        process_qty =  float(vals['process_qty']) if ('process_qty' in vals) else float(self.process_qty) 
        
        if current_qty and qty_transfer:
            if qty_transfer > current_qty:
                raise ValidationError(_('The quantity on location selected is less then your request'))

        if process_qty and qty_transfer:
            if qty_transfer > process_qty:
                raise ValidationError(_('You are not allow to request more than quantity process'))
        
        res = super(InternalTransferReceiptWizard, self).write(vals)
        return res

    @api.onchange('process_qty','qty_transfer','current_quantity','source_loc_id')
    def quantity_check(self):
        if self.qty_transfer > self.current_quantity:
            raise ValidationError(_('The quantity on location selected is less then your request'))
        
        if self.qty_transfer > self.process_qty:
            raise ValidationError(_('You are not allow to request more than quantity process'))
        
    @api.onchange('source_loc_id')
    def change_location(self):
        if self.source_loc_id:
            stock_location = self.product_id.stock_location.filtered(lambda r: r.stock_location_id.id == self.source_loc_id.id)
            print "+++++++++++++++++++++++++++++++",stock_location
            if stock_location:
                self.current_quantity = stock_location.available_qty
            else:
                self.current_quantity = 0.0

    @api.depends('process_qty')
    def _get_locations(self):
        for record in self:
            data_ids = []
            stock_location_product_ids = self.product_id.stock_location.filtered(lambda r: r.available_qty >= self.process_qty)
            for stock_location_product_id in stock_location_product_ids:
                location_id = self.env['stock.location'].search([('id','=', stock_location_product_id.stock_location_id.id)])
                if location_id:
                    data_ids.append(location_id.id)
            record.filter_location_ids = [(6, 0, data_ids)]

    @api.multi
    def split_line(self):
        context = self.env.context.copy()
        for record in self:
            split_qty = record.qty_transfer
            record.write({'process_qty': record.process_qty - split_qty, 'qty_transfer': split_qty})
            new_line = record.copy({'process_qty': record.process_qty, 'qty_transfer': 0.0})
            record.change_location()
            new_line.change_location()
            context.update({
                'partner_id': new_line.mr_id.requested_by.id,
                'schedule_date': new_line.mr_id.schedule_date,
                'dest_loc_id': new_line.mr_id.destination_location.id,
                'origin': new_line.mr_id.request_reference,
                'mr_id' : new_line.mr_id.id
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Create Internal Transfer',
                'res_model': 'mr.internal.transfer',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': record.mr_internal_transfer.id,
                'target': 'new',
                'context': context,
            }

    @api.depends('process_qty', 'qty_transfer')
    def _get_is_split_line(self):
        for record in self:
            if record.qty_transfer > 0 and record.qty_transfer < record.process_qty:
                record.is_split_line = True
            else:
                record.is_split_line = False

class PurchaseRequestWizard(models.TransientModel):
    _name = 'std.purchase.request.wizard'

    pr_wizard_line = fields.One2many('purchase.request.wizard.line', 'mr_pr_wizard')

    def create_pr(self):
        pr_line = []
        for line in self.pr_wizard_line:
            vals = {
                'product_id' : line.product_id.id,
                'name' : line.description,
                'product_uom_id' : line.uom_id.id,
                'product_qty' : line.qty_purchase,
                'date_required' : line.request_date,
                # 'procurement_id' : line.procurement_order.id,
            }
            pr_line.append((0,0, vals))
        pr_obj = self.env['purchase.request'].create({'line_ids': pr_line, 'mr_id' : self.pr_wizard_line[0].mr_id.id})
        return

class PurchaseRequestWizardLine(models.TransientModel):
    _name = 'purchase.request.wizard.line'

    mr_id = fields.Many2one('std.material.request', 'Material Request')
    product_id = fields.Many2one('product.product', 'Product')
    description = fields.Char()
    qty_purchase = fields.Float('Quantity to Purchase')
    uom_id = fields.Many2one('product.uom', 'UOM')
    mr_pr_wizard = fields.Many2one('std.purchase.request.wizard')
    request_date = fields.Date(string ="Request Date", required=True)
    destination_location_id = fields.Many2one('stock.location', string='Destination Location')

class StdMaterialRequest(models.Model):
    _name = 'std.material.request'
    _description = "Material Request"
    _rec_name = 'request_reference'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.one
    def _compute_transfer_count(self):
        for inter in self:
            internal_transfer_count = len(inter.env['internal.transfer'].search(['&',('mr_id', '=', inter.id),('state','!=','cancel')]))
            if internal_transfer_count:
                inter.transfer_count = internal_transfer_count
                inter.update({
                    'transfer_count' : internal_transfer_count,
                    })

    def _compute_pr_count(self):
        for obj in self:
            rec = obj.env['purchase.request'].search([('mr_id', '=', obj.id)])
            obj.pr_count = len(rec)
            obj.update({
                'pr_count' : len(rec),
                })
            
    @api.depends('approving_matrix_id', 'status')
    def _compute_approving_lines(self):
        line_vals=[]
        for record in self:
            time_stamp = datetime.now() if record.status in ('approved', 'rejected') else False
            status = ''
            if record.status not in ('done', 'confirm'):
                status = record.status
            for line in record.approving_matrix_id.product:
                line_vals.append((0,0, {
                    'sequence' : line.sequence,
                    'approver' : [(6, 0, line.approver.ids)],
                    'matrix_id' : line.matrix_id.id,
                    'minimal_approver': line.minimal_approver,
                    'approve_state': status,
                    'time_stamp': time_stamp
                    }))
            record.approving_matrix_line_ids = line_vals

    @api.one
    @api.depends('approving_matrix_id','current_approver_ids')
    def _compute_user_in_approver(self):
        user_approver = False
        if self.current_approver_ids and self.current_approver_ids.filtered(lambda r: r.id == self.env.user.id):
            user_approver = True
#         elif self.approving_matrix_id.product.filtered(lambda r: r.approver.id == self.env.user.id):
#             user_approver = True

        self.user_approver = user_approver

    @api.model
    def _get_approval_on_off_value(self):
        IrValue = self.env['ir.values'].sudo()
        approval_on_off_material_request = IrValue.get_default('stock.config.settings', 'approval_on_off_material_request')
        return approval_on_off_material_request

    @api.one
    @api.depends('product_line')
    def _compute_bool_product_line(self):
        if self.product_line:
            self.bool_product_line = True
            
    name = fields.Char(string='Name')
    product_line = fields.One2many(comodel_name="std.item.mr", inverse_name="std_mr", string="Product")
    bool_product_line = fields.Boolean('Product available', compute="_compute_bool_product_line")
    request_reference = fields.Char(string="Request Reference", required=True, default="/", track_visibility='onchange')
    requested_by = fields.Many2one('res.partner', string="Requested By", required=True, default=lambda self: self.env.user.partner_id.id)
    destination_location = fields.Many2one('stock.location', string="Destination Location", required=True, track_visibility='onchange')
    approving_matrix_id = fields.Many2one('mr.approval.matrix', string="Approval Matrix", copy=False, store=True, 
                                          ondelete="restrict", help=''' Approval matrix will autofill base on selected destination location''', 
                                          compute='_get_approving_matrix')
    user_approver = fields.Boolean('User is approver',compute="_compute_user_in_approver")
    schedule_date = fields.Date(string="Scheduled Date", default=fields.Date.context_today)
    expire_date = fields.Datetime(string='Expired Date')
    description = fields.Text()
    source_document = fields.Char(string='Sourced Document')
    picking_type = fields.Many2one('stock.picking.type' , string="Picking Type", compute='_get_approving_matrix', store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'), 
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),
        ('done', 'Done')
        ],
        default="draft", track_visibility='onchange')
    status_1 = fields.Selection(related="status")
    status_2 = fields.Selection(related="status")
    approval_state = fields.Selection(related="status")
    approving_matrix_line_ids = fields.One2many('std.mr.approval.matrix.line','material_request_id', 
        string="Approving Matrix Lines", compute="_compute_approving_lines", store=True)
    current_approver_ids = fields.Many2many('res.users','material_request_users_rel','mr_id','user_id','Current Approvers')

    transfer_count = fields.Integer(default=0, string='Internal Transfer Count', compute="_compute_transfer_count")
    pr_count = fields.Integer(default=0, compute="_compute_pr_count")
    source_document = fields.Char(string='Source Document')
    is_approve_button = fields.Boolean(string='Is Approve Button', compute='_get_approve_button', store=False)
    approval_matrix_line_id = fields.Many2one('std.mr.approval.matrix.line', string='Std Approval Matrix Line', compute='_get_approve_button', store=False)
    approval_on_off_material_request = fields.Boolean(string='Approval Matrix Material Request', default=_get_approval_on_off_value)

    @api.onchange('requested_by')
    def change_destination_location(self):
        user = self.env.user
        if user.restrict_locations:
            domain = [('usage','=', 'internal'), ('id', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids)]
        else:
            domain = []
        return {'domain': {'destination_location': domain}}

    @api.multi
    def button_confirm(self):
        for record in self:
            record.write({'status': 'confirm'})

    @api.onchange('destination_location')
    def change_warehouse(self):
        self.product_line = []

    @api.multi
    def action_cancel(self):
        for record in self:
            record.write({'status': 'cancel'})
            record.approving_matrix_line_ids.write({'approve_state': 'cancel', 'time_stamp': datetime.now()})

    @api.multi
    def material_request_done(self):
        for record in self:
            show_popup = False
            for line in record.product_line:
                if line.quantity != sum(line.std_item_mr_lines.mapped('remain_product')):
                    show_popup = True
            if show_popup:
                return {
                    'name'     : 'Warning',
                    'type'     : 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'show.material.done.popup',
                    'view_type': 'form',
                    'target'   : 'new'
               }
            else:
                record.write({'status': 'done'})

    @api.multi
    def _get_approve_button(self):
        for record in self:
            if record.status == 'to_approve':
                matrix_line = sorted(record.approving_matrix_line_ids.filtered(lambda r:r.approve_state == 'to_approve'), key=lambda r:r.sequence)
                if len(matrix_line) == 0:
                    record.is_approve_button = False
                elif len(matrix_line) > 0:
                    matrix_line_id = matrix_line[0]
                    if self.env.user.id in matrix_line_id.approver.ids and self.env.user.id != matrix_line_id.last_approved.id:
                        record.is_approve_button = True
                        record.approval_matrix_line_id = matrix_line_id.id
                    else:
                        record.is_approve_button = False
                        record.approval_matrix_line_id = False
                else:
                    record.is_approve_button = False
                    record.approval_matrix_line_id = False
            else:
                record.approval_matrix_line_id = False
                record.is_approve_button = False

    @api.depends('destination_location')
    def _get_approving_matrix(self):
        for rec in self:
            if rec.destination_location:
                picking_type = self.env['stock.picking.type'].search([('default_location_dest_id','=',rec.destination_location.id),('code', '=', 'incoming')],limit=1)
                # approval_matrix = self.env['mr.approval.matrix'].search([('location_ids', 'in', rec.destination_location.location_id.ids)], limit=1)
                approval_matrix = self.env['mr.approval.matrix'].search(['|',('location_ids', 'in', rec.destination_location.location_id.ids),('location_ids', 'in', rec.destination_location.ids)], limit=1)         
                rec.picking_type =  picking_type.id or False
                rec.approving_matrix_id = approval_matrix.id or False
    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('std.material.request') or '/'
        vals['request_reference'] = seq
        vals['name'] = seq
        res = super(StdMaterialRequest, self).create(vals)
        # if 'expire_date' in vals:
        #     date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        #     if res.expire_date < date and res.status not in ('rejected', 'approved'):
        #         res.with_context({'show_expired': True}).write({'status': 'rejected'})
        return res

    @api.multi
    def internal_transfer_receipt(self):
        context = self.env.context.copy()
        pr_line = []
        for line in self.product_line:
            vals = {
                'mr_id': self.id,
                'product_id': line.product.id,
                'description': line.product.name_get()[0][1],
                'uom_id': line.product.uom_id.id,
                'qty_transfer': line.quantity,
            }
            pr_line.append((0, 0, vals))
        context.update({
            'default_warehouse_id': self.approving_matrix_id.warehouse_id.id,
            'default_internal_transfer_receipt': pr_line,
            'partner_id': self.requested_by.id,
            'schedule_date': self.schedule_date,
            # 'source_loc_id': self.approving_matrix_id.warehouse_id.id,
            'dest_loc_id': self.destination_location.id,
            'origin': self.request_reference
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Internal Transfer',
            'res_model': 'mr.internal.transfer',
            'view_id': self.env.ref('std_material_request.internal_transfer_form_view').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    @api.multi
    def action_draft(self):
        for record in self:
            record.write({'status': 'draft'})
            record.approving_matrix_line_ids.write({'approve_state': 'draft'})

    @api.one
    def _get_current_approvers(self):
        approver_data ={}
        for approver in self.approving_matrix_id.product:
            if approver.sequence not in approver_data:
                approver_data[approver.sequence]=[approver.approver.id]
            else:
                approver_data[approver.sequence].append(approver.approver.id)
                
        current_approver_user_ids = []                    
        for approver_seq in sorted(approver_data):
            approver_ids = approver_data[approver_seq]
            if not self.approving_matrix_line_ids.filtered(lambda r: r.approver.id in approver_ids and r.approved):
                current_approver_user_ids = approver_ids
                break
        else:
            self.status = 'approved'
        self.current_approver_ids = [(6,0,current_approver_user_ids)]        

    @api.multi
    def approve(self):
        for record in self:
            if record.is_approve_button and record.approval_matrix_line_id:
                send_mail = False
                approval_matrix_line_id = record.approving_matrix_line_ids.filtered(lambda r: r.id == record.approval_matrix_line_id.id)
                if approval_matrix_line_id.minimal_approver == len(approval_matrix_line_id.approver):
                    approval_matrix_line_id.write({'approved_count': approval_matrix_line_id.approved_count + 1, 'last_approved': self.env.user.id})
                    if approval_matrix_line_id.minimal_approver == approval_matrix_line_id.approved_count:
                        approval_matrix_line_id.write({'approve_state': 'approved', 'time_stamp': datetime.now()})
                        record.message_post(
                            tracking_value_ids=[(0, 0, {'field': 'status', 'old_value_char': 'Waiting For Approval', 
                            'new_value_char': 'Approved', 'field_desc': u'Status', 'field_type': 'selection'})], 
                            author_id=self.env.user.id)
                        send_mail = True
                else:
                    approval_matrix_line_id.write({'approve_state': 'approved', 'time_stamp': datetime.now()})
                    send_mail = True
            if len(record.approving_matrix_line_ids) == len(record.approving_matrix_line_ids.filtered(lambda r:r.approve_state == 'approved')):
                record.write({'date': datetime.now(), 'status': 'approved'})

    @api.multi
    def request_approval(self):
        for record in self:
            record.status = 'to_approve'
            record.approving_matrix_line_ids.write({'approve_state': 'to_approve', 'time_stamp': datetime.now()})

    @api.multi
    def reject(self):
        for obj in self:
            obj.status = 'rejected'
            obj.approving_matrix_line_ids.write({'approve_state': 'rejected', 'time_stamp': datetime.now()})

#     @api.multi
#     def reset(self):
#         for obj in self:
#             obj.status = 'draft'

    @api.multi
    def create_purchase_request(self):
        context = self.env.context.copy()
        pr_line = []
        for line in self.product_line:
            vals = {
                'mr_id': self.id,
                'product_id' : line.product.id,
                'description' : line.product.name_get()[0][1],
                'uom_id' : line.product.uom_id.id,
                'qty_purchase' : line.quantity, 
                'request_date' : line.request_date,
            }
            pr_line.append((0,0, vals))
        context.update({
            'default_pr_wizard_line': pr_line,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Purchase Request',
            'res_model': 'std.purchase.request.wizard',
            'view_id' : self.env.ref('std_material_request.purchase_request_wizard_form_view').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context' : context,
        }

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations  and self.env.context.get('transfer_menu'):
            domain.extend(['&',('destination_location', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids),('create_uid', '=', user.id)])
        return super(StdMaterialRequest, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations  and self.env.context.get('transfer_menu'):
            domain.extend(['&',('destination_location', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids),('create_uid', '=', user.id)])
        return super(StdMaterialRequest, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)


class StdItemMR(models.Model):
    _name = 'std.item.mr'

    std_mr = fields.Many2one('std.material.request')
    product = fields.Many2one('product.product',string="Product")
    descript = fields.Text(string="Description",)
    destination_location_id = fields.Many2one('stock.location', required=True ,string='Destination Location')
    destination_location_ids = fields.Many2many('stock.location', string='Location', compute='_get_destination_location', store=False)
    # brand_id = fields.Many2one('brand.brand', string='Brand')
    quantity = fields.Float(string="Quantity",default=1)
    product_unit_measure = fields.Many2one('product.uom',"Purchase Unit of Measure")
    request_date = fields.Date(string ="Request Date", required=True, default=datetime.today())
    procurement_order = fields.Many2one('procurement.order', string="Procurement Order")
    # unit = fields.Many2one('product.uom',string="Unit(s)")
    text = fields.Text()
    picking_type = fields.Many2one('stock.picking.type' , string="Picking Type", compute='_get_picking_type', store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To be Approved'),
        ('approved', 'Approved'),
        ('Rejected', 'Rejected')],
        related="std_mr.status")
    std_item_mr_lines = fields.One2many('std.item.mr.lines', 'std_item_mr', string='Details')

    @api.depends('destination_location_id')
    def _get_picking_type(self):
        for rec in self:
            if rec.destination_location_id:
                picking_type = self.env['stock.picking.type'].search([('default_location_dest_id','=',rec.destination_location_id.id),('code', '=', 'incoming')], limit=1)
                rec.picking_type =  picking_type.id or False
            else:
                rec.picking_type = False

    @api.depends('status')
    def _get_destination_location(self):
        for record in self:
            if record.std_mr.destination_location:
                user = self.env.user
                location_ids = self.env['stock.location'].search([
                    ('location_id', 'child_of', record.std_mr.destination_location.id), 
                    ('usage', '=', 'internal'), 
                    # ('id', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids)
                    ])
                record.destination_location_ids = [(6, 0, location_ids.ids)]
            else:
                record.destination_location_ids = [(6, 0, [])]

    @api.onchange('product')
    def onchange_product(self):
        if self.product:
            self.descript = self.product.name_get()[0][1] or ''
            self.product_unit_measure = self.product.uom_id.id

    @api.onchange('std_mr')
    def onchange_dest_loc_id(self):
        if self.std_mr:
            self.destination_location_id = self.std_mr.destination_location.id


    @api.multi
    def show_stock(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock balance by location',
            'res_model': 'product.product',
            'res_id' : self.product.id,
            'view_id' : self.env.ref('std_material_request.stock_by_product_form_view').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def show_details(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Show Details',
            'res_model': 'std.item.mr',
            'res_id' : self.id,
            'view_id' : self.env.ref('std_material_request.std_item_mr_details_form_view').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations  and self.env.context.get('transfer_menu'):
            domain.extend([('destination_location_id', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids),('create_uid', '=', user.id)])
        return super(StdItemMR, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        user = self.env.user
        domain = domain or []
        if not user.is_admin and user.restrict_locations  and self.env.context.get('transfer_menu'):
            domain.extend([('destination_location_id', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids),('create_uid', '=', user.id)])
        return super(StdItemMR, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    # @api.model
    # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
    #     user = self.env.user
    #     domain = domain or []
    #     if not user.is_admin or user.restrict_locations:
    #         domain.extend([('destination_location_id', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids)])
    #     return super(StdItemMR, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    # @api.model
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     user = self.env.user
    #     domain = domain or []
    #     if not user.is_admin or user.restrict_locations:
    #         domain.extend([('destination_location_id', 'in', user.warehouse_location_operation_ids.mapped('location_ids').ids)])
    #     return super(StdItemMR, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)


class StdItemMRLines(models.Model):
    _name = 'std.item.mr.lines'

    product_id = fields.Many2one('product.product',string="Product")
    state_intt = fields.Selection([('sent', 'Sent'), ('cancel', 'Cancelled'), ('return', 'Returned')], string='Internal Transfer State')
    cancel_reason = fields.Text(string='Cancelled Reason')
    remain_product = fields.Float(string='Quantity Product')
    destination_location_id = fields.Many2one('stock.location', string='Destination location')
    internal_transfer_ref = fields.Many2one('internal.transfer', string='Internal transfer reference')
    purchase_request_ref = fields.Many2one('purchase.request', string='Purchase request reference')
    internal_transfer_qty = fields.Float(string='Internal transfer qty')
    purchase_request_qty = fields.Float(string='Purchase request qty')
    internal_transfer_date = fields.Date(string='Internal transfer date')
    purchase_request_date = fields.Date(string='Purchase request date')
    std_item_mr = fields.Many2one('std.item.mr')
    is_return = fields.Boolean(string='return')

    @api.multi
    def not_return(self):
        for record in self:
            record.is_return = True


    @api.multi
    def return_mr(self):
        for record in self:
            if record.std_item_mr.std_mr.status == 'done':
                record.std_item_mr.std_mr.status = 'confirm'
            record.write({'state_intt': 'return'})
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

class StdMRApprovalMatrixLine(models.Model):
    _name = 'std.mr.approval.matrix.line'
    _order = 'sequence'

    name = fields.Char('Approver')
    sequence = fields.Char(string="Sequence")
    approver = fields.Many2many('res.users', string="Approver", required=True)
    matrix_id = fields.Many2one('mr.approval.matrix', string="Matrix")
    approved = fields.Boolean('Approved')
    material_request_id = fields.Many2one('std.material.request')
    approve_state = fields.Selection([
        ('draft', ''),
        ('to_approve', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'), 
        ('cancel', '-')
        ],
        default="draft", string='Approval Status')
    time_stamp = fields.Datetime(string='TimeStamp')
    minimal_approver = fields.Float('Minimum Approver', default=1)
    last_approved = fields.Many2one('res.users', string='Users')
    approved_count = fields.Integer(string='Approved Count', default=0)
    is_approved = fields.Boolean(string='Is Approved')

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        if vals.get('model') and \
            vals.get('model') == 'std.material.request' and vals.get('tracking_value_ids'):
            vals['tracking_value_ids'] = [rec for rec in vals.get('tracking_value_ids') if 
                                        rec[2].get('field') not in ('status_1', 'status_2', 'approval_state')]
        return super(MailMessage, self).create(vals)
