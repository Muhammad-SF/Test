from odoo import fields,models,api,_

class lot_number_serializer(models.Model):

    _name = 'lot.number.serializer'

    name = fields.Char(string="Name")
    prefix_lot = fields.Char(string="Prefix")
    suffix_lot = fields.Char(string="Suffix")
    product_categ_id = fields.Many2one('product.category',string="Product Category")
    digits = fields.Integer(string="Digits")
    current_number = fields.Char(string="Current Number", default='0')
    start_with_sku = fields.Boolean(string="Start with SKU")

    @api.onchange('digits')
    def _current_number(self):
        n = '0'
        self.current_number = n.zfill(self.digits)

    _sql_constraints = [('product_categ_id_uniq', 'unique (product_categ_id)',\
                         "Lot Numer Serializer for a Product Category already exist !")]

