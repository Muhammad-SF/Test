# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class CustomerCategory(models.Model):
    _name = 'customer.category'
    _order = 'sequence'
    
    name = fields.Char("Category", required=True)
    parent_id = fields.Many2one("res.partner.category", "Parent Category")
    sequence = fields.Integer("Sequence")
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_category_id = fields.Many2one('customer.category', string='Customer Category')
    
    @api.multi
    @api.onchange('customer_category_id')
    def onchange_customer_category_id(self):
        if self.customer_category_id and self.customer_category_id.pricelist_id:
            self.property_product_pricelist = self.customer_category_id.pricelist_id.id


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id and self.partner_id.property_product_pricelist:
            self.pricelist_id = self.partner_id.property_product_pricelist.id
        return res