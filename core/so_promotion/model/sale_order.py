from openerp import api, fields, models, _
from odoo.exceptions import UserError

class sale_order(models.Model):

    _inherit = "sale.order"

    promotion_id = fields.Many2one('sale.promotion', string='Promotions program')

    def filter_promotions(self):
        sale = self
        filter_ids = []
        for rec in self.env['sale.promotion'].search([('active', '=', True), ('start_date', '<=', sale.date_order), '|', ('end_date', '>=', sale.date_order), ('end_date', '=', False)]):
            if rec.type == '1_discount_total_order':
                discount_order_line = self.env['sale.promotion.discount.order'].search([('promotion_id', '=', rec.id), ('minimum_amount', '<=', sale.amount_untaxed)])
                if discount_order_line:
                    filter_ids.append(rec.id)
                    continue
            elif rec.type ==  '2_discount_category':
                for order_line in sale.order_line:
                    if self.env['sale.promotion.discount.category'].search([('promotion_id', '=', rec.id), ('category_id', '=', order_line.product_id.categ_id.id)]):
                        filter_ids.append(rec.id)
                        continue
            elif rec.type ==  '3_discount_by_quantity_of_product':
                for order_line in sale.order_line:
                    if self.env['sale.promotion.discount.quantity'].search([('promotion_id', '=', rec.id), ('product_id', '=', order_line.product_id.id), ('minimum_quantity', '<=', order_line.product_uom_qty), ('maximum_quantity', '>=', order_line.product_uom_qty)]):
                        filter_ids.append(rec.id)
                        continue
            elif rec.type ==  '4_pack_discount':
                self._cr.execute("SELECT count(product_id) FROM sale_promotion_discount_condition as b WHERE product_id not in (SELECT product_id FROM sale_order_line as a WHERE b.product_id = a.product_id and order_id=%s and a.product_uom_qty >= b.minimum_quantity and a.product_uom_qty <= b.maximum_quantity) and promotion_id=%s" % (sale.id, rec.id))
                if not self._cr.fetchone()[0]:
                    filter_ids.append(rec.id)
                    continue
            elif rec.type ==  '5_pack_free_gift':
                self._cr.execute("SELECT count(product_id) FROM sale_promotion_gift_condition as b WHERE product_id not in (SELECT product_id FROM sale_order_line as a WHERE b.product_id = a.product_id and order_id=%s and a.product_uom_qty >= b.minimum_quantity and a.product_uom_qty <= b.maximum_quantity) and promotion_id=%s" % (sale.id, rec.id))
                if not self._cr.fetchone()[0]:
                    filter_ids.append(rec.id)
                    continue
            elif rec.type ==  '6_price_filter_quantity':
                for price_id in rec.price_ids:
                    if self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', price_id.product_id.id), ('product_uom_qty', '>=', price_id.minimum_quantity), ('product_uom_qty', '<=', price_id.maximum_quantity)]):
                        filter_ids.append(rec.id)
                        continue
            
            elif rec.type ==  '7_total_price_product_filter_by_quantity':
                for price_id in rec.sale_promotion_price_quantity_ids:
                    if self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', price_id.product_id.id), ('product_uom_qty', '>=', price_id.minimum_quantity), ('product_uom_qty', '<=', price_id.maximum_quantity)]):
                        filter_ids.append(rec.id)
                        continue
        return filter_ids

    @api.multi
    def apply_promotion_automatically(self):
        for sale in self:
            filter_ids = sale.filter_promotions()
            if len(filter_ids) > 1:
                raise UserError(_("There are multiple promotions applicable, please select manually the promotion to apply."))
            sale.apply_promotion(self.env['sale.promotion'].browse(filter_ids))
        return True
    
    def apply_promotion(self, rec):
        sale = self
        self.env['sale.order.line'].search([('order_id', '=', sale.id), ('promotion', '=', True)]).unlink()
        promotional_product_id = self.env.ref('so_promotion.promotion_service_01')
        total_discount_amount = 0.00

        if rec.type == '1_discount_total_order':
            discount_order_line = self.env['sale.promotion.discount.order'].search([('promotion_id', '=', rec.id), ('minimum_amount', '<=', sale.amount_untaxed)], order='minimum_amount desc', limit=1)
#             if discount_order_line:
            total_discount_amount += -(sale.amount_untaxed * discount_order_line.discount) / 100
        elif rec.type ==  '2_discount_category':
            product_total_cat_vise = {}
            for order_line in sale.order_line:
