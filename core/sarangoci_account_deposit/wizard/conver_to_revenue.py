from odoo import models, fields, api
from odoo.tools.translate import _


class ConvertToRevenue(models.TransientModel):
    _name = 'convert.revenue'

    @api.model
    def _get_accounts(self):
        print "----------_get_accounts "
        account_ids = []
        if self._context and self._context.get('customer'):
            # domain="[('user_type_id', '=', 'Other Income')]" 
            account_ids = self.env['account.account'].search([('user_type_id', '=', 'Other Income')])
        if self._context and self._context.get('supplier'):

            account_ids = self.env['account.account'].search([('user_type_id', '=', 'Expenses')])
        return [('id', 'in', account_ids and account_ids.ids or [])]

    date = fields.Date(string='Date', default=fields.Date.context_today)
    revenue_account = fields.Many2one('account.account', string="Revenue Account", domain=_get_accounts)

    @api.model
    def fields_get(self, fields=None):
        context = self._context
        if context is None:
            context={}
        res = super(ConvertToRevenue, self).fields_get( fields)
        if context and context.get('account_string'):
            if 'string' in res['revenue_account']:
                res['revenue_account']['string'] = context.get('account_string')
        return res

    @api.multi
    def action_confirm(self):
        payment_id = self.env['account.payment'].browse(self._context.get('active_ids'))
        # move_id = payment_id.move_line_ids and payment_id.move_line_ids[0].move_id and payment_id.move_line_ids[0].move_id.id or False

        revenue_account_move_vals = {
            'journal_id': payment_id.journal_id.id,
            'date': fields.date.today(),
            'amount': payment_id.remaining_amount,
        }
        move_id = self.env['account.move'].create(revenue_account_move_vals)

        revenue_account_value = {'payment_id': payment_id.id,
            'name': u'Customer payment revenue',
            'invoice_id': False,
            'journal_id': payment_id.journal_id.id,
            'currency_id': False,
            'amount_currency': False,
            'partner_id': payment_id.partner_id.commercial_partner_id.id,
            'move_id': move_id.id}

        if payment_id.payment_type == 'inbound':
            revenue_account_value.update({
                'credit': payment_id.remaining_amount,
                'debit': 0.0,
                'account_id': self.revenue_account.id})
        elif payment_id.payment_type == 'outbound':
            revenue_account_value.update({
                'credit': 0.0,
                'debit':payment_id.remaining_amount,
                'account_id': self.revenue_account.id})
        move_line_id = self.with_context(check_move_validity=False).env['account.move.line'].create(revenue_account_value)
         # payment_id.state = 'returned'

        deposit_account_value = {'payment_id': payment_id.id,
            'name': u'Customer payment revenue',
            'invoice_id': False,
            'journal_id': payment_id.journal_id.id,
            'currency_id': False,
            'amount_currency': False,
            'partner_id': payment_id.partner_id.commercial_partner_id.id,
            'move_id': move_id.id}
        if payment_id.payment_type == 'inbound':
            deposit_account_value.update({
                'credit': 0.0,
                'debit': payment_id.remaining_amount,
                'account_id': payment_id.writeoff_account_id.id })
        elif payment_id.payment_type == 'outbound':
            deposit_account_value.update({
                'credit': payment_id.remaining_amount,
                'debit': 0.0,
                'account_id': payment_id.writeoff_account_id.id})
        move_line_id = self.with_context(check_move_validity=False).env['account.move.line'].create(deposit_account_value)
        move_id.post()
    	payment_id.write({'state': 'revenue', 'remaining_amount': 0.0})