# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil import relativedelta
from odoo import fields, models, api

class HolidaysSummaryDept(models.TransientModel):
    _inherit = 'hr.holidays.summary.dept'

    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)

    @api.onchange('date_from','date_to')
    def onchange_dates(self):
        warning = {}
        if self.date_from and self.date_to:
            start_date = datetime.strptime(self.date_from, "%Y-%m-%d").date()
            end_date = datetime.strptime(self.date_to, "%Y-%m-%d").date()
            days = abs((end_date - start_date).days)
            if days > 90:
                warning = {'title': 'Value Error', 'message': "Please select date period fall within 3 months."}
        return {'warning': warning}

    @api.onchange('date_from', 'date_to')
    def onchange_start_date(self):
        warning = {}
        if self.date_from and self.date_to and self.date_from > self.date_to:
            warning = {'title': 'Value Error', 'message': "Start date must be anterior to end date."}
        return {'warning': warning}


HolidaysSummaryDept()