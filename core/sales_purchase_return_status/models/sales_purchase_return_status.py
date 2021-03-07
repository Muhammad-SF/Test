from odoo import fields, api, models, _, tools
from odoo.exceptions import UserError


class company(models.Model):
    _inherit = 'res.company'

    return_status_sale = fields.Boolean('Return Status', default=False)
    return_status_purchase = fields.Boolean('Return Status', default=False)

class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    return_status_sale = fields.Boolean(related='company_id.return_status_sale', string="Return Status")


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    return_status_purchase = fields.Boolean(related='company_id.return_status_purchase', string="Return Status")



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_return_status = fields.Selection((['none', 'None'],
                                      ['partial_return', 'Partial Return'],
                                      ['fully_return', 'Fully Return']),
                                        string="Return Status", readonly=True, default='none')

    return_status_config = fields.Boolean(related='company_id.return_status_sale', string="Return Status")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_return_qty = fields.Float(string="Return Quantity", copy=False)

    sale_return_status = fields.Selection((['none', 'None'],
                                      ['partial_return', 'Partial Return'],
                                      ['fully_return', 'Fully Return']),
                                        string="Return Status", readonly=True, default='none')

class InheritSaleReport(models.Model):
    _inherit = "sale.report"

    sale_return_qty = fields.Float(string="Return Quantity", copy=False)

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    t.uom_id as product_uom,
                    sum(l.sale_return_qty / u.factor * u2.factor) as sale_return_qty,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) as price_subtotal,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.state as state,
                    s.partner_id as partner_id,
                    s.user_id as user_id,
                    s.company_id as company_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    t.categ_id as categ_id,
                    s.pricelist_id as pricelist_id,
                    s.project_id as analytic_account_id,
                    s.team_id as team_id,
                    p.product_tmpl_id,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    return_status = fields.Selection((['none', 'None'],
                                      ['partial_return', 'Partial Return'],
                                      ['fully_return', 'Fully Return']),
                                     string="Return Status", readonly=True, default='none')

    return_status_purchase_config = fields.Boolean(related='company_id.return_status_purchase', string="Return Status")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    return_qty = fields.Float(string="Return Quantity", copy=False)

    return_status = fields.Selection((['none', 'None'],
                                      ['partial_return', 'Partial Return'],
                                      ['fully_return', 'Fully Return']),
                                     string="Return Status", default='none')

