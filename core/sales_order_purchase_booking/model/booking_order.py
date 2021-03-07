from odoo import models, fields, api, _

class BookingOrder(models.Model):
    
    _inherit = "booking.order"

    purchase_ids = fields.One2many('purchase.order' , 'order_id', 'Purchase order')
    purchase_count = fields.Integer(string='Puchase Orders', compute='_compute_purchase_ids')

    @api.multi
    def action_view_purchase(self):
        purchase_ids = self.mapped('purchase_ids')
        return {
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', purchase_ids.ids)],
        }

    @api.multi
    @api.depends('purchase_ids')
    def _compute_purchase_ids(self):
        for order in self:
            order.purchase_count = len(order.purchase_ids.ids)

    @api.multi
    def action_create_purchase(self):
        ctx = dict(self.env.context or {})
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action.pop('id', None)
        ctx = {
            'default_order_id': self.id or False,
            'default_date_planned': fields.Datetime.now(),
        }
        purchase_ids = sum([order.purchase_ids.ids for order in self], [])
        action['context'] = ctx
        if len(purchase_ids) >= 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, purchase_ids)) + "])]"
        else:
            res = self.env.ref('purchase.purchase_order_form', False)
            action['views'] = [(res and res.id or False, 'form')]
        return action


class PurchaseOrder(models.Model):
    
    _inherit = "purchase.order"

    order_id = fields.Many2one('booking.order' , 'Booking Reference')