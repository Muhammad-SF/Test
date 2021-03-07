from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseDirect(models.Model):
    _inherit = 'purchase.order'

    is_purchase_direct = fields.Boolean(string = "Purchase Direct")
    default_payment_journal = fields.Many2one('account.journal', string='Payment Journal',
                                              help="Need to provide Account Journal for Purchase Direct.",
                                              domain="[('type', 'in', ['cash', 'bank'])]")
 
    @api.onchange('partner_id')
    def onchange_uom(self):
        self.default_payment_journal = self.partner_id.default_payment_journal

    @api.model
    def create(self, vals):
        # Remove duplicate values for message_follower_ids
        vals['message_follower_ids'] = False
        res = super(PurchaseDirect, self).create(vals)
        if vals.get("is_purchase_direct") is True:
            res.name = self.env['ir.sequence'].next_by_code('purchase.direct')
        else:
            pass
        return res

    @api.multi
    def button_approve(self, force=False):
        res = super(PurchaseDirect, self).button_approve()
        if self.is_purchase_direct:
            #Creating and completing shipment
            for picking in self.picking_ids:
                if picking.state == 'assigned':
                    if picking.pack_operation_ids:
                        for pack in picking.pack_operation_ids:
                            if pack.product_qty > 0:
                                pack.write({'qty_done': pack.product_qty})
                    if picking.pack_operation_product_ids:
                        for pack in picking.pack_operation_product_ids:
                            if pack.product_qty > 0:
                                pack.write({'qty_done': pack.product_qty})
                    picking.do_transfer()
            # Creating and Payment done for invoice
            for invoice in self.invoice_ids.filtered(lambda x: x.state in ['proforma2', 'draft']):
                invoice.with_context(from_kp=True).action_invoice_open()
                if not self.default_payment_journal:
                    raise UserError(_('No account found for this Vendor. \n Please configure Account first.'))
                else:
                    invoice.pay_and_reconcile(pay_journal = self.default_payment_journal)
        else:
            pass
        # 2/0
        return res

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        item = super(AccountMoveLine, self).create(vals)
        return item

class AccountInvoiceModification(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        item = super(AccountInvoiceModification, self).create(vals)
        return item

    @api.multi
    def write(self, vals):
        if self:
            pass
        res = super(AccountInvoiceModification, self).write(vals)
        return res

    @api.multi
    def action_move_create(self):
        if self.env.context and self.env.context.get('from_kp'):
            for rec in self:
                seq = self.env['ir.sequence'].search([('name', '=', 'Vendor Bills')])
                rec.journal_id.sequence_id = seq.id

        res = super(AccountInvoiceModification, self).action_move_create()
        return res

