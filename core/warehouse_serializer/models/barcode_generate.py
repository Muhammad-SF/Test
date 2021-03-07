from odoo import fields,models,api,_
from odoo.exceptions import UserError

class barcode_number(models.Model):

    _name = 'barcode.number'

    digits = fields.Integer(string="Digits")
    current_number = fields.Char(string="Current Number", default='0')

    @api.onchange('digits')
    def _current_number(self):
        n = '0'
        self.current_number = n.zfill(self.digits)

class generate_barcode_number(models.TransientModel):

    _name = 'generate.barcode.number'

    @api.multi
    def generate_barcode_number(self):
        active_ids =  self._context.get('active_ids')

        product_ids = self.env['product.product'].browse(active_ids)

        for product_id in product_ids:
            '''
            old code commented to generate barcode from SKU serializer
            if not product_id.barcode:
                barcode_id = self.env['barcode.number'].search([])
                if not barcode_id:
                    raise UserError(_('Please create Barcode Number Serializer!'))
                else:
                    barcode_id = barcode_id[0]
                barcode_id.current_number = int(barcode_id.current_number) + 1
                generete_barcode = str(barcode_id.current_number).zfill(barcode_id.digits)
                product_id.write({'barcode':generete_barcode})
                barcode_id.write({'current_number':generete_barcode})
            '''
            if product_id.barcode:
                continue
            product_category = product_id.categ_id
            product_sku_serializer_id = self.env[
                'product.sku.serializer'].search(
                    [('product_categ_id', '=', product_category.id)])
            if not product_sku_serializer_id:
                raise UserError(_('First create SKU Serializer for %s Cagetory' % (product_category.name)))
            if product_sku_serializer_id:
                prefix_sku = product_sku_serializer_id.prefix_sku
                current_number = int(product_sku_serializer_id.current_number) + 1

                sequence = str(current_number).zfill(product_sku_serializer_id.digits)

                suffix_sku = product_sku_serializer_id.suffix_sku
                serialize_sequence = prefix_sku + sequence + suffix_sku
                # Update sequence
                product_sku_serializer_id.current_number = sequence

               ## Updating product with newly generated barcode
                product_id.write({'barcode': serialize_sequence})

           #if lot_number_serializer_id:
           #    #prefix_lot = lot_number_serializer_id.prefix_lot
           #    prefix_sku = product_sku_serializer_id.prefix_sku
           #    #current_number = int(lot_number_serializer_id.current_number) + 1
           #    current_number = int(product_sku_serializer_id.current_number) + 1
           #    suffix_lot = lot_number_serializer_id.suffix_lot
           #    #sequence = str(current_number).zfill(lot_number_serializer_id.digits)
           #    sequence = str(current_number).zfill(product_sku_serializer_id.digits)
           #    if lot_number_serializer_id.start_with_sku == True:
           #        if self.product_id.default_code:
           #            serialize_sequence = self.product_id.default_code + '_' + prefix_lot + sequence + suffix_lot
           #        else:
           #            serialize_sequence = prefix_lot + sequence + suffix_lot
           #    else:
           #        serialize_sequence = prefix_lot + sequence + suffix_lot
           #    ## Updating sequence in lot serialiser
           #    lot_number_serializer_id.current_number = sequence

           #    ## Updating product with newly generated barcode
           #    product_id.write({'barcode': serialize_sequence})


