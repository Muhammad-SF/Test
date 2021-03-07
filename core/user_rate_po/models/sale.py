# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from lxml import etree

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rate_type = fields.Selection([('c1', 'Corporate Rate'), ('u1', 'User Rate')], default='c1')
    c1_rate = fields.Float(string='Corporate Rate', compute='_compute_c1_rate', store=True)
    u1_rate = fields.Float(string='User Rate')
    check_currency = fields.Boolean(compute='_compute_check_currency', store=True)

    @api.depends('pricelist_id', 'pricelist_id.currency_id', 'company_id', 'company_id.currency_id')
    def _compute_check_currency(self):
        for record in self:
            if record.pricelist_id.currency_id.id == record.company_id.currency_id.id:
                record.check_currency = True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Hide/Show 'Rate type, Corporate and User rates' fields of SO form view according to sale.config.settings's 'Activate User Rate For SO' field. """
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        dom = etree.XML(res['arch'])
        is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
        if is_user_rate_so == False:
            for node in dom.xpath("//field[@name='rate_type']"):
                node.set("modifiers", '{"invisible":true}')
            for node in dom.xpath("//field[@name='c1_rate']"):
                node.set("modifiers", '{"invisible":true}')
            for node in dom.xpath("//field[@name='u1_rate']"):
                node.set("modifiers", '{"invisible":true}')
            res['arch'] = etree.tostring(dom)
        return res

    @api.depends('rate_type', 'date_order', 'pricelist_id', 'pricelist_id.currency_id')
    def _compute_c1_rate(self):
        for record in self.filtered(lambda x: x.pricelist_id.currency_id and x.rate_type == 'c1'):
            record.c1_rate = record.with_context({'date': record.date_order}).pricelist_id.currency_id.conversion

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
        if is_user_rate_so == True:
            if self.rate_type:
                invoice_vals['rate_type'] = self.rate_type
                if self.rate_type == 'c1':
                    invoice_vals['c1_rate'] = self.c1_rate
                else:
                    invoice_vals['u1_rate'] = self.u1_rate
            if self.pricelist_id and self.pricelist_id.currency_id:
                invoice_vals['currency_id'] = self.pricelist_id.currency_id.id
        return invoice_vals

SaleOrder()