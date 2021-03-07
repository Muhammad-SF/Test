from odoo import fields, models, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    transfer_log_activity_ids = fields.One2many('transfer.log.activity','reference',string='Transfer Log Activity Ids')
    process_time = fields.Char(compute="_compute_process_time", string='Processed Time', store=True, help="The time it takes to complete a transfer.")
    picking_name = fields.Char(related="picking_type_id.name")

    def create_transfer_activity_log(self):
        if self.state != 'draft':
            process_time =self._get_process_time()
        else:
            process_time = '00:00:00'
        time = str(process_time).split(':')
        total_seconds = 0
        if len(time) == 3:
            total_seconds += (float(time[0]) * 60 * 60) + (float(time[1]) * 60) + (float(time[2]))
        hours = total_seconds // 3600
        days = int(total_seconds // (24 * 3600))
        minutes = (total_seconds % 3600) // 60
        total_seconds = total_seconds % 60
        hours1 = hours + (days * 24)
        minutes1 = (hours1 * 60) + minutes
        seconds1 = (minutes1 * 60) + total_seconds
        vals = {
            'origin': self.origin or '',
            'timestamp': fields.datetime.now(),
            'user': self.env.user.name,
            'status': dict(self._fields['state'].selection).get(self.state),
            'location': self and self.location_id.display_name,
            'location_dest': self and self.location_dest_id.display_name,
            'customer': self and self.partner_id and self.partner_id.name or ' ',
            'vendor': self and self.partner_id and self.partner_id.name or ' ',
            'days': round(seconds1 / 86400.00, 2),
            'hours_minutes': process_time,
            'process_time': process_time,
            'company_id': self.company_id.id,
            'picking_name': self.picking_name,
            'reference': self.id or False
        }
        transfer_activity_log_id = self.env['transfer.activity.log'].create(vals)

    @api.multi
    @api.depends('transfer_log_activity_ids')
    def _compute_process_time(self):
        for res in self:
            total_seconds = 0
            for log_line in res.transfer_log_activity_ids:
                time = str(log_line.process_time).split(':')
                if len(time) == 3:
                    total_seconds += (float(time[0]) * 60 * 60) + (float(time[1]) * 60) + (float(time[2]))
            Days = int(total_seconds // (24 * 3600))
            Hours = int(total_seconds // 3600)
            total_seconds %= 3600
            Minutes = int(total_seconds // 60)
            res.process_time = str(Days) + ' Days ' + str(Hours) + ' Hours ' + str(Minutes) + ' Minutes'


    @api.multi
    def _get_process_time(self):
        time = fields.datetime.now() - datetime.strptime(self.transfer_log_activity_ids[-1].timestamp, DTF)
        days, seconds = time.days, time.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        second = str('0' + str(seconds)) if seconds < 9 else str(seconds)
        minute = str('0' + str(minutes)) if minutes < 9 else str(minutes)
        hour = str('0' + str(hours)) if hours < 9 else str(hours)
        return hour + ':' + minute + ':' + second


    @api.multi
    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        self.transfer_log_action_confirm()
        return res

    def transfer_log_action_confirm(self):
        line_vals = []
        for rec in self:
            rec.create_transfer_activity_log()
            line_vals.append((0, 0, {'status': dict(self._fields['state'].selection).get(self.state),
            'timestamp': fields.datetime.now(),
            'process_time': self._get_process_time(),
            'user':self.env.user.id,}))
            rec.transfer_log_activity_ids = line_vals


    @api.multi
    def action_prepared(self):
        res = super(StockPicking, self).action_prepared()
        self.transfer_log_action_prepared()
        return res

    def transfer_log_action_prepared(self):
        line_vals = []
        for rec in self:
            rec.create_transfer_activity_log()
            line_vals.append((0, 0, {'status': dict(self._fields['state'].selection).get(self.state),
                                     'timestamp': fields.datetime.now(),
                                     'process_time': self._get_process_time(),
                                     'user': self.env.user.id, }))
            rec.transfer_log_activity_ids = line_vals


    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        self.transfer_log_action_do_new_transfer()
        return res

    def transfer_log_action_do_new_transfer(self):
        line_vals = []
        for rec in self:
            rec.create_transfer_activity_log()
            line_vals.append((0, 0, {'status': dict(self._fields['state'].selection).get(self.state),
                                     'timestamp': fields.datetime.now(),
                                     'process_time': self._get_process_time(),
                                     'user': self.env.user.id, }))
            rec.transfer_log_activity_ids = line_vals

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        self.transfer_log_action_done()
        self.move_lines.write({'process_time': self.process_time})
        self.pack_operation_product_ids.write({'process_time': self.process_time})
        return res

    def transfer_log_action_done(self):
        line_vals = []
        for rec in self:
            rec.create_transfer_activity_log()
            line_vals.append((0, 0, {'status': dict(self._fields['state'].selection).get(self.state),
                                     'timestamp': fields.datetime.now(),
                                     'process_time': self._get_process_time(),
                                     'user': self.env.user.id, }))
            rec.transfer_log_activity_ids = line_vals

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        res.create_transfer_activity_log()
        line_vals = [(0, 0, {'status': 'Draft',
                                     'timestamp': fields.datetime.now(),
                                     'process_time': '00:00:00',
                                     'user': self.env.user.id})]
        res.transfer_log_activity_ids = line_vals
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    process_time = fields.Char(string='Processed Time', help="The time it takes to complete a transfer.")


class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    process_time = fields.Char(string='Processed Time', help="The time it takes to complete a transfer.")