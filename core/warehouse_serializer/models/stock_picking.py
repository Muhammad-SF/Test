from odoo import fields, models, api, _


class stock_move_inherit(models.Model):
    _inherit = 'stock.move'


class lot_number_serializer(models.Model):
    _inherit = 'stock.picking'


    def serialize_and_validate(self):
        self.action_product_to_serializer()
        self.do_new_transfer()
        return True

    def action_product_to_serializer(self):
        vals_create = {}
        stock_product_id = self.env['serial.lot.number'].search([('serial_name','=', self.name)])
        view_ref = self.env['ir.model.data'].get_object_reference('warehouse_serializer', 'view_form_serial_lot')
        view_id = view_ref[1] if view_ref else False
        if not stock_product_id:
            stock_lot_number = ''
            for product in self.move_lines:

                if (product.product_uom_qty == 1.00):
                    check_lot_number = True
                else:
                    check_lot_number = False

                vals_create.update({'serial_name': self.name})
                if stock_lot_number:
                    stock_lot_number.write(vals_create)
                    if product.product_id.tracking == 'serial':
                        for qty in range(int(product.product_uom_qty)):
                            stock_lot_number.write({'stock_lot_line_ids': [
                                (0, 0, {'product_id': product.product_id.id,
                                        'quantity': 1,
                                        'location_id': product.location_id.id,
                                        'check_lot_number': check_lot_number,
                                        'main_product': True,
                                        'source_location_id': product.location_dest_id.id,
                                        'location_dest_id': product.location_dest_id.id,
                                        })]})
                    elif product.product_id.tracking == 'lot':
                        stock_lot_number.write({'stock_lot_line_ids': [
                            (0, 0, {'product_id': product.product_id.id,
                                    'quantity': product.product_uom_qty,
                                    'location_id': product.location_id.id,
                                    'check_lot_number': check_lot_number,
                                    'main_product': True,
                                    'source_location_id': product.location_dest_id.id,
                                    'location_dest_id': product.location_dest_id.id,
                                    })]})

                else:
                    stock_lot_number = self.env['serial.lot.number'].create(vals_create)
                    if product.product_id.tracking == 'serial':
                        for qty in range(int(product.product_uom_qty)):
                            stock_lot_number.write({'stock_lot_line_ids': [
                                (0, 0, {'product_id': product.product_id.id,
                                        'quantity': 1,
                                        'location_id': product.location_id.id,
                                        'check_lot_number': check_lot_number,
                                        'main_product': True,
                                        'source_location_id': product.location_dest_id.id,
                                        'location_dest_id': product.location_dest_id.id,
                                        })]})
                    elif product.product_id.tracking == 'lot':
                        stock_lot_number.write({'stock_lot_line_ids': [
                            (0, 0, {'product_id': product.product_id.id,
                                    'quantity': product.product_uom_qty,
                                    'location_id': product.location_id.id,
                                    'check_lot_number': check_lot_number,
                                    'main_product': True,
                                    'source_location_id': product.location_dest_id.id,
                                    'location_dest_id': product.location_dest_id.id,
                                    })]})
            #stock_product_id.split_quantities()
            for line in stock_lot_number.stock_lot_line_ids:
                line.generate_lot_number()
            res = {
                'type': 'ir.actions.act_window',
                'name': _('Customer Serial Number'),
                'res_model': 'serial.lot.number',
                'res_id': stock_lot_number.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'new',

            }
        else :

            #stock_product_id.split_quantities()
            for line in stock_product_id.stock_lot_line_ids:
                line.generate_lot_number()
            res = {
                'type': 'ir.actions.act_window',
                'name': _('Customer Serial Number'),
                'res_model': 'serial.lot.number',
                'res_id': stock_product_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'target': 'new',

            }
        return res

    def get_width(self):
        obj = self.env['label.size'].search([])
        return str(obj.width)

    def get_height(self):
        obj = self.env['label.size'].search([])
        return str(obj.height)
