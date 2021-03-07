from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

WEEKDAYS = [
    ('0', 'Sunday'),
    ('1', 'Monday'),
    ('2', 'Tuesday'),
    ('3', 'Wednesday'),
    ('4', 'Thursday'),
    ('5', 'Friday'),
    ('6', 'Saturday'),
]


class resource_calendar(models.Model):
    _inherit = 'resource.calendar'

    week_working_day = fields.Integer(string='Number of working days (in a week)')
    week_start_day = fields.Selection(WEEKDAYS, string='Start Day', default='1')
    interval = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'), ], string='Interval', default='daily')

    @api.one
    @api.constrains('week_working_day')
    def _check_week_working_day(self):
        if self.week_working_day <= 0 or self.week_working_day > 7:
            raise ValidationError(_('Number of working days in a week should be 1-7.'))

