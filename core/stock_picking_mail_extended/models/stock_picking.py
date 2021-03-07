# -*- coding: utf-8 -*-

import pytz
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, SUPERUSER_ID


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    change_datetime = fields.Datetime('---')

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        if vals.get('model') == 'stock.picking' and \
           vals.get('message_type') == 'notification' and \
           'tracking_value_ids' in vals and vals.get('tracking_value_ids') and \
           vals.get('res_id'):
            picking_id = self.env['stock.picking'].browse(vals.get('res_id'))
            tz = self.env['res.users'].sudo().browse(SUPERUSER_ID).tz
            if tz:
                timezone = pytz.timezone(tz)
                start_utc_datetime = datetime.now(timezone)
            else:
                start_utc_datetime = datetime.now()
            picking_id.write({'change_datetime': start_utc_datetime})
            vals.get('tracking_value_ids').extend([[0, 0, {
                'field': 'change_datetime',
                'old_value_datetime': picking_id.change_datetime,
                'new_value_datetime': picking_id.change_datetime,
                'field_desc': '--- ',
                'field_type': 'datetime'
            }]])
        return super(MailMessage, self).create(vals)

    @api.model
    def write(self, vals):
         return super(MailMessage, self).write(vals)
