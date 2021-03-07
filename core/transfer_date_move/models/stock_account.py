from odoo import fields, models, exceptions, api,_
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
import logging
from odoo.tools.float_utils import float_compare, float_round
from datetime import datetime
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
     
    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return
 
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)
 
        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
 
        if not seller:
            return
        price_unit = self.env['account.tax']._fix_tax_included_price(seller.price, self.product_id.supplier_taxes_id, self.taxes_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.with_context(date=self.order_id.date_order).currency_id.compute(price_unit, self.order_id.currency_id)
        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)
        self.price_unit = price_unit
        
    @api.multi
    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0)['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.with_context(date=order.date_order).currency_id.compute(price_unit, order.company_id.currency_id, round=False)
        return price_unit

class StockMove(models.Model):
    _inherit = 'stock.move'
 
    def _prepare_account_move_line_new(self, move, qty, cost, credit_account_id, debit_account_id):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()
  
        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            if self.product_id.cost_method == 'average':
                valuation_amount = cost if self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'internal' else self.product_id.standard_price
            else:
                valuation_amount = cost if self.product_id.cost_method == 'real' else self.product_id.standard_price
        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount * qty)
  
        # check that all data is correct
        if self.company_id.currency_id.is_zero(debit_value):
            if self.product_id.cost_method == 'standard':
                raise UserError(_("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (self.product_id.name,))
            return []
        credit_value = debit_value
  
        if self.product_id.cost_method == 'average' and self.company_id.anglo_saxon_accounting:
            if self.location_dest_id.usage == 'supplier' and self.origin_returned_move_id and self.origin_returned_move_id.purchase_line_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
            if self.location_id.usage == 'customer' and self.origin_returned_move_id:
                debit_value = self.origin_returned_move_id.price_unit * qty
                credit_value = debit_value
        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        currency_rate = move.picking_id.po_request_id.with_context(date=move.picking_id.po_request_id.date_order).currency_id.rate
        if move.picking_id.po_request_id.with_context(date=move.picking_id.min_date).currency_id.rate:
            picking_currency_rate = move.picking_id.po_request_id.with_context(date=move.picking_id.min_date).currency_id.rate
        else:
            picking_currency_rate = 1.0
        analytic_account_id = False
        analytic_tag_ids = []
        if move.picking_id.origin:
            sale_id = self.env['sale.order'].search([('name','=',move.picking_id.origin)])
            if sale_id:
                analytic_account_id = sale_id[0].order_line[0].account_analytic_id.id if sale_id[0].order_line and sale_id[0].order_line[0].account_analytic_id else False
                analytic_tag_ids = sale_id[0].order_line[0].analytic_tag_ids.ids if sale_id[0].order_line and sale_id[0].order_line[0].analytic_tag_ids else False
        if self.product_id.uom_id != self.product_id.uom_po_id:
            if self.product_id.uom_id.uom_type == 'reference':
                if self.product_id.uom_po_id.uom_type == 'bigger':
                    qty = qty / self.product_id.uom_po_id.factor_inv
                if self.product_id.uom_po_id.uom_type == 'smaller':
                    qty = qty * self.product_id.uom_po_id.factor_inv
            if self.product_id.uom_id.uom_type == 'bigger':
                qty = qty / self.product_id.uom_id.factor_inv
                if self.product_id.uom_po_id.uom_type == 'bigger':
                    qty = qty / self.product_id.uom_po_id.factor_inv
                if self.product_id.uom_po_id.uom_type == 'smaller':
                    qty = qty * self.product_id.uom_po_id.factor_inv
            if self.product_id.uom_id.uom_type == 'smaller':
                qty = qty * self.product_id.uom_id.factor_inv
                if self.product_id.uom_po_id.uom_type == 'bigger':
                    qty = qty / self.product_id.uom_po_id.factor_inv
                if self.product_id.uom_po_id.uom_type == 'smaller':
                    qty = qty * self.product_id.uom_po_id.factor_inv
        debit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'partner_id': partner_id,
            'currency_id':move.picking_id.po_request_id.currency_id.id,
            'amount_currency': round((debit_value*currency_rate),2) if debit_value > 0 else -debit_value,
            'debit': round(((debit_value*currency_rate)/picking_currency_rate),2) if debit_value > 0 else 0,
            'credit': -round(((debit_value*currency_rate)/picking_currency_rate),2) if debit_value < 0 else 0,
            'account_id': debit_account_id,
            'analytic_account_id': analytic_account_id,
            'analytic_tag_ids': [(6,0, analytic_tag_ids)],
        }
        credit_line_vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': self.picking_id.name,
            'currency_id':move.picking_id.po_request_id.currency_id.id,
            'partner_id': partner_id,
            'amount_currency': -round((credit_value*currency_rate),2) if credit_value > 0 else credit_value,
            'credit': round(((credit_value*currency_rate)/picking_currency_rate),2) if credit_value > 0 else 0,
            'debit': -round(((credit_value*currency_rate)/picking_currency_rate),2) if credit_value < 0 else 0,
            'account_id': credit_account_id,
            'analytic_account_id': analytic_account_id,
            'analytic_tag_ids': [(6,0, analytic_tag_ids)],
        }
        res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference
            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
            price_diff_line = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': self.picking_id.name,
                'currency_id':move.picking_id.po_request_id.currency_id.id,
                'partner_id': partner_id,
                'amount_currency': diff_amount > 0 and diff_amount or -diff_amount,
                'credit': diff_amount > 0 and (diff_amount/currency_rate) or 0,
                'debit': diff_amount < 0 and -(diff_amount/currency_rate) or 0,
                'account_id': price_diff_account.id,
                'analytic_account_id': analytic_account_id,
                'analytic_tag_ids': [(6,0, analytic_tag_ids)],
            }
            res.append((0, 0, price_diff_line))
        return res
    
