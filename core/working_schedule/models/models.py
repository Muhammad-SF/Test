# -*- coding: utf-8 -*-

from odoo import models, fields, api


class working_schedule(models.Model):
    _inherit = 'resource.calendar.attendance'

    grace_time_for_late = fields.Float('Grace Time for Late')

