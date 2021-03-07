# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class SaleRequisitionType(models.Model):
    _name = "sale.requisition.type"
    _description = "Sale Agreement Type"
    _order = "sequence"

    name = fields.Char(string='Agreement Type', required=True, translate=True)
    sequence = fields.Integer(default=1)
    exclusive = fields.Selection([
        ('exclusive', 'Select only one Quotation (exclusive)'), ('multiple', 'Select multiple Quotation')],
        string='Agreement Selection Type', required=True, default='multiple',
            help="""Select only one Quotation (exclusive):  when a sale order is confirmed, cancel the remaining sale order.\n
                    Select multiple Quotation: allows multiple sale orders. On confirmation of a sale order it does not cancel the remaining orders""")
    quantity_copy = fields.Selection([
        ('copy', 'Use quantities of agreement'), ('none', 'Set quantities manually')],
        string='Quantities', required=True, default='none')
    line_copy = fields.Selection([
        ('copy', 'Use lines of agreement'), ('none', 'Do not create Quotation lines automatically')],
        string='Lines', required=True, default='copy')

class SaleRequisition(models.Model):
    _name = "sale.requisition"
    _description = "Sale Requisition"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "id desc"

    def _get_picking_in(self):
        return self.env.ref('stock.picking_type_in')

    def _get_type_id(self):
        return self.env['sale.requisition.type'].search([], limit=1)

    name = fields.Char(string='Agreement Reference', required=True, copy=False, default= lambda self: self.env['ir.sequence'].next_by_code('sale.order.requisition'))
    origin = fields.Char(string='Source Document')
    order_count = fields.Integer(compute='_compute_orders_number', string='Number of Orders')
    partner_id = fields.Many2one('res.partner', string="Customer")
    type_id = fields.Many2one('sale.requisition.type', string="Agreement Type", required=True, default=_get_type_id)
    ordering_date = fields.Date(string="Ordering Date")
    date_end = fields.Datetime(string='Agreement Deadline')
    schedule_date = fields.Date(string='Delivery Date', index=True, help="The expected and scheduled delivery date where all the products are received")
    user_id = fields.Many2one('res.users', string='Responsible', default= lambda self: self.env.user)
    description = fields.Text()
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env['res.company']._company_default_get('sale.requisition'))
    sale_ids = fields.One2many('sale.order', 'requisition_id', string='Sale Orders', states={'done': [('readonly', True)]})
    line_ids = fields.One2many('sale.requisition.line', 'requisition_id', string='Products to Sale', states={'done': [('readonly', True)]}, copy=True)
    procurement_id = fields.Many2one('procurement.order', string='Procurement', ondelete='set null', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'Confirmed'),
                               ('open', 'Bid Selection'), ('done', 'Done'),
                               ('cancel', 'Cancelled')],
                              'Status', track_visibility='onchange', required=True,
                              copy=False, default='draft')
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True, default=_get_picking_in)
    amount_total = fields.Float(compute="_compute_amount_total", string="Total", digits=dp.get_precision('Product Price'))
    
    @api.multi
    @api.depends('line_ids')
    def _compute_amount_total(self):
        for sale in self:
            total = 0.0
            for line in self.line_ids:
                total += line.sub_total
            sale.amount_total = total

    @api.multi
    @api.depends('sale_ids')
    def _compute_orders_number(self):
        for requisition in self:
            requisition.order_count = len(requisition.sale_ids)

    @api.multi
    def action_cancel(self):
        # try to set all associated quotations to cancel state
        for requisition in self:
            requisition.sale_ids.action_cancel()
            for so in requisition.sale_ids:
                so.message_post(body=_('Cancelled by the agreement associated to this quotation.'))
        self.write({'state': 'cancel'})

    @api.multi
    def action_in_progress(self):
        if not all(obj.line_ids for obj in self):
            raise UserError(_('You cannot confirm call because there is no product line.'))
        self.write({'state': 'in_progress'})

    @api.multi
    def action_open(self):
        self.write({'state': 'open'})

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_done(self):
        """
        Generate all sale order based on selected lines, should only be called on one agreement at a time
        """
        if any(sale_order.state in ['draft', 'sent', 'to approve'] for sale_order in self.mapped('sale_ids')):
            raise UserError(_('You have to cancel or validate every Quotation before closing the sale requisition.'))
        self.write({'state': 'done'})

