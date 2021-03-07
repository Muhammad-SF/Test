# -*- coding: utf-8 -*-
import json
import logging
import time

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class SyncPosConfig(models.Model):
    _inherit = 'pos.config'

    sync_session_id = fields.Many2one('pos.sync_session', 'Sync Session', help='Set the same value for POSes where orders should be synced. Keep empty if this POS should not use syncing')
    
    sync_message_ID = fields.Integer(default=1, string="Last sent message number")
    
    query_timeout = fields.Float(string='Query timeout', default=0.0833,
                                 help="Waiting period for any message from poll "
                                      "(if we have not received a message at this period, "
                                      "poll will send message ('PING') to check the connection)")

    response_timeout = fields.Float(string='Response timeout', default=0.01666,
                                    help="Waiting period for response message (i.e. once message from "
                                         "poll has been sent, it will be waiting for response message ('PONG') "
                                         "at this period and if the message has not been received, the icon turns "
                                         "color to red. Once the connection is restored, the icon changes its color "
                                         "back to green)")
    
    deactivate_empty_order = fields.Boolean('Deactivate empty order', default=False, help='POS is switched to new foreign Order, if current order is empty')
    replace_empty_order = fields.Boolean('Replace empty order', default=True, help='Empty order is deleted whenever new order is come from another POS')
    accept_incoming_orders = fields.Boolean('Accept incoming orders', default=True)


    @api.multi
    def _get_full_channel_name(self, channel_name):
        self.ensure_one()
        return '["%s","%s","%s"]' % (self._cr.dbname, channel_name, self.id)

    @api.multi
    def _send_to_channel(self, channel_name, message):
        notifications = []
        if channel_name == "pos.longpolling":
            channel = self._get_full_channel_name(channel_name)
            notifications.append([channel, "PONG"])
        else:
            for ps in self.env['pos.session'].search([('state', '!=', 'closed'), ('config_id', 'in', self.ids)]):
                channel = ps.config_id._get_full_channel_name(channel_name)
                notifications.append([channel, message])
        if notifications:
            self.env['bus.bus'].sendmany(notifications)
        _logger.debug('POS notifications for %s: %s', self.ids, notifications)
        return True

class SyncPosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        self.ensure_one()
        res = super(SyncPosSession, self).action_pos_session_close()
        self.config_id.sync_message_ID = 1
        active_sessions = self.env['pos.session'].search([
            ('state', '!=', 'closed'),
            ('config_id.sync_session_id', '=', self.config_id.sync_session_id.id)
        ])
        if not active_sessions:
            self.config_id.sync_session_id.sudo().write({'order_ID': 0})
            order_ids = self.config_id.sync_session_id.order_ids.filtered(lambda x: x.state == "draft")
            for order_id in order_ids:
                order_id.state ='unpaid'
        return res

class SyncPosMultiSession(models.Model):
    _name = 'pos.sync_session'

    name = fields.Char('Name')
    order_ID = fields.Integer(string="Order number", default=0,
        help="Current Order Number shared across all POS in Multi Session")
    order_ids = fields.One2many('pos.sync_session.order', 'sync_session_id', 'Orders')
    pos_ids = fields.One2many('pos.config', 'sync_session_id', 'Point Of Sale')

    @api.multi
    def order_set(self, message):
        self.ensure_one()
        order_uid = message['data']['uid']
        sequence_number = message['data']['sequence_number']
        multi_order_id = self.env['pos.sync_session.order'].search([('order_uid', '=', order_uid)])
        revision = self.order_revision_check(message, multi_order_id)
        if not revision or (multi_order_id and multi_order_id.state == 'deleted'):
            return {'action': 'revision_error'}
        if multi_order_id:
            multi_order_id.order = json.dumps(message)
            multi_order_id.revision_ID = multi_order_id.revision_ID + 1
        else:
            if self.order_ID + 1 != sequence_number:
                sequence_number = self.order_ID + 1
                message['data']['sequence_number'] = sequence_number
            multi_order_id = multi_order_id.create({
                'order_uid': order_uid,
                'order': json.dumps(message),
                'sync_session_id': self.id,
            })
            self.write({'order_ID': sequence_number})
        revision_ID = multi_order_id.revision_ID
        message['data']['revision_ID'] = revision_ID
        self.message_broadcast(message)
        return {
            'action': 'update_revision_ID',
            'revision_ID': revision_ID,
            'order_ID': sequence_number
        }

    @api.multi
    def order_remove(self, message):
        self.ensure_one()
        order_uid = message['data']['uid']
        multi_order_id = self.env['pos.sync_session.order'].search([('order_uid', '=', order_uid)])
        if multi_order_id.state is not 'deleted':
            revision = self.order_revision_check(message, multi_order_id)
            if not revision:
                return {'action': 'revision_error'}
        if multi_order_id:
            multi_order_id.state = 'deleted'
        self.message_broadcast(message)
        return {'order_ID': self.order_ID}

    @api.multi
    def message_broadcast(self, message):
        self.ensure_one()
        notifications = []
        channel_name = "pos.sync_session"
        for ps in self.env['pos.session'].search([('user_id', '!=', self.env.user.id), ('state', '!=', 'closed'),
                                                  ('config_id.sync_session_id', '=', self.id)]):
            message_ID = ps.config_id.sync_message_ID
            message_ID += 1
            ps.config_id.sync_message_ID = message_ID
            message['data']['message_ID'] = message_ID
            ps.config_id._send_to_channel(channel_name, message)

        if self.env.context.get('phantomtest') == 'slowConnection':
            _logger.info('Delayed notifications from %s: %s', self.env.user.id, notifications)
            self.env.cr.commit()
            time.sleep(3)
        return 1

    @api.multi
    def get_sync_all(self, message):
        self.ensure_one()
        pos_id = message['data']['pos_id']
        config_id = self.env['pos.config'].search([("id", "=", pos_id), ('sync_session_id', '=', self.id)])
        data = []
        for order_id in self.env['pos.sync_session.order'].search([('sync_session_id', '=', self.id), ('state', '=', 'draft')]):
            msg = json.loads(order_id.order)
            msg['data']['revision_ID'] = order_id.revision_ID
            msg['data']['message_ID'] = config_id.sync_message_ID
            data.append(msg)
        return {
            'action': 'sync_all',
            'orders': data,
            'order_ID': self.order_ID
        }

    @api.multi
    def message_update(self, msg):
        self.ensure_one()
        if msg['action'] == 'update_order':
            res = self.order_set(msg)
        elif msg['action'] == 'remove_order':
            res = self.order_remove(msg)
        elif msg['action'] == 'sync_all':
            res = self.get_sync_all(msg)
        else:
            res = self.message_broadcast(msg)
        return res

    @api.multi
    def order_revision_check(self, msg, order):
        self.ensure_one()
        server_revision_ID = order.revision_ID
        client_revision_ID = msg['data']['revision_ID']
        if not server_revision_ID:
            server_revision_ID = 1
        if client_revision_ID is not server_revision_ID:
            return False
        return True


class SyncPosMultiSessionOrder(models.Model):
    _name = 'pos.sync_session.order'

    order = fields.Text('Orders')
    order_uid = fields.Char(index=True)
    sync_session_id = fields.Many2one('pos.sync_session', 'Multi session', index=True)
    revision_ID = fields.Integer(string="Revision", default=1, help="Number of updates received from clients")
    state = fields.Selection([('draft', 'Draft'), ('deleted', 'Deleted'), ('unpaid', 'Unpaid and removed')], default='draft', index=True)