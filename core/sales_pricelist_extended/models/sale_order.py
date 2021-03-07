# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)])
    so_pricelist_id = fields.Many2one('product.pricelist',string='Invoicing Pricelist')
    is_approving = fields.Boolean(compute='compute_is_approving',string='Is Setting Approver',default=False)

    @api.onchange('partner_id')
    def onchange_customer(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            self.so_pricelist_id = False
            price_list_final = []
            price_list_final2 = []
            domain = {}
            for so in self:
                if so.partner_id and so.is_approving:
                    pricelist_ids = self.env['product.pricelist'].search([('state', '=', 'approved'), ('partner_id', '=', so.partner_id.id)])
                    if pricelist_ids:
                        for pricelist in pricelist_ids:
                            price_list_final = [pricelist.id for pricelist in pricelist_ids]
                        domain = {'so_pricelist_id': [('id', 'in', price_list_final)]}
                        return {'domain': domain}
                    else:
                        domain = {'so_pricelist_id': []}
                        return {'domain': domain}
                else:
                    pricelist_ids = self.env['product.pricelist'].search([('state', '=', 'confirmed')])
                    if pricelist_ids:
                        for pricelist in pricelist_ids:
                            price_list_final2 = [pricelist.id for pricelist in pricelist_ids]
                        domain = {'so_pricelist_id': [('id', 'in', price_list_final2)]}
                        return {'domain': domain}
                    else:
                        domain = {'so_pricelist_id': []}
                        return {'domain': domain}


    @api.model
    def default_get(self, field_list):
        result = super(SaleOrder, self).default_get(field_list)
        if self.env['ir.values'].get_default('sale.config.settings', 'is_approving_matrix'):
            result['is_approving'] = True
        else:
            result['is_approving'] = False
        return result

    @api.multi
    def compute_is_approving(self):
        if self.env['ir.values'].get_default('sale.config.settings', 'is_approving_matrix'):
            self.is_approving = True
        else:
            self.is_approving = False

SaleOrder()