class SaleRequisitionLine(models.Model):
    _name = "sale.requisition.line"
    _description = "Sale Requisition Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], required=True)
    product_uom_id = fields.Many2one('product.uom', string='Product Unit of Measure')
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
    price_unit = fields.Float(string='Unit Price', digits=dp.get_precision('Product Price'))
    qty_ordered = fields.Float(compute='_compute_ordered_qty', string='Ordered Quantities')
    delivered_qty = fields.Float(string='Delivered Quantities')
    requisition_id = fields.Many2one('sale.requisition', string='Sale Agreement', ondelete='cascade')
    company_id = fields.Many2one('res.company', related='requisition_id.company_id', string='Company', store=True, readonly=True, default= lambda self: self.env['res.company']._company_default_get('sale.requisition.line'))
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    schedule_date = fields.Date(string='Scheduled Date')
    sub_total = fields.Float(compute="_compute_sub_total", string="Sub Total", digits=dp.get_precision('Product Price'))

    @api.multi
    @api.depends('requisition_id.sale_ids.state')
    def _compute_ordered_qty(self):
        for line in self:
            total = 0.0
            for po in line.requisition_id.sale_ids.filtered(lambda sale_order: sale_order.state in ['sale', 'done']):
                for po_line in po.order_line.filtered(lambda order_line: order_line.product_id == line.product_id):
                    if po_line.product_uom != line.product_uom_id:
                        total += po_line.product_uom._compute_quantity(po_line.product_uom_qty, line.product_uom_id)
                    else:
                        total += po_line.product_uom_qty
            line.qty_ordered = total

    @api.multi
    @api.depends('price_unit','product_uom_qty')
    def _compute_sub_total(self):
        for line in self:
            line.sub_total = line.product_uom_qty * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.product_uom_qty = 1.0
            self.price_unit = self.product_id.list_price
        if not self.account_analytic_id:
            self.account_analytic_id = self.requisition_id.account_analytic_id
        if not self.schedule_date:
            self.schedule_date = self.requisition_id.schedule_date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    requisition_id = fields.Many2one('sale.requisition', string='Sale Agreement', copy=False)

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.partner_id
        payment_term = partner.property_payment_term_id
        currency = requisition.company_id.currency_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id,
        self.company_id = requisition.company_id.id
        self.currency_id = currency.id
        self.origin = requisition.name
        self.partner_ref = requisition.name # to control vendor bill based on agreement reference
        self.notes = requisition.description
        self.date_order = requisition.date_end or fields.Datetime.now()
        self.picking_type_id = requisition.picking_type_id.id
        self.pricelist_id = self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        self.partner_invoice_id = addr['invoice'],
        self.partner_shipping_id = addr['delivery'],
        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_sale:
                name += '\n' + product_lang.description_sale

            # Compute taxes
            if fpos:
                taxes_ids = fpos.map_tax(line.product_id.taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id))
            else:
                taxes_ids = line.product_id.taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_id:
                product_uom_qty = line.product_uom_id._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_id)
            else:
                product_uom_qty = line.product_uom_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_uom_qty = 0

            # Compute price_unit in appropriate currency
            if requisition.company_id.currency_id != currency:
                price_unit = requisition.company_id.currency_id.compute(price_unit, currency)

            # Create PO line
            order_lines.append((0, 0, {
                'name': name,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': product_uom_qty,
                'price_unit': price_unit,
                'taxes_id': [(6, 0, taxes_ids)],
                'date_planned': requisition.schedule_date or fields.Date.today(),
                'procurement_ids': [(6, 0, [requisition.procurement_id.id])] if requisition.procurement_id else False,
                'account_analytic_id': line.account_analytic_id.id,
            }))
        self.order_line = order_lines

    @api.multi
    def button_confirm(self):
        res = super(SaleOrder, self).button_confirm()
        for po in self:
            if po.requisition_id.type_id.exclusive == 'exclusive':
                others_po = po.requisition_id.mapped('sale_ids').filtered(lambda r: r.id != po.id)
                others_po.button_cancel()
                po.requisition_id.action_done()

            for element in po.order_line:
                if element.product_id == po.requisition_id.procurement_id.product_id:
                    element.move_ids.write({
                        'procurement_id': po.requisition_id.procurement_id.id,
                        'move_dest_id': po.requisition_id.procurement_id.move_dest_id.id,
                    })
        return res

    @api.model
    def create(self, vals):
        sale = super(SaleOrder, self).create(vals)
        if sale.requisition_id:
            sale.message_post_with_view('mail.message_origin_link',
                    values={'self': sale, 'origin': sale.requisition_id},
                    subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))
        return sale

    @api.multi
    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        if vals.get('requisition_id'):
            self.message_post_with_view('mail.message_origin_link',
                    values={'self': self, 'origin': self.requisition_id, 'edit': True},
                    subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))
        return result


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        res = super(SaleOrderLine, self)._onchange_discount()
        if self.order_id.requisition_id:
            for line in self.order_id.requisition_id.line_ids:
                if line.product_id == self.product_id:
                    if line.product_uom_id != self.product_uom:
                        self.price_unit = line.product_uom_id._compute_price(
                            line.price_unit, self.product_uom)
                    else:
                        self.price_unit = line.price_unit
                    break
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sale_requisition = fields.Selection(
        [('quotation', 'Create a draft sale order'),
         ('tenders', 'Propose a call for tenders')],
        string='Procurement', default='quotation')


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    requisition_id = fields.Many2one('sale.requisition', string='Latest Requisition')

    @api.multi
    def make_po(self):
        Requisition = self.env['sale.requisition']
        procurements = self.env['procurement.order']
        Warehouse = self.env['stock.warehouse']
        res = []
        for procurement in self:
            if procurement.product_id.sale_requisition == 'tenders':
                warehouse_id = Warehouse.search([('company_id', '=', procurement.company_id.id)], limit=1).id
                requisition_id = Requisition.create({
                    'origin': procurement.origin,
                    'date_end': procurement.date_planned,
                    'warehouse_id': warehouse_id,
                    'company_id': procurement.company_id.id,
                    'procurement_id': procurement.id,
                    'picking_type_id': procurement.rule_id.picking_type_id.id,
                    'line_ids': [(0, 0, {
                        'product_id': procurement.product_id.id,
                        'product_uom_id': procurement.product_uom.id,
                        'product_uom_qty': procurement.product_qty
                    })],
                })
                procurement.message_post(body=_("Sale Requisition created"))
                requisition_id.message_post_with_view('mail.message_origin_link',
                    values={'self': requisition_id, 'origin': procurement},
                    subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'))
                procurement.requisition_id = requisition_id
                procurements += procurement
                res += [procurement.id]
        set_others = self - procurements
        if set_others:
            res += super(ProcurementOrder, set_others).make_po()
        return res
