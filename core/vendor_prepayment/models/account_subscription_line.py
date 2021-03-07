from odoo import models, fields, api, _


class AccountSubscriptionLine(models.Model):
    _inherit = 'account.subscription.line'

    @api.multi
    def move_create(self):
        move_ids = super(AccountSubscriptionLine, self).move_create()
        for move in self.env['account.move'].browse(move_ids):
            if move.state == 'draft':
                move.post()
        return move_ids
