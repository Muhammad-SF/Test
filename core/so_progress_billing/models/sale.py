from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    retention_per = fields.Float(string='Retention %')
    total_invoiced_per = fields.Float('Total Invoiced Percentage')
    total_invoice_amount_paid = fields.Float('Total Amount Paid')
    total_down_payment_paid = fields.Float('Total Down Payment Amount Paid')

    @api.onchange('retention_per')
    def _onchange_retention_per(self):
        warning = {}
        for rec in self:
            if rec.retention_per and (rec.retention_per < 0 or rec.retention_per > 100):
                warning = {'title': 'Value Error', 'message': "Please input between 0 to 100% in Retention %."}
        return {'warning': warning}

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')

        if 'retention_per' and vals.get('retention_per'):
            retention_per = int(vals.get('retention_per'))
            if retention_per < 0 or retention_per > 100:
                raise UserError(_("Please input between 0 to 100% in Retention %."))

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        return result

    @api.multi
    def write(self, values):
        order = super(SaleOrder, self).write(values)
        if order:
            for rec in self:
                if rec.retention_per and (rec.retention_per < 0 or rec.retention_per > 100):
                    raise UserError(_("Please input between 0 to 100% in Retention %."))
        return order
