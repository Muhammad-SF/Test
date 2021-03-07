# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import Warning as UserError
from odoo.tools.translate import _


class SaleOrderMerge(models.TransientModel):
    _name = 'sale.order.merge'
    _description = 'Merge sale orders'

    sale_order = fields.Many2one(
        'sale.order', 'Merge into', required=True, readonly=True)
    mergeable = fields.Many2many(
        comodel_name='sale.order',
        related='sale_order.merge_with')
    to_merge = fields.Many2many(
        'sale.order', 'rel_sale_to_merge', 'sale_id', 'to_merge_id',
        'Orders to merge')
    keep_references = fields.Boolean('Keep references from original invoices',
                                     default=True)
    date_invoice = fields.Date('Invoice Date')

    @api.multi
    def merge_order_lines(self):
        self.sale_order.write({
            'order_line': [
                (4, line.id)
                for line in self.to_merge.mapped('order_line')
            ]})

    @api.multi
    def merge_invoices(self):
        """To merge similar type of account invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: account invoice action
        """
        inv_obj = self.env['account.invoice']
	aw_obj = self.env['ir.actions.act_window']
	ids = self.sale_order.invoice_ids.ids
	for invoice in (self.sale_order.invoice_ids + self.to_merge.mapped('invoice_ids')):
		allinvoices = invoice.do_merge()
		xid = {
		    'out_invoice': 'action_invoice_tree1',
		    'out_refund': 'action_invoice_tree1',
		    'in_invoice': 'action_invoice_tree2',
		    'in_refund': 'action_invoice_tree2',
		}[invoice.type]
		action = aw_obj.for_xml_id('account', xid)
		action.update({
		    'domain': [('id', 'in', ids + allinvoices.keys())],
		})
		return action

    @api.multi
    def _picking_can_merge(self, picking):
        return (picking.state not in ('done', 'cancel') and
                picking.location_dest_id.usage == 'customer')

    @api.multi
    def _get_picking_map_key(self, picking):
        return (picking.picking_type_id, picking.location_id,
                picking.location_dest_id, picking.partner_id)

    @api.multi
    def merge_pickings(self):
        """ Assign all pickings to the target sale order and merge any
        pending pickings """
        orders = self.sale_order + self.to_merge
        group = self.env['procurement.group']
        if self.sale_order.procurement_group_id:
            group = self.sale_order.procurement_group_id
        else:
            for order in self.to_merge:
                if order.procurement_group_id:
                    group = order.procurement_group_id
                    break
            else:
                return  # no group, no pickings
            self.sale_order.write({'procurement_group_id': group.id})
        other_groups = orders.mapped('procurement_group_id')
        self.env['stock.picking'].search(
            [('group_id', 'in', other_groups.ids)]).write(
                {'group_id': group.id})
        self.env['stock.move'].search(
            [('group_id', 'in', other_groups.ids)]).write(
                {'group_id': group.id})
        self.env['procurement.order'].search(
            [('group_id', 'in', other_groups.ids)]).write(
                {'group_id': group.id})
        pick_map = {}
        for picking in self.sale_order.picking_ids:
            if self._picking_can_merge(picking):
                key = self._get_picking_map_key(picking)
                if key not in pick_map:
                    pick_map[key] = self.env['stock.picking']
                pick_map[key] += picking
            else:
                picking.write({'origin': group.name})
        for pickings in pick_map.values():
            target = pickings[0]
            if len(pickings) > 1:
                pickings -= target
                pickings.mapped('move_lines').write({'picking_id': target.id})
		pickings.mapped('pack_operation_product_ids').write({'picking_id': target.id})
                pickings.unlink()
            target.write({'origin': group.name})
        return True

    @api.multi
    def open_sale(self):
        self.ensure_one()
        return {
            'name': _('Merged sale order'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.sale_order.id,
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def merge(self):
        self.ensure_one()
        orders = self.sale_order + self.to_merge
        create_picking = False
        reset_wait_invoice = False
        if not all(order.state in ('sent', 'draft') for order in orders):
            drafts = orders.filtered(
                lambda o: o.state in ('sent', 'draft'))
            confirmed = orders - drafts
            for draft in drafts:
                draft.action_confirm()
            self.merge_invoices()
            self.merge_pickings()

        self.merge_order_lines()
        self.to_merge.write({'state': 'cancel'})
        for order in self.to_merge:
            order.message_post(_('Merged into %s') % self.sale_order.name)
        self.sale_order.message_post(
            _('Order(s) %s merged into this one') % ','.join(
                self.to_merge.mapped('name')))
        return self.open_sale()
