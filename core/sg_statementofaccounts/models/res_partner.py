from odoo import fields, models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class res_partner(models.Model):
    _inherit = 'res.partner'

    today_date = fields.Date('Date Today',default=fields.Date.today)

    @api.multi
    def get_current_due(self):
       for record in self.invoice_ids:
        day30 = datetime.strptime(self.today_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=30)
        current_due = 0
        if record.state not in ['draft', 'cancel'] and record.date_invoice:
            if (datetime.strptime(record.date_invoice, DEFAULT_SERVER_DATE_FORMAT) >= day30) and (datetime.strptime(record.date_invoice, DEFAULT_SERVER_DATE_FORMAT) <= datetime.strptime(self.today_date, DEFAULT_SERVER_DATE_FORMAT)):
                current_due += record.residual_signed
                return current_due

    @api.multi
    def get_date_31_60(self):
        for record in self.invoice_ids:
            day30 = datetime.strptime(self.today_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=30)
            day60 = datetime.strptime(self.today_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=60)
            due_3160 = 0
            if record.state not in ['draft', 'cancel'] and record.date_invoice:
                if (datetime.strptime(record.date_invoice, DEFAULT_SERVER_DATE_FORMAT) < day30) and (datetime.strptime(record.date_invoice, DEFAULT_SERVER_DATE_FORMAT) >= day60):
                    due_3160 += record.residual_signed
                    return due_3160

    @api.multi
    def get_date_61_90(self):
        for record in self.invoice_ids:
            day90 = datetime.strptime(self.today_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=90)
            due_6190 = 0
            if record.state not in ['draft', 'cancel'] and record.date_invoice:
                if datetime.strptime(record.date_invoice, DEFAULT_SERVER_DATE_FORMAT) >= day90:
                    due_6190 += record.residual_signed
                    return due_6190

    @api.multi
    def get_date_91(self):
        for record in self.invoice_ids:
            day90 = datetime.strptime(self.today_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=90)
            due_91 = 0
            if record.state not in ['draft', 'cancel'] and record.date_invoice:
                if datetime.strptime(record.date_invoice, DEFAULT_SERVER_DATE_FORMAT) < day90:
                    due_91 += record.residual_signed
                    return due_91

res_partner()