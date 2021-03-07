
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import Warning


class ReturnDepositWizard(models.TransientModel):
    _name = 'account.deposit.return'
    # _inherit = 'account.abstract.payment'


    @api.one
    @api.depends('return_amount', 'return_date')
    def _compute_payment_difference(self):
        if self._context and self._context.get('active_id'):
            payment_id = self.env['account.payment'].search([('id', '=', self._context.get('active_id'))])
            payment_obj = self.env['account.payment']
            if self.return_amount == payment_id.remaining_amount:
                return
            self.payment_difference = payment_id.remaining_amount - self.return_amount

    @api.model
    def _get_amount(self):
        if self._context and self._context.get('active_id'):
            payment_id = self.env['account.payment'].search([('id', '=', self._context.get('active_id'))])
            return payment_id.remaining_amount
        return 0.0

    return_date = fields.Date(string='Date', default=fields.Date.context_today)
    return_amount = fields.Float(string='Amount', digits=0, required=True, default=_get_amount)
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])


    payment_difference = fields.Integer(compute='_compute_payment_difference', readonly=True)
    payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark Deposit as fully returned')], default='open', string="Payment Difference", copy=False)
    diff_amount_account_id = fields.Many2one('account.account', string='Post Difference In')

    @api.onchange('return_amount')
    def _onchange_return_amount(self):
        if self.return_amount and self._context and self._context.get('active_id'):
            payment_obj = self.env['account.payment']
            payment_id = payment_obj.search([('id', '=', self._context.get('active_id'))])
            if payment_id.remaining_amount < self.return_amount:
                raise Warning(_('Please input amount lessthen '+ str(payment_id.remaining_amount) ))

    @api.multi
    def return_deposit(self):
        if self._context and self._context.get('active_id'):
            payment_obj = self.env['account.payment']
            payment_id = payment_obj.search([('id', '=', self._context.get('active_id'))])
            current_amount = payment_id.remaining_amount and payment_id.remaining_amount or payment_id.remaining_amount
            if self.payment_difference_handling == 'reconcile' or self.payment_difference == 0.0:
                if current_amount < self.return_amount:
                    raise Warning(_('Please input amount lessthen '+ str(payment_id.remaining_amount) ))
                payment_refund_value = {
                    'partner_id': payment_id.partner_id.id,
                    'journal_id' : self.journal_id.id,
                    'amount': payment_id.remaining_amount,
                    'payment_date' : self.return_date,
                    'payment_type': payment_id.payment_type == 'inbound' and 'outbound' or payment_id.payment_type == 'outbound' and 'inbound' or 'transfer',
                    'partner_type': payment_id.payment_type == 'inbound' and 'customer' or payment_id.payment_type == 'outbound' and 'supplier' or False,
                    'is_deposit_return': True,
                    'deposit_payment_id': payment_id.id,
                    'writeoff_account_id' : payment_id.writeoff_account_id.id,
                }
                payment_methods = payment_refund_value.get('payment_type') == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                payment_method_id = payment_methods and payment_methods[0] or False
                
                if payment_method_id:
                    payment_refund_value.update({'payment_method_id':payment_method_id.id})
                else:
                    raise Warning(_('Please assign payment method.'))
                
                return_payment_id = payment_obj.with_context(return_payment_create=True,return_amount=self.return_amount).create(payment_refund_value)
                payment_id.return_payment_reference =  [(4, return_payment_id.id)]
                return_payment_id.post()
                move_id = return_payment_id.move_line_ids and return_payment_id.move_line_ids[0].move_id and return_payment_id.move_line_ids[0].move_id.id or False
                if payment_id.remaining_amount != self.return_amount and self.diff_amount_account_id:
                    diff_account_value = {'payment_id': return_payment_id.id, 
                        'name': u'Customer Deposit Return Diff', 
                        'invoice_id': False, 
                        'journal_id': return_payment_id.journal_id.id, 
                        'currency_id': False, 
                        'amount_currency': False, 
                        'partner_id': return_payment_id.partner_id.commercial_partner_id.id, 
                        'move_id': move_id, 
                        'account_id': self.diff_amount_account_id.id}
                    if payment_id.payment_type == 'inbound':
                        diff_account_value.update({
                            'credit': payment_id.remaining_amount - self.return_amount,   
                            'debit': 0.0, })
                    elif payment_id.payment_type == 'outbound':
                        diff_account_value.update({
                            'credit': 0.0 ,   
                            'debit':payment_id.remaining_amount - self.return_amount, })
                    move_line_id = self.env['account.move.line'].with_context(return_payment_id=return_payment_id.id,deposit_active_id=payment_id.id,return_amount=self.return_amount).create(diff_account_value)
                payment_id.state = 'returned'
                return_payment_id.state = 'returned'
                return True
            else:
                payment_refund_value = {
                    'partner_id': payment_id.partner_id.id,
                    'journal_id' : self.journal_id.id,
                    'amount': self.return_amount,
                    'payment_date' : self.return_date,
                    'payment_type': payment_id.payment_type == 'inbound' and 'outbound' or payment_id.payment_type == 'outbound' and 'inbound' or 'transfer',
                    'partner_type': payment_id.payment_type == 'inbound' and 'customer' or payment_id.payment_type == 'outbound' and 'supplier' or False,
                    'is_deposit_return': True,
                    'deposit_payment_id': payment_id.id,
                    'writeoff_account_id' : payment_id.writeoff_account_id.id,
                }
                payment_methods = payment_refund_value.get('payment_type') == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                payment_method_id = payment_methods and payment_methods[0] or False
                
                if payment_method_id:
                    payment_refund_value.update({'payment_method_id':payment_method_id.id})
                else:
                    raise Warning(_('Please assign payment method.'))
                
                return_payment_id = payment_obj.with_context(return_payment_create=True,return_amount=self.return_amount).create(payment_refund_value)
                payment_id.return_payment_reference = [(4, return_payment_id.id)]
                return_payment_id.post()
                return_payment_id.state = 'returned'
                move_id = return_payment_id.move_line_ids and return_payment_id.move_line_ids[0].move_id and return_payment_id.move_line_ids[0].move_id.id or False
                
                payment_id.remaining_amount =  current_amount - self.return_amount
                if payment_id.remaining_amount == 0.0:
                    payment_id.state = 'returned'