#                 if rec.discount_category_ids.search([('category_id', '=', order_line.product_id.categ_id.id)]):
                if order_line.product_id.categ_id.id in product_total_cat_vise.keys():
                    product_total_cat_vise[order_line.product_id.categ_id.id] = product_total_cat_vise[order_line.product_id.categ_id.id] + order_line.price_subtotal
                else:
                    product_total_cat_vise.update({order_line.product_id.categ_id.id: order_line.price_subtotal})
            discount_amount = 0.00
            for discount_category_id in rec.discount_category_ids:
                for cat_id in product_total_cat_vise.keys():
                    if cat_id == discount_category_id.category_id.id:
                        discount_amount += product_total_cat_vise.get(cat_id)
            if discount_amount:
                total_discount_amount += -(discount_amount * discount_category_id.discount) / 100
        elif rec.type ==  '3_discount_by_quantity_of_product':
            discount_amount = 0.00
            for order_line in sale.order_line:
                discount_quantity_ids = self.env['sale.promotion.discount.quantity'].search([('promotion_id', '=', rec.id), ('product_id', '=', order_line.product_id.id), ('minimum_quantity', '<=', order_line.product_uom_qty), ('maximum_quantity', '>=', order_line.product_uom_qty)], limit=1)
                discount_amount += order_line.price_subtotal
            if discount_amount:
                total_discount_amount += -(discount_amount * discount_quantity_ids.discount) / 100
        elif rec.type ==  '4_pack_discount':
            self._cr.execute("SELECT count(product_id) FROM sale_promotion_discount_condition as b WHERE product_id not in (SELECT product_id FROM sale_order_line as a WHERE b.product_id = a.product_id and order_id=%s and a.product_uom_qty >= b.minimum_quantity and a.product_uom_qty <= b.maximum_quantity) and promotion_id=%s" % (sale.id, rec.id))
            if not self._cr.fetchone()[0]:
                for discount_apply_id in rec.discount_apply_ids:
                    sub_total = self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', discount_apply_id.product_id.id)]).price_subtotal
                    total_discount_amount += -(sub_total * discount_apply_id.discount) / 100
        elif rec.type ==  '5_pack_free_gift':
            self._cr.execute("SELECT count(product_id) FROM sale_promotion_gift_condition as b WHERE product_id not in (SELECT product_id FROM sale_order_line as a WHERE b.product_id = a.product_id and order_id=%s and a.product_uom_qty >= b.minimum_quantity and a.product_uom_qty <= b.maximum_quantity) and promotion_id=%s" % (sale.id, rec.id))
            if not self._cr.fetchone()[0]:
                for gift_free_id in rec.gift_free_ids:
                    self.env['sale.order.line'].create({
                        'order_id': sale.id,
                        'product_id': gift_free_id.product_id.id,
                        'product_uom_qty': gift_free_id.quantity_free,
                        'product_uom': gift_free_id.product_id.uom_id.id,
                        'price_unit': 0.00,
                        'account_id': gift_free_id.account_id.id, 
                        'promotion': True,
                    })
        elif rec.type ==  '6_price_filter_quantity':
            for price_id in rec.price_ids:
                order_line = self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', price_id.product_id.id),
                                        ('product_uom_qty', '>=', price_id.minimum_quantity), ('product_uom_qty', '<=', price_id.maximum_quantity)])
                if order_line:
                    order_line.write({'price_unit': price_id.list_price})
        
        elif rec.type ==  '7_total_price_product_filter_by_quantity':
            for price_id in rec.sale_promotion_price_quantity_ids:
                order_line = self.env['sale.order.line'].search([('order_id', '=', sale.id), ('product_id', '=', price_id.product_id.id),
                                        ('product_uom_qty', '>=', price_id.minimum_quantity), ('product_uom_qty', '<=', price_id.maximum_quantity)])
                if order_line:
                    order_line.write({'price_unit': (price_id.total_price / order_line.product_uom_qty)})
        
        if total_discount_amount:
            self.env['sale.order.line'].create({
                'order_id': sale.id,
                'product_id': promotional_product_id.id,
                'product_uom_qty': 1,
                'account_id': promotional_product_id.property_account_expense_id.id,
                'product_uom': promotional_product_id.uom_id.id,
                'price_unit': total_discount_amount,
                'promotion': True,
            })
        sale.write({
            'promotion_id': rec.id
        })
        return True

class sale_order_line(models.Model):

    _inherit = "sale.order.line"

    promotion = fields.Boolean('Promotion', readonly=1)
    account_id = fields.Many2one('account.account', string='Account', domain=[('deprecated', '=', False)])
    
    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(sale_order_line, self)._prepare_invoice_line(qty)
        if self.promotion:
            res.update({
                'account_id': self.account_id.id
            })
        return res
