# -*- coding: utf-8 -*-

from odoo import fields, models, exceptions, api

class HrTimesheetSheet(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'

    @api.model
    def create(self, values):
        if 'timesheet_ids' in values:
            timesheet_ids = values.get('timesheet_ids')
            timesheets = []
            for timesheet in timesheet_ids:
                if timesheet[0] in [0, 1]:
                    if 'amount' in timesheet[2] and 'unit_amount' in timesheet[2]:
                        timesheet[2]['amount'] = timesheet[2]['unit_amount'] * 30
                timesheets.append(timesheet)
            values['timesheet_ids'] = timesheets
        result = super(HrTimesheetSheet, self).create(values)
        return result

    @api.multi
    def write(self, values):
        if 'timesheet_ids' in values:
            timesheet_ids = values.get('timesheet_ids')
            timesheets = []
            for timesheet in timesheet_ids:
                if timesheet[0] in [0, 1]:
                    if 'amount' in timesheet[2] and 'unit_amount' in timesheet[2]:
                        timesheet[2]['amount'] = timesheet[2]['unit_amount'] * 30
                timesheets.append(timesheet)
            values['timesheet_ids'] = timesheets
        result = super(HrTimesheetSheet, self).write(values)
        return result