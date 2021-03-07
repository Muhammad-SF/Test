from odoo import models, fields, api,exceptions,_

class prl_make_rfq(models.TransientModel):
    _inherit = 'purchase.request.line.make.purchase.order'

    @api.multi
    def make_purchase_order(self):
        for item in self.item_ids:
            if item.line_id.branch_id.id != self.item_ids[0].line_id.branch_id.id:
                raise exceptions.Warning(_('Branch of purchase request line should be same.'))
        return super(prl_make_rfq,self).make_purchase_order()

    @api.model
    def _prepare_purchase_order(self, picking_type, location, company_id):
        # checking all lines then create PR lines inside the PO
        if not self.supplier_id:
            raise exceptions.Warning(_('Enter a supplier.'))
        supplier = self.supplier_id
        supplier_pricelist = supplier.property_product_pricelist or False
        data = {
            'origin': '',
            'partner_id': self.supplier_id.id,
            'pricelist_id': supplier_pricelist.id,
            'location_id': location.id,
            'fiscal_position_id': (supplier.property_account_position_id and supplier.property_account_position_id.id) or False,
            'payment_term_id': supplier.property_supplier_payment_term_id and supplier.property_supplier_payment_term_id.id or 0,
            'picking_type_id': picking_type.id,
            'company_id': company_id,
        }
        if self.env.context.get('active_model',False) == 'purchase.request.line' and self.env.context.get('active_ids',False):
            line = self.env['purchase.request.line'].browse(self.env.context.get('active_ids',False))
            data.update({'branch_id': line.mapped('requested_by') and line.mapped('requested_by')[0].branch_id.id or False })
        return data