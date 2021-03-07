from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class serial_lot_number(models.Model):
    _name = 'serial.lot.number'

    serial_name = fields.Char(string='Name')
    stock_lot_line_ids = fields.One2many('serial.lot.product', 'lot_id', string="Stock Moves")

    @api.multi
    def wizard_view(self):
        view = self.env.ref('warehouse_serializer.view_form_serial_lot')

        return {
            'name': _('Enter transfer details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'serial.lot.number',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }

    @api.multi
    def write(self, vals):
        res = super(serial_lot_number, self).write(vals)
        picking_id = self.env['stock.picking'].search([('name', '=', self.serial_name)])

        lists = []
        for stock_lot in self.stock_lot_line_ids:
            if not lists:
                lists.append({'name': stock_lot.product_id.name, 'qty': stock_lot.quantity})
            else:
                if stock_lot.product_id.name not in [line.get('name') for line in lists]:
                    lists.append({'name': stock_lot.product_id.name, 'qty': stock_lot.quantity})
                else:
                    for list in lists:
                        if list.get('name') == stock_lot.product_id.name:
                            list.update({'qty': list.get('qty') + stock_lot.quantity})
                            break

        for product in picking_id.pack_operation_product_ids:
            for list in lists:
                if product.product_id.name == list.get('name'):
                    if product.product_id.tracking == 'lot':
                        if product.product_qty != list.get('qty'):
                            raise UserError(_('%s Product quantity should be same as a picking product quantity')% product.product_id.name)

        for stock_lot in self.stock_lot_line_ids:
            for pack_operantion_id in picking_id.pack_operation_product_ids:
                if pack_operantion_id.product_id.name == stock_lot.product_id.name:
                    for pack_lot_id in pack_operantion_id.pack_lot_ids:
                        if pack_lot_id.lot_name == stock_lot.lot_serial_number:
                            pack_lot_id.write({'qty':stock_lot.quantity})
                            #lot/serial number
                            stock_production_id = self.env['stock.production.lot'].search([('name', '=', pack_lot_id.lot_name)])
                            for quant_id in stock_production_id.quant_ids:
                                if quant_id.lot_id.name == pack_lot_id.lot_name:
                                    quant_id.write({'qty': stock_lot.quantity})
                    done_quantity = 0
                    for pack_lot_id in pack_operantion_id.pack_lot_ids:
                        done_quantity = done_quantity + pack_lot_id.qty
                    pack_operantion_id.write({'qty_done': done_quantity})

        return res


class serial_lot_product(models.Model):
    _name = 'serial.lot.product'
    _order = 'lot_serial_number desc'

    lot_id = fields.Many2one('serial.lot.number', string='Lot number')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')
    check_lot_number = fields.Boolean('Check lot', default=False)
    lot_serial_number = fields.Char('Lot serial Number')
    main_product = fields.Boolean('Main Product')
    source_location_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one('stock.location', 'Source Destination')


    @api.multi
    def unlink(self):
        picking_id = self.env['stock.picking'].search([('name', '=', self.lot_id.serial_name)])
        for pack_operantion_id in picking_id.pack_operation_product_ids:
            if pack_operantion_id.product_id.name == self.product_id.name:
                for pack_lot_id in pack_operantion_id.pack_lot_ids:
                    if pack_lot_id.lot_name == self.lot_serial_number:
                        pack_lot_id.unlink()


        return super(serial_lot_product, self).unlink()


    # @api.onchange('quantity', 'check_lot_serial')
    # def _check_quantity_tracking(self):
    #     picking_id = self.env['stock.picking'].search([('name', '=', self.lot_id.serial_name)])
    #     stock_lot = self.env['serial.lot.number'].search([('serial_name', '=', self.lot_id.serial_name)])
    #     stock_production_id = self.env['stock.production.lot'].search([('name', '=', self.lot_id.serial_name)])
    #
    #     picking_qty = 0
    #     for move_line in picking_id.move_lines:
    #         if move_line.product_id.name == self.product_id.name:
    #             picking_qty += move_line.product_uom_qty
    #     stock_qty = 0
    #     for stock_lot in stock_lot.stock_lot_line_ids:
    #         if stock_lot.product_id.name == self.product_id.name:
    #             stock_qty += stock_lot.quantity
    #
    #         if self._origin.id == stock_lot.id:
    #
    #             stock_qty -= stock_lot.quantity
    #             stock_qty += self.quantity
    #             if stock_qty > picking_qty:
    #                 raise UserError(_('Quantity is more then picking product quantity'))
    #
    #
    #     if self.product_id.tracking == 'lot':
    #         for pack_operantion_id in picking_id.pack_operation_product_ids:
    #             if pack_operantion_id.product_id.name == self.product_id.name:
    #                 for pack_lot_id in pack_operantion_id.pack_lot_ids:
    #                     if pack_lot_id.lot_name == self.lot_serial_number:
    #                         pack_operantion_id.write(
    #                             {'qty_done': pack_operantion_id.qty_done + self.quantity,
    #                              'pack_lot_ids': [(1, pack_lot_id.id, {
    #                                  'qty': self.quantity,
    #                              })]})
    #                     if stock_production_id:
    #                         stock_production_id.write()
    #                 done_quantity = 0
    #                 for pack_lot_id in pack_operantion_id.pack_lot_ids:
    #                     done_quantity = done_quantity + pack_lot_id.qty
    #                 pack_operantion_id.write({'qty_done': done_quantity})
    #         print "1111111111",self._origin[0]
    #         print "1111111111",self._origin
    #     if self._origin.id and self._origin[0].id:
    #         print ">>>>>>>>>>>>>",self._origin[0].lot_id.wizard_view()
    #         return self._origin[0].lot_id.wizard_view()


    @api.multi
    def split_quantities(self):

        picking_id = self.env['stock.picking'].search([('name', '=', self.lot_id.serial_name)])

        if self.product_id.tracking == 'serial':
            product_category = self.product_id.categ_id

            product_sku_serializer_id = self.env['lot.number.serializer'].search(
                [('product_categ_id', '=', product_category.id)])
            ## did customisation for the auto assign lot
            # and deduct qty when we split it from stock.product.lot
            # if self.lot_serial_number:
            #    print "#########"
            #    qunts = self.env['stock.quant'].search(
            #        [('lot_id.name', '=', self.lot_serial_number)])
            #    if qunts:
            #        qunts.qty -= 1
            # End

            # if self.quantity == 2.00:
            #     prefix_sku = product_sku_serializer_id.prefix_sku
            #     current_number = int(product_sku_serializer_id.current_number) + 1
            #
            #     sequence = str(current_number).zfill(product_sku_serializer_id.digits)
            #
            #     suffix_sku = product_sku_serializer_id.suffix_sku
            #     serialize_sequence = prefix_sku + sequence + suffix_sku
            #     product_sku_serializer_id.current_number = sequence
            #
            #     self.write({'lot_serial_number': serialize_sequence})
            #
            #     production_lot_id = self.env['stock.production.lot'].create(
            #         {'name': serialize_sequence, 'product_id': self.product_id.id, 'quant_ids': [(0, 0, {
            #             'product_id': self.product_id.id,
            #             'location_id': self.location_dest_id.id,
            #             'qty': 1.00,
            #         })]})
            #     lot_id = self.env['stock.pack.operation.lot'].create(
            #         {'lot_id': production_lot_id.id, 'lot_name': production_lot_id.name,
            #          'qty': production_lot_id.product_qty})
            #
            #     for pack_operantion_id in picking_id.pack_operation_product_ids:
            #         if pack_operantion_id.product_id.name == self.product_id.name:
            #             pack_operantion_id.write(
            #                 {'qty_done': pack_operantion_id.qty_done + 1, 'pack_lot_ids': [(0, 0, {
            #                     'lot_id': production_lot_id.id,
            #                     'lot_name': production_lot_id.name,
            #                     'qty': lot_id.qty,
            #                 })]})

            if product_sku_serializer_id:
                self.quantity = self.quantity - 1
                prefix_sku = product_sku_serializer_id.prefix_lot
                current_number = int(product_sku_serializer_id.current_number) + 1

                sequence = str(current_number).zfill(product_sku_serializer_id.digits)

                suffix_sku = product_sku_serializer_id.suffix_lot

                if product_sku_serializer_id.start_with_sku == True and self.product_id.default_code:
                    serialize_sequence = self.product_id.default_code + '_' + prefix_sku + sequence + suffix_sku
                else:
                    serialize_sequence = prefix_sku + sequence + suffix_sku

                # serialize_sequence = prefix_sku + sequence + suffix_sku
                product_sku_serializer_id.current_number = sequence
                self.lot_id.write({'stock_lot_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                                                  'quantity': '1',
                                                                  'source_location_id': self.location_dest_id.id,
                                                                  'lot_serial_number': serialize_sequence,
                                                                  'location_dest_id': self.location_dest_id.id,
                                                                  })]})

                production_lot_id = self.env['stock.production.lot'].create(
                    {'name': serialize_sequence, 'product_id': self.product_id.id,
                    #     'quant_ids': [(0, 0, {
                    #     'product_id': self.product_id.id,
                    #     'location_id': self.location_dest_id.id,
                    #     'qty': 1.00,
                    # })]
                     })
                lot_id = self.env['stock.pack.operation.lot'].create(
                    {'lot_id': production_lot_id.id, 'lot_name': production_lot_id.name,
                     'qty': 1.00})

                for pack_operantion_id in picking_id.pack_operation_product_ids:
                    if pack_operantion_id.product_id.name == self.product_id.name:
                        pack_operantion_id.write(
                            {'qty_done': pack_operantion_id.qty_done + 1, 'pack_lot_ids': [(0, 0, {
                                'lot_id': production_lot_id.id,
                                'lot_name': production_lot_id.name,
                                'qty': lot_id.qty,
                            })]})
            else:
                raise UserError(_('First create serial number'))

        elif self.product_id.tracking == 'lot':

            self.quantity = self.quantity - 1

            if self.main_product == True:
                self.write({'check_lot_number': True})

            product_category = self.product_id.categ_id

            lot_number_serializer_id = self.env['lot.number.serializer'].search(
                [('product_categ_id', '=', product_category.id)])

            ## did customisation for the auto assign lot
            # and deduct qty when we split it from stock.product.lot
            # if self.lot_serial_number:
            #    print "#########"
            #    qunts = self.env['stock.quant'].search(
            #        [('lot_id.name', '=', self.lot_serial_number)])
            #    print "EEEEEEEEEEEEEEEe", qunts
            #    if qunts:
            #        qunts.qty -= 1
            ## End
            if lot_number_serializer_id:
                prefix_lot = lot_number_serializer_id.prefix_lot
                current_number = int(lot_number_serializer_id.current_number) + 1
                suffix_lot = lot_number_serializer_id.suffix_lot

                sequence = str(current_number).zfill(lot_number_serializer_id.digits)
                if lot_number_serializer_id.start_with_sku == True:
                    if self.product_id.default_code:
                        serialize_sequence = self.product_id.default_code + '_' + prefix_lot + sequence + suffix_lot
                    else:
                        serialize_sequence = prefix_lot + sequence + suffix_lot
                else:
                    serialize_sequence = prefix_lot + sequence + suffix_lot

                lot_number_serializer_id.current_number = sequence

                self.lot_id.write({'stock_lot_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                                                  'quantity': '1',
                                                                  'source_location_id': self.location_dest_id.id,
                                                                  'lot_serial_number': serialize_sequence,
                                                                  'location_dest_id': self.location_dest_id.id,
                                                                  })]})

                lot_id = self.env['stock.pack.operation.lot'].search([('lot_name', '=', self.lot_serial_number)])

                lot_id.write({'qty': self.quantity})

                production_lot_id = self.env['stock.production.lot'].create(
                    {'name': serialize_sequence, 'product_id': self.product_id.id,
                    #     'quant_ids': [(0, 0, {
                    #     'product_id': self.product_id.id,
                    #     'location_id': self.location_dest_id.id,
                    #     'qty': '1',
                    # })]
                     })

                lot_id = self.env['stock.pack.operation.lot'].create(
                    {'lot_id': production_lot_id.id, 'lot_name': production_lot_id.name,
                     'qty': self.quantity})

                for pack_operantion_id in picking_id.pack_operation_product_ids:

                    if pack_operantion_id.product_id.name == self.product_id.name:

                        pack_operantion_id.write(
                            {'qty_done': pack_operantion_id.qty_done + 1, 'pack_lot_ids': [(0, 0, {
                                'lot_id': production_lot_id.id,
                                'lot_name': production_lot_id.name,
                                'qty': 1.00,
                            })]})
                        price = 0
                        for lot_qty in pack_operantion_id.pack_lot_ids:
                            price = price + lot_qty.qty
                        pack_operantion_id.write(
                            {'qty_done': price})

            else:
                raise UserError(_('First create lot serial number'))


        elif self.product_id.tracking == 'none':
            raise UserError(_('You can not select the tracking for the Product'))

        if self and self[0]:
            return self[0].lot_id.wizard_view()

    @api.multi
    def generate_lot_number(self):
        picking_id = self.env['stock.picking'].search([('name', '=', self.lot_id.serial_name)])
        product_category = self.product_id.categ_id
        if (self.lot_serial_number == '') or (self.lot_serial_number == False):
            if self.product_id.tracking == 'serial':
                product_sku_serializer_id = self.env['lot.number.serializer'].search(
                    [('product_categ_id', '=', product_category.id)])
                if product_sku_serializer_id:
                    prefix_sku = product_sku_serializer_id.prefix_lot
                    current_number = int(product_sku_serializer_id.current_number) + 1

                    sequence = str(current_number).zfill(product_sku_serializer_id.digits)

                    suffix_sku = product_sku_serializer_id.suffix_lot

                    if product_sku_serializer_id.start_with_sku == True and self.product_id.default_code:
                        serialize_sequence = self.product_id.default_code + '_' + prefix_sku + sequence + suffix_sku
                    else:
                        serialize_sequence = prefix_sku + sequence + suffix_sku
                    product_sku_serializer_id.current_number = sequence
                    self.write({'lot_serial_number': serialize_sequence})
                    production_lot_id = self.env['stock.production.lot'].create(
                        {'name': serialize_sequence, 'product_id': self.product_id.id,
                         })
                    lot_id = self.env['stock.pack.operation.lot'].create(
                        {'lot_id': production_lot_id.id, 'lot_name': production_lot_id.name,
                         'qty': 1.00})

                    for pack_operantion_id in picking_id.pack_operation_product_ids:
                        if pack_operantion_id.product_id.name == self.product_id.name:
                            pack_operantion_id.write(
                                {'qty_done': pack_operantion_id.qty_done + 1, 'pack_lot_ids': [(0, 0, {
                                    'lot_id': production_lot_id.id,
                                    'lot_name': production_lot_id.name,
                                    'qty': 1.00,
                                })]})
                else:
                    raise UserError(_('First create Product SKU Serializer'))
            elif self.product_id.tracking == 'lot':
                lot_number_serializer_id = self.env['lot.number.serializer'].search(
                    [('product_categ_id', '=', product_category.id)])

                if lot_number_serializer_id:
                    prefix_lot = lot_number_serializer_id.prefix_lot
                    current_number = int(lot_number_serializer_id.current_number) + 1
                    suffix_lot = lot_number_serializer_id.suffix_lot

                    sequence = str(current_number).zfill(lot_number_serializer_id.digits)
                    if lot_number_serializer_id.start_with_sku == True:
                        if self.product_id.default_code:
                            serialize_sequence = self.product_id.default_code + '_' + prefix_lot + sequence + suffix_lot
                        else:
                            serialize_sequence = prefix_lot + sequence + suffix_lot
                    else:
                        serialize_sequence = prefix_lot + sequence + suffix_lot

                    lot_number_serializer_id.current_number = sequence

                    self.write({'lot_serial_number': serialize_sequence})

                    production_lot_id = self.env['stock.production.lot'].create(
                        {'name': serialize_sequence, 'product_id': self.product_id.id,
                         #     'quant_ids': [(0, 0, {
                         #     'product_id': self.product_id.id,
                         #     'location_id': self.location_dest_id.id,
                         #     'qty': self.quantity,
                         # })]
                         })
                    lot_id = self.env['stock.pack.operation.lot'].create(
                        {'lot_id': production_lot_id.id, 'lot_name': production_lot_id.name,
                         'qty': self.quantity})

                    for pack_operantion_id in picking_id.pack_operation_product_ids:
                        if pack_operantion_id.product_id.name == self.product_id.name:

                            pack_operantion_id.write(
                                {'qty_done': pack_operantion_id.qty_done + lot_id.qty,
                                 'pack_lot_ids': [(0, 0, {
                                     'lot_id': production_lot_id.id,
                                     'lot_name': production_lot_id.name,
                                     'qty': self.quantity,
                                 })]
                                 })
                else:
                    raise UserError(_('First create Batch/lot Number serializer'))
            if self and self[0]:
                return self[0].lot_id.wizard_view()
        else:
            if self and self[0]:
                return self[0].lot_id.wizard_view()
            raise UserError(_('Serializer number already generated'))

