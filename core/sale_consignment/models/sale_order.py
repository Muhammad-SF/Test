# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv import  osv
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.one
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.partner_id.is_consignment:
            commission_ids_lst = []
            for line in self.order_line:
                vals = {
                    'name':line.name,
                    'product_id':line.product_id and line.product_id.id or False,
                    'price_unit':line.price_unit,
                    'quantity':line.product_uom_qty
                }
                line_id = self.env['commission.lines'].create(vals)
                commission_ids_lst.append(line_id.id)
            commission_id = self.env['commission.commission'].create({
                'partner_id':self.partner_id.id, 
                'sale_order':self.id,
                'currency_id': self.currency_id.id,
                'commission_lines':[(6,0,commission_ids_lst)]
            })
            invoice_ids = commission_id.action_invoice_create()
            self.write({'supplier_invoice': invoice_ids and invoice_ids[0] or False})
            self.env['force.done'].order_shipped(self.id)
            # self.env['force.done'].invoice_paid(invoice_ids[0])
        return res

    @api.multi
    def action_view_commission(self):
        commission_ids = self.env['commission.commission'].search([('sale_order','=',self.id)])
        if commission_ids:
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('sale_consignment.wk_commission_action')
            form_view_id = imd.xmlid_to_res_id('sale_consignment.commission_from_view')
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[False, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
            }
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = commission_ids and commission_ids.id or False
            return result
        else:
            raise osv.except_osv(_('Warning'),("Order has no related commission record!"))

    @api.multi
    def action_view_commission_invoice(self):
        if self.supplier_invoice:
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('account.action_invoice_tree2')
            form_view_id = imd.xmlid_to_res_id('account.invoice_supplier_form')
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[False, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
                'target': action.target,
                'context': action.context,
                'res_model': action.res_model,
            }

            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = self.supplier_invoice.id
            return result
        else:
            raise osv.except_osv(_('Warning'),("Order has no related commission record!"))


    @api.depends('amount_total','order_line.price_subtotal')
    def _compute_commission_total(self):
        for record in self:
            consignment = 0.0
            if record.partner_id and record.partner_id.is_consignment:
                amount = 0.0
                for line in record.order_line:
                    amount+=line.price_subtotal
                consignment = float(amount*record.partner_id.consignment_percent)/100.0
            record.commission_total = consignment

    commission_total = fields.Float(string="Commission", compute="_compute_commission_total", store=True)
    supplier_invoice = fields.Many2one('account.invoice',string='Invoice')
    is_consignment = fields.Boolean(string='Is Consignment')

class commission_commission(models.Model):
    _name = "commission.commission"
    _description = "Commission"

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('commission.commission') or 'New'
        return super(commission_commission, self).create(vals)
    
    @api.one
    @api.depends('commission_lines')
    def get_total_amount(self):
        total = 0.0
        for line in self.commission_lines:
            total += line.price_subtotal
        self.amount_total = total
    
    name = fields.Char(string='Reference', copy=False, index=True)
    partner_id = fields.Many2one("res.partner", string="Partner Name")
    sale_order = fields.Many2one("sale.order", string="Sale Order Reference")
    commission_lines = fields.One2many("commission.lines", "commission_id")
    commission = fields.Float(related="partner_id.consignment_percent", string="Partner Commission")
    amount_total = fields.Float(compute=get_total_amount, string="Total", store=True)
    currency_id = fields.Many2one("res.currency", string="Currency")

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journals = self.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', self.sale_order.company_id.id)])
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.sale_order.client_order_ref or '',
            'origin': self.sale_order.name,
            'type': 'in_invoice',
            'reference': self.sale_order.client_order_ref or self.name,
            'account_id': self.sale_order.partner_invoice_id.property_account_payable_id.id,
            'partner_id': self.sale_order.partner_invoice_id.id,
            'journal_id': journals[0].id,
            'currency_id': self.sale_order.pricelist_id.currency_id.id,
            'payment_term_id': self.sale_order.payment_term_id.id,
            'fiscal_position_id': self.sale_order.fiscal_position_id.id or self.sale_order.partner_invoice_id.property_account_position_id.id,
            'company_id': self.sale_order.company_id.id,
            'user_id': self.sale_order.user_id and self.sale_order.user_id.id,
            'date_invoice': datetime.now().strftime('%Y-%m-%d'),
            
        }
        return invoice_vals

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        for commission in self:
            group_key = commission.id if grouped else (commission.sale_order.partner_id.id, commission.sale_order.currency_id.id)
            for line in commission.commission_lines.sorted(key=lambda l: l.quantity < 0):
                if float_is_zero(line.quantity, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = commission._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    invoices[group_key] = invoice
                elif group_key in invoices and commission.name not in invoices[group_key].origin.split(', '):
                    invoices[group_key].write({'origin': invoices[group_key].origin + ', ' + commission.name})
                if line.quantity > 0:
                    line.invoice_line_create(invoices[group_key].id, line.quantity)
        # for inv in invoices.values():
        #     inv.signal_workflow('invoice_open')
        return [inv.id for inv in invoices.values()]

class commission_lines(models.Model):
    _name = "commission.lines"
    _description = "Commission Lines"

    @api.one
    @api.depends('quantity','price_unit','commission_id.commission')
    def _amount_line(self):
        total = self.price_unit*self.quantity
        self.price_subtotal = (total*self.commission_id.commission)/100

    commission_id = fields.Many2one("commission.commission", string="Commission ID")
    name = fields.Char(string="Description", required=True)
    product_id = fields.Many2one("product.product", string="Product")
    price_unit = fields.Float(string="Unit Price", required=True )
    price_subtotal = fields.Float(compute=_amount_line, string='Commission Amount', digits_compute= dp.get_precision('Account'))
    quantity = fields.Float(string="Quantity", required=True)


    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_expense_id or self.product_id.categ_id.property_account_expense_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                            (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.commission_id.sale_order.fiscal_position_id or self.commission_id.sale_order.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'origin': self.commission_id.name,
            'account_id': account.id,
            'price_unit': self.price_subtotal,
            'quantity': 1.0,
            'product_id': self.product_id and self.product_id.id or False,
            'account_analytic_id': self.commission_id.sale_order.project_id and self.commission_id.sale_order.project_id.id or False,
        }
        return res

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'commission_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)