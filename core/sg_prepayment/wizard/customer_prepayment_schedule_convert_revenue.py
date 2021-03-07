from odoo import fields, models,api
from odoo.exceptions import ValidationError

class prepayment_schedule_convert_revenue(models.TransientModel):
    _name = "prepayment.schedule.convert.revenue"
    _description = "Customer Prepayment Schedule Convert Revenue"

    date_id = fields.Date(string='Date')

    @api.multi
    def convert_revenue(self):
        context = dict(self._context)
        if context.get('active_model') == 'account.invoice':
            cust_prepayment_schedule_obj = self.env['customer.prepayment.schedule'].search([('invoice_id','=',context.get('active_id'))], limit=1)
        else:
            cust_prepayment_schedule_obj = self.env['customer.prepayment.schedule'].browse(context.get('active_id'))

        if cust_prepayment_schedule_obj.state != 'inprogress':
            raise ValidationError('Error!\nCan not convert to revenue. Prepayment schedule is cancelled.')
        schedule_line_obj = self.env['customer.prepayment.schedule.line']
        line1_ids = schedule_line_obj.search([('date','<',self.date_id),('journal_id','=',False),('customer_schedule_id','=',cust_prepayment_schedule_obj.id)])
        for line in line1_ids:
            line.do_payment_convert(self.date_id)
        if cust_prepayment_schedule_obj.state != 'inprogress':
            raise ValidationError('Error!\nCan not convert to revenue. Prepayment schedule is cancelled.')
        schedule_line_obj = self.env['customer.prepayment.schedule.line']
        line1_ids = schedule_line_obj.search([('date','=',self.date_id),('journal_id','=',False),('customer_schedule_id','=',cust_prepayment_schedule_obj.id)])
        for line in line1_ids:
            line.do_payment_convert(self.date_id)
        if cust_prepayment_schedule_obj.state != 'inprogress':
            raise ValidationError('Error!\nCan not convert to revenue. Prepayment schedule is cancelled.')
        schedule_line_obj = self.env['customer.prepayment.schedule.line']
        line1_ids = schedule_line_obj.search([('date','>=',self.date_id),('journal_id','=',False),('customer_schedule_id','=',cust_prepayment_schedule_obj.id)])
        for line in line1_ids:
            line.do_payment_convert(self.date_id)


prepayment_schedule_convert_revenue()