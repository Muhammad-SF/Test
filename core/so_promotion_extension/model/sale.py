from openerp import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from pygments.lexer import _inherit

class promotion_gift(models.TransientModel):
    _name = "promotion.gift"
    
    product_id = fields.Many2one('product.product', string='Product gift')
    quantity_free = fields.Float('Quantity free', )
    apply_promotion_on_so_id = fields.Many2one('apply.sale.promotion', string='Product gift')
    account_id = fields.Many2one('account.account', string='Account')
    apply_promotion_automatically_on_so_id = fields.Many2one('apply.sale.promotion.automatically.wiz', string='Product gift')


class apply_promotion_on_so(models.TransientModel):
    _inherit = "apply.sale.promotion"
    
    sale_promotion_ids = fields.Many2many('sale.promotion', 'apply_sale_sale_promotion_rel', 'apply_promotion_id','sale_promotion_id', string='Discounts')
    promotion_gift_line = fields.One2many('promotion.gift', 'apply_promotion_on_so_id', 'Gifts apply')
    visible = fields.Boolean("Visible", default=False)
    number_of_product = fields.Char('Number of product')
    
    @api.onchange('sale_promotion_ids')
    def onchange_promosition_ids(self):
        line_vals = []
        num_of_product = 0
        for record in self:
            type_of_sale_promotion = []
            if record.sale_promotion_ids:
                for sale_promotion_id in record.sale_promotion_ids:
                    type_of_sale_promotion.append(sale_promotion_id.type)
                    if sale_promotion_id.type == '8_by_pack_product_free_flexible_product':
                        num_of_product += int(sale_promotion_id.number_of_product)
                         
                        #visible = True
                        if sale_promotion_id.gift_free_ids:
                            for gift_free_id in sale_promotion_id.gift_free_ids:
                                #add extra
                                line_vals.append((0,0,{'product_id':gift_free_id.product_id.id,
                                      'quantity_free':gift_free_id.quantity_free,
                                      'account_id':gift_free_id.account_id,}))
                            
        self.promotion_gift_line = line_vals
        self.number_of_product = num_of_product
        if '8_by_pack_product_free_flexible_product' in type_of_sale_promotion:
            self.visible = True
        else:
            self.visible = False
    
    @api.multi
    def action_apply(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        promotion_gift_lines = self.promotion_gift_line
        quantity_free = 0 
        if promotion_gift_lines:
            for promotion_gift_line in promotion_gift_lines:
                quantity_free += promotion_gift_line.quantity_free
        if self.number_of_product:
            if self.number_of_product.isdigit():
                if int(self.number_of_product) != quantity_free:
                    raise UserError(_('Please check the free gift'))
                
        if active_id:
            sale = self.env['sale.order'].browse(active_id)
            for promotion in self.sale_promotion_ids:
                if len(self.sale_promotion_ids.ids)>1 and promotion.stackable == False:
                    raise UserError(_('You cannot choose this program, stacking is not permitted - %s') % promotion.name)
            #default
            #sale.with_context({'promotion_gift_line': self.promotion_gift_line}).apply_promotion(self.sale_promotion_ids)
            if promotion_gift_lines:
                for sale_promotion_id in self.sale_promotion_ids:
                    #sale.with_context({'promotion_gift_line': self.promotion_gift_line}).apply_promotion(sale_promotion_id)
                    if sale_promotion_id.type ==  '8_by_pack_product_free_flexible_product':
                        self._cr.execute("SELECT count(product_id) FROM sale_promotion_gift_condition as b WHERE product_id not in (SELECT product_id FROM sale_order_line as a WHERE b.product_id = a.product_id and order_id=%s and a.product_uom_qty >= b.minimum_quantity and a.product_uom_qty <= b.maximum_quantity) and promotion_id=%s" % (sale.id, sale_promotion_id.id))
                        if not self._cr.fetchone()[0]:
                            sale.with_context({'promotion_gift_line': self.promotion_gift_line}).apply_promotion(sale_promotion_id)
                
                
                
                #sale.with_context({'promotion_gift_line': self.promotion_gift_line}).apply_promotion(self.sale_promotion_ids)
            else:
                sale.apply_promotion(self.sale_promotion_ids)
        return True
    
class apply_promotion_on_so(models.Model):
    
    _inherit = "sale.promotion"
    
    number_of_product = fields.Char('Number of product')
    number_of_product_description = fields.Text('Free product Description')
    stackable = fields.Boolean('Stackable')
    type = fields.Selection([
        ('1_discount_total_order', 'Discount on total order'),
        ('2_discount_category', 'Discount on categories'),
        ('3_discount_by_quantity_of_product', 'Discount by quantity of product'),
        ('4_pack_discount', 'By pack products discount products'),
        ('5_pack_free_gift', 'By pack products free products'),
        ('6_price_filter_quantity', 'Unit Price product filter by quantity'),
        ('7_total_price_product_filter_by_quantity', 'Total Price product filter by quantity'),
        ('8_by_pack_product_free_flexible_product', 'By pack product free flexible product'),
    ], 'Type', required=1)
    
    

class sale_order(models.Model):

    _inherit = "sale.order"
    
    promotion_ids = fields.Many2many('sale.promotion', 'sale_order_sale_promotion_rel', 'sale_id','sale_promotion_id', string='Promotions programs')

    @api.multi
    def apply_promotion_automatically(self):
        line_vals = []
        num_of_product = 0
        for sale in self:
            type_of_sale_promotion = []
            filter_ids = sale.filter_promotions()
            #add
            sale_promotion_recs = self.env['sale.promotion'].browse(filter_ids)
            for sale_promotion_rec in sale_promotion_recs:
                type_of_sale_promotion.append(sale_promotion_rec.type)
                if sale_promotion_rec.type == '8_by_pack_product_free_flexible_product':
                    num_of_product += int(sale_promotion_rec.number_of_product)
                    if sale_promotion_rec.gift_free_ids:
                        for gift_free_id in sale_promotion_rec.gift_free_ids:
                            line_vals.append((0,0,{'product_id':gift_free_id.product_id.id,
                                              'quantity_free':gift_free_id.quantity_free,
                                              'account_id':gift_free_id.account_id.id,}))
            
            if '8_by_pack_product_free_flexible_product' in type_of_sale_promotion:
                return {
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'apply.sale.promotion.automatically.wiz',
                        'target': 'new',
                        'context': {'active_sale_id': self.id,'line_vals':line_vals,'filter_ids':filter_ids,'num_of_product':num_of_product}
                       }
            else:
                #default
                sale.apply_promotion(self.env['sale.promotion'].browse(filter_ids))
        return True
    
    def filter_promotions(self):
        sale = self
        filter_ids = []
        promotions = self.env['sale.promotion'].search([('active', '=', True), ('stackable','=',True), ('start_date', '<=', sale.date_order), '|', ('end_date', '>=', sale.date_order), ('end_date', '=', False)])
        for rec in promotions:
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
            #add
            elif rec.type ==  '8_by_pack_product_free_flexible_product':
                self._cr.execute("SELECT count(product_id) FROM sale_promotion_gift_condition as b WHERE product_id not in (SELECT product_id FROM sale_order_line as a WHERE b.product_id = a.product_id and order_id=%s and a.product_uom_qty >= b.minimum_quantity and a.product_uom_qty <= b.maximum_quantity) and promotion_id=%s" % (sale.id, rec.id))
                if not self._cr.fetchone()[0]:
                    filter_ids.append(rec.id)
                    continue
            
        return filter_ids
    
    
    
    def apply_promotion(self, recs):
        total_discount_amount = 0.00
        gift_vals = []
        for rec in recs:
            sale = self
            self.env['sale.order.line'].search([('order_id', '=', sale.id), ('promotion', '=', True)]).unlink()
            promotional_product_id = self.env.ref('so_promotion.promotion_service_01')
    
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
                        gift_vals.append({
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
            #add
            elif rec.type ==  '8_by_pack_product_free_flexible_product':
                self._cr.execute("SELECT count(product_id) FROM sale_promotion_gift_condition as b WHERE product_id not in (SELECT product_id FROM sale_order_line as a WHERE b.product_id = a.product_id and order_id=%s and a.product_uom_qty >= b.minimum_quantity and a.product_uom_qty <= b.maximum_quantity) and promotion_id=%s" % (sale.id, rec.id))
                if not self._cr.fetchone()[0]:
                    if self._context.has_key('promotion_gift_line'):
                        promotion_gift_lines = self._context.get('promotion_gift_line')
                        #for promotion_gift_line in promotion_gift_lines:
                        if promotion_gift_lines:
                            for promotion_gift_line in promotion_gift_lines:
                                gift_vals.append({
                                    'order_id': sale.id,
                                    'product_id': promotion_gift_line.product_id.id,
                                    'product_uom_qty': promotion_gift_line.quantity_free,
                                    'product_uom': promotion_gift_line.product_id.uom_id.id,
                                    'price_unit': 0.00,
                                    'account_id': promotion_gift_line.account_id.id, 
                                    'promotion': True,
                                })
                    else:
                        for gift_free_id in rec.gift_free_ids:
                            gift_vals.append({
                                'order_id': sale.id,
                                'product_id': gift_free_id.product_id.id,
                                'product_uom_qty': gift_free_id.quantity_free,
                                'product_uom': gift_free_id.product_id.uom_id.id,
                                'price_unit': 0.00,
                                'account_id': gift_free_id.account_id.id, 
                                'promotion': True,
                            })
        if total_discount_amount:
            sale_line = self.env['sale.order.line'].create({
                'order_id': sale.id,
                'product_id': promotional_product_id.id,
                'product_uom_qty': 1,
                'account_id': promotional_product_id.property_account_expense_id.id,
                'product_uom': promotional_product_id.uom_id.id,
                'price_unit': total_discount_amount,
                'promotion': True,
            })
        if gift_vals:
            for vals in gift_vals:
                gift_line = self.env['sale.order.line'].create(vals)
        if recs:
            self.write({
                'promotion_ids': [(6, 0, recs.ids)]
            })
        return True
    

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    last_sales_price = fields.Float(string='Last Sales Price')
    last_sales_price_customer = fields.Float(string='Last Sales Price to this customer')
    
    @api.onchange('product_id')
    def get_last_sales_price(self):
        for rec in self:
            order_lines_id = self.env['sale.order.line'].search([('order_id.state','in',['done','sale']),('product_id','=',rec.product_id.id)],limit=1)
            if order_lines_id:
                rec.last_sales_price = order_lines_id.price_unit
            corder_lines_id = self.env['sale.order.line'].search([('order_id.state','in',['done','sale']),('product_id','=',rec.product_id.id),('order_id.partner_id','=',rec.order_id.partner_id.id)],limit=1)
            if corder_lines_id:
                rec.last_sales_price_customer = corder_lines_id.price_unit
                
                
    
    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product_id = vals.get('product_id')
            order_lines_id = self.env['sale.order.line'].search([('order_id.state','in',['done','sale']),('product_id', '=', product_id)],limit=1)
            if order_lines_id:
                last_sales_price = order_lines_id.price_unit
                vals.update({'last_sales_price': last_sales_price})
            sale = self.env['sale.order'].browse(vals.get('order_id'))
            corder_lines_id = self.env['sale.order.line'].search([('order_id.state','in',['done','sale']),('product_id','=', product_id),('order_id.partner_id','=', sale.partner_id.id)],limit=1)
            if corder_lines_id:
                last_sales_price_customer = corder_lines_id.price_unit
                vals.update({'last_sales_price_customer': last_sales_price_customer})
        res = super(SaleOrderLine, self).create(vals)
        return res
     
    @api.multi
    def write(self, vals):
        if vals.get('product_id'):
            product_id = vals.get('product_id')
            order_lines_id = self.env['sale.order.line'].search([('order_id.state','in',['done','sale']),('product_id', '=', product_id)],limit=1)
            if order_lines_id:
                last_sales_price = order_lines_id.price_unit
                vals.update({'last_sales_price': last_sales_price})
            corder_lines_id = self.env['sale.order.line'].search([('order_id.state','in',['done','sale']),('product_id','=', product_id),('order_id.partner_id','=',self.order_id.partner_id.id)],limit=1)
            if corder_lines_id:
                last_sales_price_customer = corder_lines_id.price_unit
                vals.update({'last_sales_price_customer': last_sales_price_customer})
        res = super(SaleOrderLine, self).write(vals)
        return res
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
