# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
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
from openerp import models, fields, exceptions, api, _
import openerp.addons.decimal_precision as dp
import product
from openerp.tools.float_utils import float_is_zero, float_compare
from openerp.exceptions import Warning,UserError
import datetime

#class stock_transfer_details(models.TransientModel):
#    _inherit = 'stock.transfer_details'
#
#    @api.one
#    def do_detailed_transfer(self):
#        res = super(stock_transfer_details, self).do_detailed_transfer()
#        if self._context.get('active_id'):
#            picking_obj = self.env['stock.picking'].browse(self._context.get('active_id'))
#            if picking_obj.origin:
#                landed_cost_id = self.env['stock.landed.cost'].search([('picking_ids','in',picking_obj.id)])
#                res1 = landed_cost_id.compute_landed_cost()
#                result = landed_cost_id.button_validate()
#        return res   
#
#
class stock_landed_cost_lines(models.Model):
    _name = "custom.stock.landed.cost.lines"

    name = fields.Char('Description')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    invoice = fields.Many2one('account.invoice', 'Invoice')
    price_unit = fields.Float('Cost', required=True, digits_compute=dp.get_precision('Product Price'))
    split_method = fields.Selection(product.SPLIT_METHOD, string='Split Method', required=True)
    account_id = fields.Many2one('account.account', 'Account', domain=[('type', '<>', 'view'), ('type', '<>', 'closed')])
#
    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return {'value': {'quantity': 0.0, 'price_unit': 0.0}}

        product = self.product_id
        self.name = product.name
        self.split_method = product.split_method
        self.price_unit = product.standard_price
        self.account_id = product.property_account_expense_id and product.property_account_expense_id.id or product.categ_id.property_account_expense_categ_id.id

class container_number_bi(models.Model):
    _name = "container.number.bi"

    name = fields.Integer('Container Number')
    invoice_id = fields.Many2one('account.invoice','Invoice')
    picking_id = fields.Many2one('stock.picking','Picking')


class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    bi_landed_cost = fields.One2many('custom.stock.landed.cost.lines', 'invoice', string="Invoice")
    bi_acount_journal_id = fields.Many2one('account.journal', 'Landed Cost Journal')
    bi_container_number = fields.One2many('container.number.bi', 'invoice_id', string="Container Number")
#
    @api.multi
    def invoice_validate(self):
        super(account_invoice, self).invoice_validate()
        po = self.env['purchase.order'].search([('name','=',self.origin)])
        print "=====================po",po
        res = po.with_context(custom=True,invoice=self.id)._create_picking()
        if self.bi_container_number:
            for a in self.bi_container_number:
                a.picking_id = res.id
        if self.bi_landed_cost:
            if not self.bi_acount_journal_id:
                raise Warning("Enter Landed Cost Journal Value")
            new_cost_id = self.env['stock.landed.cost'].create({
                                                  'date':datetime.datetime.today().date(),
                                                  'picking_ids':[(6,0,[res.id])],
                                                  'account_journal_id':self.bi_acount_journal_id.id,
                                                  
                                                })
            for record in self.bi_landed_cost:
                result = self.env['stock.landed.cost.lines'].create({
                                                'name':record.name,
                                                'product_id':record.product_id.id,
                                                'price_unit':record.price_unit,
                                                'split_method':record.split_method,
                                                'account_id':record.account_id.id,
                                                'cost_id':new_cost_id.id
                                                })
            po.landed_cost_id = [(4,new_cost_id.id)]
        return True
#        
class stock_picking(models.Model):
    _inherit = "stock.picking"

    bi_container_number = fields.One2many('container.number.bi', 'picking_id', string="Container Number")

    @api.multi
    def do_new_transfer(self):
        res = super(stock_picking, self).do_new_transfer()
        if self.origin:
            landed_cost_id = self.env['stock.landed.cost'].search([('picking_ids','in',self.id)])
            print "===========landed_cost_id===========",landed_cost_id
            res1 = landed_cost_id.compute_landed_cost()
            print "===========res1======",res1
            result = landed_cost_id.button_validate()
        return res   





class purchase_order(models.Model):
    _inherit = "purchase.order"

    landed_cost_id = fields.Many2many('stock.landed.cost', string="Landed cost")

    @api.multi
    def button_approve(self, force=False):
        if self.company_id.po_double_validation == 'two_step'\
          and self.amount_total >= self.env.user.company_id.currency_id.compute(self.company_id.po_double_validation_amount, self.currency_id)\
          and not self.user_has_groups('purchase.group_purchase_manager'):
            raise UserError(_('You need purchase manager access rights to validate an order above %.2f %s.') % (self.company_id.po_double_validation_amount, self.company_id.currency_id.name))
        self.write({'state': 'purchase'})
        if self.company_id.po_lock == 'lock':
            self.write({'state': 'done'})
        return {}


    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        picking = True
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done','cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                moves = moves.action_confirm()
                moves.force_assign()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
                if self._context.get('invoice'):
                    return picking
        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _create_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._create_stock_moves(picking)
        invoice_brw = self.env['account.invoice'].browse(self._context.get('invoice'))
        for moves in res:
            for lines in invoice_brw.invoice_line_ids:
                if lines.product_id.id == moves.product_id.id:
                    moves.product_uom_qty = lines.quantity
        return res
            
#
#    @api.multi
#    def action_picking_create(self):
#        if self._context.get('custom'):
#            for order in self:
#                picking_vals = {
#                    'picking_type_id': order.picking_type_id.id,
#                    'partner_id': order.partner_id.id,
#                    'date': order.date_order,
#                    'origin': order.name
#                }
#                picking_id = self.env['stock.picking'].create(picking_vals)
#                self._create_stock_moves(order, order.order_line, picking_id.id)
#            return picking_id
#
#        return True
#
#    @api.v7
#    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, group_id, context=None):
#        result = []
#        res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, group_id, context)
#        if context.get('invoice'):
#            invoie_brw = self.pool.get('account.invoice').browse(cr,uid,context.get('invoice'),context=None)
#            for line in invoie_brw.invoice_line:
#                if line.product_id.id == res[0].get('product_id'):
#                    result.append(res[0])
#                    result[0].update({'product_uom_qty':line.quantity,
#                                'product_uos_qty':line.quantity})
#        return result
#                            
