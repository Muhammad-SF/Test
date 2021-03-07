from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class apply_promotion_on_so_automatically_wiz(models.TransientModel):
    
    _name = "apply.sale.promotion.automatically.wiz"
    
    sale_id = fields.Many2one('sale.order', string='So')
    promotion_gift_line = fields.One2many('promotion.gift', 'apply_promotion_automatically_on_so_id', 'Gifts apply')
    sale_promotion_ids = fields.Many2many('sale.promotion', 'apply_sale_sale_promotion_rel_new', 'apply_promotion_id','sale_promotion_id', string='Discounts')
    number_of_product = fields.Char('Number of product')

    @api.model
    def default_get(self, fields):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')
        sale_id = self.env['sale.order'].browse(active_id)
        res = super(apply_promotion_on_so_automatically_wiz, self).default_get(fields)
        #sale_id
        if sale_id:
            res.update({'sale_id':sale_id.id})
        #sale_promotion_ids
        if self._context.has_key('filter_ids'):
            filter_ids = self._context.get('filter_ids')
            sale_promotion_recs = self.env['sale.promotion'].browse(filter_ids) 
            if sale_promotion_recs:
                res.update({'sale_promotion_ids':[(6,0,sale_promotion_recs.ids)]})
        #line_vals
        if self._context.has_key('line_vals'):
            line_vals = self._context.get('line_vals')
            if line_vals:
                res.update({'promotion_gift_line':line_vals,'sale_id':sale_id.id})
        #num_of_product
        if self._context.has_key('num_of_product'):
            num_of_product = self._context.get('num_of_product')
            res.update({'number_of_product':num_of_product})
        
        return res
    
    def apply_auto_promotion(self, recs):
        quantity_free = 0
        promotion_gift_lines = self.promotion_gift_line
        for promotion_gift_line in promotion_gift_lines:
                quantity_free += promotion_gift_line.quantity_free
                
        if self.number_of_product:
            if self.number_of_product.isdigit():
                if int(self.number_of_product) != quantity_free:
                    raise UserError(_('Please check the free gift'))
        if self.sale_promotion_ids and self.sale_id:
            for sale_promotion_id in self.sale_promotion_ids:
                self.sale_id.with_context({'promotion_gift_line': self.promotion_gift_line}).apply_promotion(sale_promotion_id)
            
        return True
