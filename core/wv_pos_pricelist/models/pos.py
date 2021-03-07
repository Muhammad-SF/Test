# -*- coding: utf-8 -*-

from odoo import models, fields ,api


class PosPriceList(models.Model):
    _name = 'pos.pricelist'

    name = fields.Char(string="Name", required=True)
    item_ids = fields.One2many('pos.pricelist.items', 'pos_pricelist_id', string="Pricelist Items")



class PosPricelistItems(models.Model):
    _name = 'pos.pricelist.items'

    name = fields.Char(string="Applicable On", required=True)
    pos_pricelist_id = fields.Many2one('pos.pricelist', string="Pricelist")
    applied_on = fields.Selection([('global', "Global"), ('product_category', 'Product Category'),
                                   ('product', 'Product'), ('default_code', 'Item Code')], string="Applied On", default='global', required=True)
    min_quantity = fields.Integer(string="Minimum Quantity",default=1)
    date_start = fields.Date(string="Date Start")
    date_end = fields.Date(string="Date End")
    compute_price = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage')],string="Compute Price", default='fixed')
    fixed_price = fields.Float(string="Fixed Price")
    percent_price = fields.Float(string="Percentage")
    categ_id = fields.Many2one('pos.category', string="Product Category")
    product_tmpl_id = fields.Many2one('product.template', string="Product")
    item1 = fields.Many2one('wv.default.code', string="Item code")



class PriceListPartner(models.Model):
    _inherit = 'res.partner'

    pos_pricelist_id = fields.Many2one('pos.pricelist', string="POS Pricelist")

class WvDefaultCode(models.Model):
    _name = 'wv.default.code'

    name = fields.Char(string="Item Code")

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_selection = fields.Many2one("wv.default.code","Item Code")

class pos_config(models.Model):
    _inherit = 'pos.config' 
    
    allow_pricelist = fields.Boolean("Allow Pricelist")
    default_pricelist = fields.Many2one("pos.pricelist","Default Pricelist")


class PosOrder(models.Model):
    _inherit = "pos.order"

    pos_pricelist = fields.Many2one("pos.pricelist","Pricelist")

    @api.model
    def _order_fields(self,ui_order):
        fields = super(PosOrder,self)._order_fields(ui_order)
        fields['pos_pricelist'] = ui_order.get('pos_pricelist',0)
        return fields



