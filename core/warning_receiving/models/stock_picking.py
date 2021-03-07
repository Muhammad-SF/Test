from odoo import models, fields, api, _,exceptions
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ignore_qty = fields.Boolean('Ignore Qty', default=False)

    @api.model
    def _purchase_qty_message_content(self):
        title = _('Some products in %s has been received with Qty is less or more than initial demand.') % (
            self.name)
        message = '<h3>%s</h3>' % title
        message += _('The following items are:')
        message += '<ul>'
        for line in self.pack_operation_product_ids:
            purchase_order_lines = self.purchase_id.order_line
            tmp_line = None
            for order_line in purchase_order_lines:
                if order_line.product_id.id == line.product_id.id:
                    tmp_line = order_line


            if line.qty_done > line.product_qty or line.qty_done < line.product_qty:
                message += _(
                    '<li><b>%s</b> Initial Demand:<b>%s</b> Received Qty:<b>%s</b></li>'
                ) % (line.product_id.name, tmp_line.product_qty, tmp_line.qty_received + line.qty_done
                     )
            message += '</ul>'
        return message

    @api.multi
    def do_new_transfer(self):
        flag=False
        for line in self.pack_operation_product_ids:
            if line.qty_done > line.ordered_qty:
                flag=True
                message = self._purchase_qty_message_content()
                break
        if flag == True and not self.ignore_qty:
            view = (self.env.ref('warning_receiving.purchase_qty_warning_popup_view')).id
            return {
                'name': 'Warning',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.qty.warning.wiz',
                'view_id': view,
                'target': 'new',
                'context': {'default_warning_msg': message},
                'type': 'ir.actions.act_window',
            }
        else:
            return super(StockPicking, self).do_new_transfer()


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    warning_msg = fields.Html(string='Message', readonly=True)

    @api.one
    def _process(self, cancel_backorder=False):
        self.pick_id.update({'ignore_qty': False})
        return super(StockBackorderConfirmation,self)._process(cancel_backorder=cancel_backorder)

    @api.multi
    def process_cancel_backorder(self):
        message = self.pick_id._purchase_qty_message_content()
        view = (self.env.ref('warning_receiving.purchase_qty_warning_popup_view_2')).id
        return {
            'name': 'Warning',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.qty.warning.wiz',
            'view_id': view,
            'target': "new",
            'context': {'default_warning_msg': message},
            'type': 'ir.actions.act_window',
        }

