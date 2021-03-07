from odoo import api, fields, models, _


class sale_promotion(models.Model):
    _name = "sale.promotion"

    name = fields.Char('Name', required=1)
    active = fields.Boolean('Active', default=1)
    start_date = fields.Datetime('Start date', default=fields.Datetime.now())
    end_date = fields.Datetime('End date')
    type = fields.Selection([
        ('1_discount_total_order', 'Discount on total order'),
        ('2_discount_category', 'Discount on categories'),
        ('3_discount_by_quantity_of_product', 'Discount by quantity of product'),
        ('4_pack_discount', 'By pack products discount products'),
        ('5_pack_free_gift', 'By pack products free products'),
        ('6_price_filter_quantity', 'Unit Price product filter by quantity'),
        ('7_total_price_product_filter_by_quantity', 'Total Price product filter by quantity'),
    ], 'Type', required=1)
    product_id = fields.Many2one('product.product', 'Product service')
    discount_order_ids = fields.One2many('sale.promotion.discount.order', 'promotion_id', 'Discounts')
    discount_category_ids = fields.One2many('sale.promotion.discount.category', 'promotion_id', 'Discounts')
    discount_quantity_ids = fields.One2many('sale.promotion.discount.quantity', 'promotion_id', 'Discounts')
    gift_condition_ids = fields.One2many('sale.promotion.gift.condition', 'promotion_id', 'Gifts condition')
    gift_free_ids = fields.One2many('sale.promotion.gift.free', 'promotion_id', 'Gifts apply')
    discount_condition_ids = fields.One2many('sale.promotion.discount.condition', 'promotion_id', 'Discounts condition')
    discount_apply_ids = fields.One2many('sale.promotion.discount.apply', 'promotion_id', 'Discounts apply')
    price_ids = fields.One2many('sale.promotion.price', 'promotion_id', 'Prices')
    sale_promotion_price_quantity_ids = fields.One2many('sale.promotion.price.quantity', 'promotion_id', 'Total Price')
    

    @api.model
    def default_get(self, fields):
        res = super(sale_promotion, self).default_get(fields)
        products = self.env['product.product'].search([('name', '=', 'Promotion service')])
        if products:
            res.update({'product_id': products[0].id})
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        context = dict(self._context or {})
        if context.get('from_wizard'):
            active_id = context.get('active_sale_id', False)
            if active_id:
                sale = self.env['sale.order'].browse(active_id)
                filter_ids = sale.filter_promotions()
                args = [('id', 'in', filter_ids)]
        return super(sale_promotion, self).name_search(name, args=args, operator=operator, limit=limit)


class sale_promotion_discount_order(models.Model):
    _name = "sale.promotion.discount.order"
    _order = "minimum_amount"

    minimum_amount = fields.Float('Amount total (without tax) greater or equal', required=1)
    discount = fields.Float('Discount %', required=1)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)


class sale_promotion_discount_category(models.Model):
    _name = "sale.promotion.discount.category"
    _order = "category_id, discount"

    category_id = fields.Many2one('product.category', 'Product Category', required=1)
    discount = fields.Float('Discount %', required=1)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)


class sale_promotion_discount_quantity(models.Model):
    _name = "sale.promotion.discount.quantity"
    _order = "product_id"

    product_id = fields.Many2one('product.product', 'Product', required=1)
#     quantity = fields.Float('Minimum quantity', required=1)
    minimum_quantity = fields.Float('Minimum Qty', required=1, default=1.0)
    maximum_quantity = fields.Float('Maximum Qty', required=1, default=1.0)
    discount = fields.Float('Discount %', required=1)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)


class sale_promotion_gift_condition(models.Model):
    _name = "sale.promotion.gift.condition"
    _order = "product_id, minimum_quantity"

    product_id = fields.Many2one('product.product', string='Product',
                                 required=1)
    minimum_quantity = fields.Float('Minimum Qty', required=1, default=1.0)
    maximum_quantity = fields.Float('Maximum Qty', required=1, default=1.0)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)


class sale_promotion_gift_free(models.Model):
    _name = "sale.promotion.gift.free"
    _order = "product_id"

    product_id = fields.Many2one('product.product', string='Product gift',
                                 required=1)
    quantity_free = fields.Float('Quantity free', required=1, default=1.0)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)
    account_id = fields.Many2one('account.account', string='Account', domain=[('deprecated', '=', False)], required=1)


class sale_promotion_discount_condition(models.Model):
    _name = "sale.promotion.discount.condition"
    _order = "product_id, minimum_quantity"

    product_id = fields.Many2one('product.product', string='Product', required=1)
    minimum_quantity = fields.Float('Minimum Qty', required=1, default=1.0)
    maximum_quantity = fields.Float('Maximum Qty', required=1, default=1.0)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)


class sale_promotion_discount_apply(models.Model):
    _name = "sale.promotion.discount.apply"
    _order = "product_id"

    product_id = fields.Many2one('product.product', string='Product', required=1)
    discount = fields.Float('Discount %', required=1, default=1.0)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)
    account_id = fields.Many2one('account.account', string='Account', domain=[('deprecated', '=', False)], required=1)

class sale_promotion_price(models.Model):
    _name = "sale.promotion.price"
    _order = "product_id, minimum_quantity"

    product_id = fields.Many2one('product.product', string='Product', required=1)
    minimum_quantity = fields.Float('Minimum Qty', required=1, default=1.0)
    maximum_quantity = fields.Float('Maximum Qty', required=1, default=1.0)
    list_price = fields.Float('List Price', required=1)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)
    
    
class sale_promotion_price_quantity(models.Model):
    _name = "sale.promotion.price.quantity"
    _order = "product_id, minimum_quantity"

    product_id = fields.Many2one('product.product', string='Product', required=1)
    minimum_quantity = fields.Float('Minimum Qty', required=1, default=1.0)
    maximum_quantity = fields.Float('Maximum Qty', required=1, default=1.0)
    total_price = fields.Float('Total Price', required=1)
    promotion_id = fields.Many2one('sale.promotion', 'Promotion', required=1)
