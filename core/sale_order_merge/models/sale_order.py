# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    MERGE_STATES = ['draft', 'sent', 'sale']

    @api.multi
    @api.depends('merge_with')
    def _compute_merge_ok(self):
        for sale in self:
            sale.merge_ok = bool(sale.merge_with)

    @api.multi
    def _compute_merge_with(self):
        for sale in self:
    	    sale.merge_with = self.search([('merge_with', '=', sale.id)])

    @api.multi
    def _can_merge(self):
        """ Hook for redefining merge conditions """
        self.ensure_one()
        return self.state in self.MERGE_STATES and self.order_line

    @api.multi
    def _get_merge_domain(self):
        """ Hook for redefining merge conditions """
        return [
            ('id', '!=', self.id),
            ('partner_id', '=', self.partner_id.id),
            ('partner_shipping_id', '=', self.partner_shipping_id.id),
            ('warehouse_id', '=', self.warehouse_id.id),
            ('company_id', '=', self.company_id.id),
            ('state', 'in', self.MERGE_STATES),
        ]

    def _search_merge_with(self, op, arg):
        """ Apply criteria with which other sale orders the given order
        is mergeable. """
        if op != '=' and not arg or not isinstance(arg, (int, long)):
            return [('id', '=', False)]
        sale = self.browse(arg)
        if not sale._can_merge():
            return [('id', '=', False)]
        domain = sale._get_merge_domain()
        return [('id', 'in', self.search(domain).ids)]

    @api.multi
    def button_merge(self):
        self.ensure_one()
        merge_ids = self.search([('merge_with', '=', self.id)]).ids
        wizard = self.env['sale.order.merge'].create({
            'sale_order': self.id,
            'to_merge': [(6, 0, merge_ids)],
        })
        return {
            'name': _('Merge sale orders'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wizard.id,
            'res_model': 'sale.order.merge',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    merge_ok = fields.Boolean(
        'Has candidates to merge with',
        compute='_compute_merge_ok')
    merge_with = fields.Many2many(
        comodel_name='sale.order',
        compute='_compute_merge_with',
        search='_search_merge_with',
        string='Can be merged with')
