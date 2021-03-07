from odoo import models,fields,api,_
from datetime import date

class PurchaseQtyQarning(models.TransientModel):
    _name = 'purchase.qty.warning.wiz'


    warning_msg = fields.Html(string='Message',readonly=True)

    @api.multi
    def approve_order(self):
        order_id = self.env['stock.picking'].search([('id', 'in', self._context.get('active_ids'))], limit=1)
        if order_id:
            order_id.update({'ignore_qty': True})
            return order_id.do_new_transfer()

    @api.multi
    def approve_no_backorder(self):
        """

        :return:
        """
        backorder = self.env['stock.backorder.confirmation'].search([('id', 'in', self._context.get('active_ids'))],
                                                                    limit=1)
        if len(backorder):
            return backorder._process(cancel_backorder=True)
