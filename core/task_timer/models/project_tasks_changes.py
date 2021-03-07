# -*- coding: utf-8 -*-
# Copyright 2017-2018 ZAD solutions (<http://www.zadsolutions.com>).
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pytz
from openerp import models, fields, api, _, exceptions
import datetime

# ______________Umar Aziz__________________________


class projectTasksTimer(models.Model):
    _inherit = 'project.task'

    work_start = fields.Datetime(string="Work Start", readonly=True)
    task_running = fields.Boolean(string="Task Running")
    work_hours = fields.Float(string="Total Work Hours")


    @api.multi
    def start_work(self):
        for line in self:
            active_tasks = line.search([('user_id', '=', line.user_id.id), ('task_running', '=', True)])
            active_task_ids = ','.join([active_task.name for active_task in active_tasks])
            if len(active_tasks) > 0:
                raise exceptions.ValidationError(
                    _("task ( " + str(active_task_ids) + " ) is Running, Stop it first before starting another task"))
            else:
                line.work_start = fields.Datetime.now()
                line.task_running = True

    @api.multi
    def stop_work_wizard(self):
        view_id = self.env['ir.model.data'].xmlid_to_res_id('task_timer.Project_timesheets_work')
        work_start = datetime.datetime.strptime(self.work_start, "%Y-%m-%d %H:%M:%S")
        today = datetime.datetime.now()
        return {
            'name': 'Project Timesheets Work',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.timesheets.work',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_work_start': self.work_start,
                'default_total_work_hour': float((today - work_start).seconds) / (60*60),
                'default_description': self.name
            },

        }


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
    def stop_work_kanban(self):
        for line in self:
            work_start = datetime.datetime.strptime(line.work_start, "%Y-%m-%d %H:%M:%S")
            today = datetime.datetime.now()

            #Custom by Harish
            work_end = datetime.datetime.now()

            work_start_tz = self._get_time_in_tz(work_start)
            work_end = self._get_time_in_tz(work_end)

            start_time = self._convert_time_to_float(work_start_tz)
            finish_time = self._convert_time_to_float(work_end)

            #End Custom by Harish
            vals = {
                'task_id': line.id,
                'date': fields.Date.today(),
                'user_id': line.user_id.id,
                'name': line.name,
                'account_id': line.project_id.analytic_account_id.id,
                'unit_amount': float((today - work_start).seconds) / (60*60),
                'project_id': line.project_id.id,
                'start_time': start_time, #Custom
                'finish_time': finish_time,#Custom
            }
            self.env['account.analytic.line'].create(vals)
            line.work_hours += float((today - work_start).seconds) / (60*60)
            line.task_running = False


# Code added by Harish
class AnalyticAccountLine(models.Model):

    _inherit = 'account.analytic.line'

    start_time = fields.Float(string='Start Time')
    finish_time = fields.Float(string="Finish Time")


