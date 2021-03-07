from odoo import fields, models,api
from odoo.exceptions import ValidationError

class prepayment_schedule_convert_revenue(models.TransientModel):
    _name = "prepayment.schedule.convert.revenue"
    _description = "Customer Prepayment Schedule Convert Revenue"

    date_id = fields.Date(string='Date')

    @api.multi
    def convert_revenue(self):
        customer_prepayment, supplier_prepayment = False, False
        context = dict(self._context)
        if context.get('active_model') == 'account.invoice':
            invoice_obj = self.env[context.get('active_model')].browse(context.get('active_id'))
            if invoice_obj.type in ['out_invoice','in_refund']:
                customer_prepayment = True
                prepayment_schedule_obj = self.env['customer.prepayment.schedule'].search([('invoice_id','=',invoice_obj.id)], limit=1)
            if invoice_obj.type in ['in_invoice','out_refund']:
                supplier_prepayment = True
                prepayment_schedule_obj = self.env['supplier.prepayment.schedule'].search([('invoice_id','=',invoice_obj.id)], limit=1)
        elif context.get('active_model') == 'customer.prepayment.schedule':
            customer_prepayment = True
            prepayment_schedule_obj = self.env['customer.prepayment.schedule'].browse(context.get('active_id'))
        elif context.get('active_model') == 'supplier.prepayment.schedule':
            supplier_prepayment = True
            prepayment_schedule_obj = self.env['supplier.prepayment.schedule'].browse(context.get('active_id'))

        if prepayment_schedule_obj.state != 'inprogress':
            raise ValidationError('Error!\nCan not convert to revenue. Prepayment schedule is cancelled.')

        if customer_prepayment:
            line_ids = self.env['customer.prepayment.schedule.line'].search([('journal_id','=',False),('customer_schedule_id','=',prepayment_schedule_obj.id)])
            for line in line_ids:
                line.do_payment_convert(self.date_id)
        if supplier_prepayment:
            line_ids = self.env['supplier.prepayment.schedule.line'].search([('journal_id','=',False),('supplier_schedule_id','=',prepayment_schedule_obj.id)])
            for line in line_ids:
                line.do_payment_convert(self.date_id)

prepayment_schedule_convert_revenue()