class InheritPurchaseReport(models.Model):
    _inherit = "purchase.report"

    return_qty = fields.Float(string="Return Quantity", copy=False)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'purchase_report')
        self._cr.execute("""
            create view purchase_report as (
                WITH currency_rate as (%s)
                select
                    min(l.id) as id,
                    s.date_order as date_order,
                    s.state,
                    s.date_approve,
                    s.dest_address_id,
                    spt.warehouse_id as picking_type_id,
                    s.partner_id as partner_id,
                    s.create_uid as user_id,
                    s.company_id as company_id,
                    s.fiscal_position_id as fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    s.currency_id,
                    t.uom_id as product_uom,
                    sum(l.product_qty/u.factor*u2.factor) as unit_quantity,
                    extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                    extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                    count(*) as nbr_lines,
                    sum(l.price_unit / COALESCE(cr.rate, 1.0) * l.product_qty)::decimal(16,2) as price_total,
                    avg(100.0 * (l.price_unit / COALESCE(cr.rate,1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2) as negociation,
                    sum(ip.value_float*l.product_qty/u.factor*u2.factor)::decimal(16,2) as price_standard,
                    sum(l.return_qty / u.factor * u2.factor) as return_qty,
                    (sum(l.product_qty * l.price_unit / COALESCE(cr.rate, 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    analytic_account.id as account_analytic_id,
                    sum(p.weight * l.product_qty/u.factor*u2.factor) as weight,
                    sum(p.volume * l.product_qty/u.factor*u2.factor) as volume
                from purchase_order_line l
                    join purchase_order s on (l.order_id=s.id)
                    join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                            LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.product,',p.id) AND ip.company_id=s.company_id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join stock_picking_type spt on (spt.id=s.picking_type_id)
                    left join account_analytic_account analytic_account on (l.account_analytic_id = analytic_account.id)
                    left join currency_rate cr on (cr.currency_id = s.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
                group by
                    s.company_id,
                    s.create_uid,
                    s.partner_id,
                    u.factor,
                    s.currency_id,
                    l.price_unit,
                    s.date_approve,
                    l.date_planned,
                    l.product_uom,
                    s.dest_address_id,
                    s.fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id,
                    s.date_order,
                    s.state,
                    spt.warehouse_id,
                    u.uom_type,
                    u.category_id,
                    t.uom_id,
                    u.id,
                    u2.factor,
                    partner.country_id,
                    partner.commercial_partner_id,
                    analytic_account.id
            )
        """ % self.env['res.currency']._select_companies_rates())

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        # TDE FIXME: store it in the wizard, stupid
        picking = self.env['stock.picking'].browse(self.env.context['active_id'])
        sale_order = self.env['sale.order'].search([('name', '=', picking.origin)])
        purchase_order = self.env['purchase.order'].search([('name', '=', picking.origin)])


        if sale_order:
            if sale_order.company_id and sale_order.company_id.return_status_sale:
                for sale_line in sale_order.order_line:
                    for sale_return_line in self.product_return_moves:
                        if sale_line.product_id.id == sale_return_line.product_id.id:
                            if sale_line.product_uom_qty > sale_return_line.quantity:
                                sale_line.sudo().write(
                                    {'sale_return_status': 'partial_return', 'sale_return_qty': sale_return_line.quantity})

                            elif sale_line.product_uom_qty == sale_return_line.quantity:
                                sale_line.sudo().write(
                                    {'sale_return_status': 'fully_return', 'sale_return_qty': sale_return_line.quantity})

                            else:
                                raise UserError(_("Return Quantity cannot be more than Ordered Quantity"))

                sale_order_status = sale_order.order_line.filtered(lambda x: x.sale_return_status == 'partial_return')
                if not sale_order_status:
                    sale_order.sudo().write({'sale_return_status': 'fully_return'})
                else:
                    sale_order.sudo().write({'sale_return_status': 'partial_return'})


        if purchase_order:
            if purchase_order.company_id and purchase_order.company_id.return_status_purchase:
                for purchase_line in purchase_order.order_line:
                    for purchase_return_line in self.product_return_moves:
                        if purchase_line.product_id.id == purchase_return_line.product_id.id:
                            if purchase_line.product_qty > purchase_return_line.quantity:
                                purchase_line.sudo().write(
                                    {'return_status': 'partial_return', 'return_qty': purchase_return_line.quantity})

                            elif purchase_line.product_qty == purchase_return_line.quantity:
                                purchase_line.sudo().write(
                                    {'return_status': 'fully_return', 'return_qty': purchase_return_line.quantity})

                            else:
                                raise UserError(_("Return Quantity cannot be more than Ordered Quantity"))

                order_status = purchase_order.order_line.filtered(lambda x: x.return_status == 'partial_return')
                if not order_status:
                    purchase_order.sudo().write({'return_status': 'fully_return'})
                else:
                    purchase_order.sudo().write({'return_status': 'partial_return'})


        return_moves = self.product_return_moves.mapped('move_id')
        unreserve_moves = self.env['stock.move']
        for move in return_moves:
            to_check_moves = self.env['stock.move'] | move.move_dest_id
            while to_check_moves:
                current_move = to_check_moves[-1]
                to_check_moves = to_check_moves[:-1]
                if current_move.state not in ('done', 'cancel') and current_move.reserved_quant_ids:
                    unreserve_moves |= current_move
                split_move_ids = self.env['stock.move'].search([('split_from', '=', current_move.id)])
                to_check_moves |= split_move_ids

        if unreserve_moves:
            unreserve_moves.do_unreserve()
            # break the link between moves in order to be able to fix them later if needed
            unreserve_moves.write({'move_orig_ids': False})

        # create new picking for returned products
        picking_type_id = picking.picking_type_id.return_picking_type_id.id or picking.picking_type_id.id
        new_picking = picking.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': picking.name,
            'location_id': picking.location_dest_id.id,
            'location_dest_id': self.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': picking},
                                           subtype_id=self.env.ref('mail.mt_note').id)

        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed"))
            new_qty = return_line.quantity
            if new_qty:
                # The return of a return should be linked with the original's destination move if it was not cancelled
                if return_line.move_id.origin_returned_move_id.move_dest_id.id and return_line.move_id.origin_returned_move_id.move_dest_id.state != 'cancel':
                    move_dest_id = return_line.move_id.origin_returned_move_id.move_dest_id.id
                else:
                    move_dest_id = False

                returned_lines += 1
                return_line.move_id.copy({
                    'product_id': return_line.product_id.id,
                    'product_uom_qty': new_qty,
                    'picking_id': new_picking.id,
                    'state': 'draft',
                    'location_id': return_line.move_id.location_dest_id.id,
                    'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
                    'picking_type_id': picking_type_id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                    'origin_returned_move_id': return_line.move_id.id,
                    'procure_method': 'make_to_stock',
                    'move_dest_id': move_dest_id,
                })

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id