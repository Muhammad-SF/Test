# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from datetime import  datetime
class ScheduleRateItem(models.Model):
    _name = 'schedule.rate.item'

    name = fields.Char('Schedule of Rates Items')

class ScheduleRate(models.Model):
    _name = 'schedule.rate'

    @api.model
    def _get_default_line(self):
        line_ids = self.env['schedule.rate.line']
        for line in self.env['schedule.rate.item'].search([]):
            new_id = line_ids.new({
                'name': line.id,
                'qty': 1,
                'unit_price': 1
            })
            line_ids += new_id
        return line_ids

    name = fields.Char('Schedule of Rates',required=1)
    active = fields.Boolean('Active', default=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id.id)


    line_ids = fields.One2many('schedule.rate.line', 'schedule_id',default=_get_default_line)

class ScheduleRateLine(models.Model):
    _name = 'schedule.rate.line'

    name = fields.Many2one('schedule.rate.item', 'Schedule of Rates Items')
    schedule_id = fields.Many2one('schedule.rate')
    qty = fields.Float('Quantity', default=1)
    unit_price = fields.Float('Unit Price',default=1)
