from odoo import models, fields, api


class Invoice(models.Model):
    _inherit = "account.invoice"

    state = fields.Selection(selection_add=[('overpaid', 'Overpaid')])


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def post(self):
        res =  super(AccountPayment, self).post()
        invoice_id = self._context.get('active_ids', False)
        invoice_obj = self.env['account.invoice']
        for rec in self:
            if rec.payment_difference_handling == 'reconcile':
                if invoice_id:
                    invoice_rec = invoice_obj.search([('id','=', invoice_id[0]),('type','=','in_invoice')])
                    if invoice_rec: invoice_rec.state = 'overpaid'
        return res