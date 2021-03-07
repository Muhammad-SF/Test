from odoo import fields,models,api,_

class product_sku_serializer(models.Model):

    _name = 'product.sku.serializer'

    prefix_sku = fields.Char(string="Prefix")
    suffix_sku = fields.Char(string="Suffix")
    product_categ_id = fields.Many2one('product.category',string="Product Category")
    digits = fields.Integer(string="Digits")
    current_number = fields.Char(string="Current Number", default='0')


    @api.onchange('digits')
    def _current_number(self):
        n = '0'
        self.current_number =  n.zfill(self.digits)

    _sql_constraints = [('product_categ_id_uniq', 'unique (product_categ_id)',\
                         "Product SKU Serializer for a Product Category already exist !")]
