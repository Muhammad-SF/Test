from odoo import fields, models,api
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class prepayment_schedule(models.TransientModel):
    _name = "prepayment.schedule"
    _description = "Customer Prepayment Schedule"

    payment_id= fields.Many2one('account.account', 'Payment Method')
    frequency_method= fields.Selection([('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Frequency Method',track_visibility='onchange')
    frequency= fields.Integer(string='Frequency',default = 1,track_visibility='onchange')
    date= fields.Date('First Date',track_visibility='onchange')
    prepaid_account = fields.Many2one('account.account',string= "Prepaid Account")
    revenue_account = fields.Many2one('account.account',string= "Revenue Account")

    @api.multi
    def action_confirm(self):
        context = dict(self._context)
        invoice_id = context.get('active_id')
        invoice_obj = self.env['account.invoice'].browse(invoice_id)
        invoice_obj.action_invoice_open()
        invoice_obj.write({'state': 'prepaid'})

        debit_vals = {
                    'name': "/",
                    'debit': invoice_obj.amount_total,
                    'credit': 0.0,
                    'account_id': self.payment_id.id,
                    'partner_id': invoice_obj.partner_id.id,
                    'tax_line_id': False,
                }
        print "debit_vals =",debit_vals
        credit_vals = {
                    'name': invoice_obj.number,
                    'debit': 0.0,
                    'credit': invoice_obj.amount_total,
                    'account_id': self.prepaid_account.id,
                    'partner_id': invoice_obj.partner_id.id,
                    'tax_line_id': False,
                }
        print "credit_vals =",credit_vals
        vals = {
                    'ref': invoice_obj.number,
                    'journal_id': invoice_obj.journal_id.id,
                    'date': datetime.now(),
                    'state': 'draft',
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
        print "vals =",vals
        move = self.env['account.move'].create(vals)
        move.post()

        vals = {
            'journal_id' : self.payment_id.id,
            'frequency_method' : self.frequency_method,
            'frequency' : self.frequency,
            'date' : self.date,
            'prepaid_account' : self.prepaid_account.id,
            'revenue_account': self.revenue_account.id,
            'invoice_id' : invoice_obj.id,
            'partner_id' : invoice_obj.partner_id.id,
            'state': 'inprogress',
        }

        schedule_obj = self.env['customer.prepayment.schedule']
        # schedule_line_obj = self.env['customer.prepayment.schedule.line']
        create_obj = schedule_obj.create(vals)
        create_obj.compute()





prepayment_schedule()