class stock_quant(models.Model):

    _inherit = 'stock.quant'


    @api.model
    def quants_move(self, quants, move, location_to, location_from=False, lot_id=False, owner_id=False,
                    src_package_id=False, dest_package_id=False, entire_pack=False):
        """Moves all given stock.quant in the given destination location.  Unreserve from current move.
        :param quants: list of tuple(browse record(stock.quant) or None, quantity to move)
        :param move: browse record (stock.move)
        :param location_to: browse record (stock.location) depicting where the quants have to be moved
        :param location_from: optional browse record (stock.location) explaining where the quant has to be taken
                              (may differ from the move source location in case a removal strategy applied).
                              This parameter is only used to pass to _quant_create_from_move if a negative quant must be created
        :param lot_id: ID of the lot that must be set on the quants to move
        :param owner_id: ID of the partner that must own the quants to move
        :param src_package_id: ID of the package that contains the quants to move
        :param dest_package_id: ID of the package that must be set on the moved quant
        """
        # TDE CLEANME: use ids + quantities dict
        if location_to.usage == 'view':
            raise UserError(_('You cannot move to a location of type view %s.') % (location_to.name))

        quants_reconcile_sudo = self.env['stock.quant'].sudo()
        quants_move_sudo = self.env['stock.quant'].sudo()
        check_lot = False
        for quant, qty in quants:
            if not quant:
                # If quant is None, we will create a quant to move (and potentially a negative counterpart too)
                quant = self._quant_create_from_move(
                    qty, move, lot_id=lot_id, owner_id=owner_id, src_package_id=src_package_id,
                    dest_package_id=dest_package_id, force_location_from=location_from, force_location_to=location_to)
                check_lot = True
            else:
                quant._quant_split(qty)
                quants_move_sudo |= quant
            quants_reconcile_sudo |= quant

        if quants_move_sudo:
            moves_recompute = quants_move_sudo.filtered(lambda self: self.reservation_id != move).mapped(
                'reservation_id')
            quants_move_sudo._quant_update_from_move(move, location_to, dest_package_id, lot_id=lot_id,
                                                     entire_pack=entire_pack)
            moves_recompute.recalculate_move_state()

        if location_to.usage == 'internal':
            # Do manual search for quant to avoid full table scan (order by id)
            self._cr.execute("""
                    SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                    ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
                """, (move.product_id.id, location_to.parent_left, location_to.parent_right, location_to.id))
            if self._cr.fetchone():
                quants_reconcile_sudo._quant_reconcile_negative(move)

        # In case of serial tracking, check if the product does not exist somewhere internally already
        # Checking that a positive quant already exists in an internal location is too restrictive.
        # Indeed, if a warehouse is configured with several steps (e.g. "Pick + Pack + Ship") and
        # one step is forced (creates a quant of qty = -1.0), it is not possible afterwards to
        # correct the inventory unless the product leaves the stock.
        picking_type = move.picking_id and move.picking_id.picking_type_id or False
        if check_lot and lot_id and move.product_id.tracking == 'serial' and (
            not picking_type or (picking_type.use_create_lots or picking_type.use_existing_lots)):
            #other_quants = self.search([('product_id', '=', move.product_id.id), ('lot_id', '=', lot_id),
             #                           ('qty', '>', 0.0), ('location_id.usage', '=', 'internal')])[0]
	    other_quants = self.search([('product_id', '=', move.product_id.id), ('lot_id', '=', lot_id),
                                        ('qty', '>', 0.0), ('location_id.usage', '=', 'internal')])

            if other_quants:
                # We raise an error if:
                # - the total quantity is strictly larger than 1.0
                # - there are more than one negative quant, to avoid situations where the user would
                #   force the quantity at several steps of the process

                if sum(other_quants.mapped('qty')) > 1.0 or len([q for q in other_quants.mapped('qty') if q < 0]) > 1:
                    lot_name = self.env['stock.production.lot'].browse(lot_id).name
                    raise UserError(_('The serial number %s is already in stock.') % lot_name + _(
                        "Otherwise make sure the right stock/owner is set."))
