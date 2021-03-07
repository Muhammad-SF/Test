# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _purchase_qty_received_content(self, line):
        title = _('Some products in purchase order has been received with Qty is less or more than initiprocesal demand.')
        # for line in self:
        message = '<h3>%s</h3>' % title
        message += _('The following items from Purchase Order %s '
                     'have Qty more/less than purchasing qty:') % (
                       line.order_id.name)
        message += '<ul>'
        if line.qty_received > line.product_qty or line.qty_received < line.product_qty:
            message += _(
                '<li><b>%s</b> Initial Demand:<b>%s</b> Received Qty:<b>%s</b></li>'
            ) % (line.product_id.name, line.product_qty, line.qty_received)
        message += '</ul>'
        return message

    @api.onchange('qty_received')
    def on_change_qty_received(self):
        Flag=False
        for line in self:
            if line.qty_received > line.product_qty or line.qty_received < line.product_qty:
                Flag=True
        if Flag:
            message = self._purchase_price_cost_message_content()
            channel = self.env['mail.channel'].search([('name','=','general')],limit=1)
            mail_message=self.env['mail.message'].create({
                'body': message,
                'channel_ids': [(6, 0, [channel.id])],
                'message_type': 'comment',
                'subtype_id': 1,
                'author_id':self.order_id.partner_id.id,
                'origin': self.order_id.id,
                'res_id': self.order_id.id,
                'user_id':self.env.user.id,
                'model': self.order_id._name,
                'needaction_partner_ids': [(4, self.order_id.partner_id.id)],
            })

    @api.depends('order_id.state', 'move_ids.state')
    def _compute_qty_received(self):
        res = super(PurchaseOrderLine,self)._compute_qty_received()
        for rec in self:
            Flag = False
            message=False
            if rec.qty_received:
                if rec.qty_received > rec.product_qty or rec.qty_received < rec.product_qty:
                    message= self._purchase_qty_received_content(rec)
                    Flag = True
            if Flag:
                channel = self.env['mail.channel'].search([('name', '=', 'general')], limit=1)
                mail_message = self.env['mail.message'].create({
                    'body': message,
                    'channel_ids': [(6, 0, [channel.id])],
                    'message_type': 'comment',
                    'subtype_id': 1,
                    'author_id': rec.order_id.partner_id.id,
                    'origin': rec.order_id.id,
                    'res_id': rec.order_id.id,
                    'user_id': self.env.user.id,
                    'model': 'purchase.order',
                })
        return res