class stock_quant(models.Model):
    _inherit = "stock.quant"
    
    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        quant_cost_qty = defaultdict(lambda: 0.0)
        serial_cost_qty = []
        for quant in self:
            if move.inventory_id.new_price:
                for inv_line in move.inventory_id.line_ids:
                    if inv_line.prod_lot_id and quant.lot_id:
                        line = inv_line.search([('product_id', '=', move.product_id.id), ('id', '=', inv_line.id),('prod_lot_id','=',quant.lot_id.id or False)])
                        if line:
                            serial_cost_qty.append({line.unit_price:quant.qty})
                    else:
                        invetory_line = inv_line.search([('product_id', '=', move.product_id.id), ('id', '=', inv_line.id)])
                        if invetory_line.unit_price:
                            quant_cost_qty[invetory_line.unit_price] += quant.qty
            else:
                quant_cost_qty[quant.cost] += quant.qty
        alternate_journal_id = self.env['account.journal'].search([('type', '=', 'cash')], limit=1)
        if journal_id:
            journal_id = journal_id
        else:
            journal_id = alternate_journal_id.id

        inventory_id = False
        if self._context.get('create_from_inventory_adjustment',False):
            inventory_id = self.env['stock.inventory'].browse(self._context.get('inv_adjustment_ids', False))
            if inventory_id.journal_id:
                journal_id = inventory_id.journal_id.id

        if move.picking_id.sale_id or move.picking_id.is_delivery or self._context.get('create_from_inventory_adjustment',False):
            AccountMove = self.env['account.move']
            for cost, qty in quant_cost_qty.iteritems():
                move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
                if move_lines:
                    if inventory_id:
                        if inventory_id.force_accounting_date:
                            date = inventory_id.force_accounting_date
                        else:
                            date = self._context.get('force_period_date', fields.Date.context_today(self))
                    else:
                        if move.picking_id and move.picking_id.min_date:
                            date = move.picking_id.min_date
                        else:
                            date = self._context.get('force_period_date', fields.Date.context_today(self))
                    new_account_move = AccountMove.create({
                        'journal_id': journal_id,
                        'line_ids': move_lines,
                        'date': date,
                        'branch_id': move.branch_id.id,
                        'ref': move.picking_id.name})
                    new_account_move.post()
            if self._context.get('create_from_inventory_adjustment',False):
                for dict_cost_qty in serial_cost_qty:
                    for cost,qty in dict_cost_qty.iteritems():
                        move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
                        if move_lines:
                            if inventory_id:
                                date = inventory_id.force_accounting_date
                            else:
                                date = self._context.get('force_period_date', fields.Date.context_today(self))
                            new_account_move = AccountMove.create({
                                'journal_id': journal_id,
                                'line_ids': move_lines,
                                'date': date,
                                'branch_id': move.branch_id.id,
                                'ref': move.picking_id.name})
                            new_account_move.post()

stock_quant()