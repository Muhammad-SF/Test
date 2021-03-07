# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api


class hr_holiday_lines_inherit(models.Model):
    _inherit = 'hr.holiday.lines'

    state = fields.Selection(related='holiday_id.state', string='Status', store=True)


class HrTimesheetSheetSheet(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'

    employee_leave_ids = fields.One2many('hr.holidays', compute="_compute_employee_leave_ids", string='Leaves')
    holiday_line_ids = fields.One2many('hr.holiday.lines', compute="_compute_employee_leave_ids", string='Holidays')

    @api.multi
    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_employee_leave_ids(self):
        for one_sheet in self:
            employee_leaves = False
            if one_sheet.employee_id and one_sheet.date_from and one_sheet.date_to:
                employee_id = one_sheet.employee_id.id
                date_from = one_sheet.date_from
                date_to = one_sheet.date_to
                query = "select id from hr_holidays " \
                        "where employee_id in (" + str(employee_id) + ") and " \
                        "type in ('remove') and " \
                        "(((date_from between '" + date_from + "' and '" + date_to + "') or " \
                        "(date_to between '" + date_from + "' and '" + date_to + "')) or " \
                        "(date_from = '" + date_from + "' and date_to = '" + date_to + "') or " \
                        "('" + date_from + "' between date_from and date_to))"
                self._cr.execute(query)
                existing_ids = [x[0] for x in self._cr.fetchall()]
                if existing_ids:
                    employee_leaves = self.env["hr.holidays"].search([("id", "in", existing_ids)])
            one_sheet.employee_leave_ids = employee_leaves

            hr_holidays = False
            if one_sheet.date_from and one_sheet.date_to:
                date_from = one_sheet.date_from
                date_to = one_sheet.date_to
                query = "select id from hr_holiday_lines " \
                        "where state in ('confirmed') and " \
                        "(((holiday_date between '" + date_from + "' and '" + date_to + "')) or " \
                        "(holiday_date = '" + date_from + "' and holiday_date = '" + date_to + "'))"
                self._cr.execute(query)
                existing_ids = [x[0] for x in self._cr.fetchall()]
                if existing_ids:
                    hr_holidays = self.env["hr.holiday.lines"].search([("id", "in", existing_ids)])
            one_sheet.holiday_line_ids = hr_holidays
