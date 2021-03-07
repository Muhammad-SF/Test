# -*- coding: utf-8 -*
from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    allow_multiple_attendance = fields.Boolean('Allow Multiple Attendance per Day?', default=True)

ResCompany()