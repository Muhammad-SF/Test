# -*- coding: utf-8 -*-
# Copyright 2017-2018 ZAD solutions (<http://www.zadsolutions.com>).
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pytz
from openerp import models, fields,api
import datetime
# ______________Umar Aziz__________________________


class project_timesheets_work(models.TransientModel):
    _name = 'project.timesheets.work'

    work_start = fields.Datetime(string="Work Start",)
    work_end = fields.Datetime(string="Work End", default=fields.Datetime.now)
    total_work_hour = fields.Float(string="Total Work Hour")
    description = fields.Char(string="Description", required=True)

    @api.onchange('work_start', 'work_end')
    def _get_total_work_hour(self):
        work_start = datetime.datetime.strptime(self.work_start, "%Y-%m-%d %H:%M:%S")
        work_end = datetime.datetime.strptime(self.work_end, "%Y-%m-%d %H:%M:%S")
        self.total_work_hour = float((work_end - work_start).seconds) / (60 * 60)


    @staticmethod
    def _convert_time_to_float(timeObj):
        t, hours = divmod(float(timeObj.time().hour), 24)
        t, minutes = divmod(float(timeObj.time().minute), 60)
        minutes = minutes / 60.0
        return hours + minutes

    def _get_time_in_tz(self, timeObj):
        tz = pytz.timezone(self.env.user.tz)
        tz_time = pytz.utc.localize(timeObj).astimezone(tz)
        return tz_time

    @api.multi
    def stop_work(self):
        for line in self:
            task_obj = self.env['project.task']
            task = task_obj.search([('id', '=', self.env.context['active_id'])])

            #Custom by Harish
            work_start = datetime.datetime.strptime(line.work_start, "%Y-%m-%d %H:%M:%S")
            work_end = datetime.datetime.strptime(line.work_end, "%Y-%m-%d %H:%M:%S")

            work_start = self._get_time_in_tz(work_start)
            work_end = self._get_time_in_tz(work_end)

            start_time = self._convert_time_to_float(work_start)
            finish_time = self._convert_time_to_float(work_end)

            #End Custom by Harish

            vals = {
                'task_id': task.id,
                'date': fields.Date.today(),
                'user_id': task.user_id.id,
                'name': line.description and line.description or task.name,
                'account_id': task.project_id.analytic_account_id.id,
                'unit_amount': line.total_work_hour,
                'project_id': task.project_id.id,
                'start_time': start_time, #Custom
                'finish_time': finish_time,#Custom
            }

            self.env['account.analytic.line'].create(vals)
            task.work_start = line.work_start
            task.work_hours += line.total_work_hour
            task.task_running = False
