from odoo import fields, models,api
from datetime import datetime
from odoo.exceptions import ValidationError

class prepayment_schedule_cancel(models.TransientModel):
    _name = "prepayment.schedule.cancel"
    _description = "Customer Prepayment Schedule Cancel"

    @api.multi
    @api.depends('refund_amount')
    def compute_refund_amount(self):
        context = dict(self._context)
        active_id = context.get('active_id')
        prepayment_schedule_obj = self.env['customer.prepayment.schedule'].browse(active_id)
        for record in self:
            refund_amount2 = self.refund_amount
            for line in prepayment_schedule_obj.lines.sorted(key=lambda r: r.id, reverse=True):
                if not line.journal_id:
                    if line.amount <= refund_amount2:
                        refund_amount2 -= line.amount
                        line.amount = 0.0
                    else:
                        line.amount -= refund_amount2
                        refund_amount2 = 0.0
            if refund_amount2 > prepayment_schedule_obj.invoice_id.residual:
                record.refund_amount_check = True

    refund_amount = fields.Float(string="Refund Amount")
    payment_method = fields.Many2one('account.journal',string="Payment Method")
    reason_id = fields.Text(string="Reason")
    revenue_account = fields.Many2one('account.account', string="Revenue Account")
    refund_amount_check = fields.Boolean(compute='compute_refund_amount', string='Refund Amount Check')

    @api.multi
    def action_confirm_cancel(self):
        context = dict(self._context)
        active_id = context.get('active_id')
        if context.get('active_model') == 'customer.prepayment.schedule':
            prepayment_schedule_obj = self.env['customer.prepayment.schedule'].browse(active_id)
        elif context.get('active_model') == 'supplier.prepayment.schedule':
            prepayment_schedule_obj = self.env['supplier.prepayment.schedule'].browse(active_id)
        invoice_obj = prepayment_schedule_obj.invoice_id

        if self.refund_amount > prepayment_schedule_obj.invoice_id.amount_total:
            raise ValidationError('Error!\nRefund amount must be less than or equal to invoice amount')
        refund_amount2 = self.refund_amount
        for line in prepayment_schedule_obj.lines.sorted(key=lambda r: r.id, reverse=True):
            if not line.journal_id:
                if line.amount <= refund_amount2:
                    refund_amount2 -= line.amount
                    line.amount = 0.0
                else:
                    line.amount -= refund_amount2
                    refund_amount2 = 0.0
        if refund_amount2:
            if (refund_amount2 == prepayment_schedule_obj.invoice_id.amount_total) or (refund_amount2 < prepayment_schedule_obj.invoice_id.residual):
                debit_vals = {
                    'name': self.reason_id,
                    'debit': refund_amount2,
                    'credit': 0.0,
                    'account_id': prepayment_schedule_obj.prepaid_account.id,
                    'tax_line_id': False,
                }
                credit_vals = {
                    'name': prepayment_schedule_obj.journal_id.name,
                    'debit': 0.0,
                    'credit': refund_amount2,
                    'account_id': self.payment_method.default_credit_account_id.id,
                    'tax_line_id': False,
                }
                vals = {
                    'ref': prepayment_schedule_obj.invoice_id.number,
                    'journal_id': self.payment_method.id,
                    'partner_id': prepayment_schedule_obj.partner_id.id,
                    'date': datetime.now(),
                    'state': 'draft',
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                move.post()
                prepayment_schedule_obj.write({'move_ids': [(4, move.id)]})

            elif refund_amount2 > prepayment_schedule_obj.invoice_id.residual:
                debit_vals1 = {
                    'name': 'Prepaid',
                    'debit': prepayment_schedule_obj.invoice_id.residual,
                    'credit': 0.0,
                    'account_id': prepayment_schedule_obj.prepaid_account.id,
                    'tax_line_id': False,
                }
                debit_vals2 = {
                    'name': 'Revenue',
                    'debit': refund_amount2 - prepayment_schedule_obj.invoice_id.residual,
                    'credit': 0.0,
                    'account_id': self.revenue_account.id,
                    'tax_line_id': False,
                }
                credit_vals = {
                    'name': prepayment_schedule_obj.journal_id.name,
                    'debit': 0.0,
                    'credit': refund_amount2,
                    'account_id': self.payment_method.default_credit_account_id.id,
                    'tax_line_id': False,
                }
                vals = {
                    'ref': prepayment_schedule_obj.invoice_id.number,
                    'journal_id': self.payment_method.id,
                    'partner_id': prepayment_schedule_obj.partner_id.id,
                    'date': datetime.now(),
                    'state': 'draft',
                    'line_ids': [(0, 0, debit_vals1), (0, 0, debit_vals2), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                move.post()
                prepayment_schedule_obj.write({'move_ids': [(4, move.id)]})
        prepayment_schedule_obj.write({'state': 'cancelled'})
        if invoice_obj.state == 'prepaid':
            invoice_obj.state = 'open'
        return True

prepayment_schedule_cancel()