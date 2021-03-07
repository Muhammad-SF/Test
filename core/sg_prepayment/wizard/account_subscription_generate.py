import time
from odoo import fields, models, api, _

class account_subscription_generate(models.TransientModel):
    _name = 'account.subscription.generate'
    _description = "Subscription Compute"

    date = fields.Date('Generate Entries Before', default=lambda *a: time.strftime('%Y-%m-%d'), required=True)

    @api.multi
    def action_generate(self):
        sub_line_obj = self.env['account.subscription.line']
        moves_created = []
        for data in self:
            line_ids = sub_line_obj.search([('date', '<=', data.date), ('move_id', '=', False)])
            moves = line_ids.move_create()
            moves_created.extend(moves)
        action = self.env.ref('account.action_move_line_form')
        result = action.read()[0]
        result['domain'] = str([('id', 'in', moves_created)])
        return result

account_subscription_generate()