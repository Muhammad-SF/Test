# -*- coding: utf-8 -*-
import datetime
import json
import logging

import odoo
from odoo import http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


try:
    from odoo.addons.bus.controllers.main import BusController
except ImportError:
    _logger.error('sync_pos_orders inconsisten with odoo version')
    BusController = object


class Controller(BusController):

    @http.route('/sync_pos_restaurant_order/update', type="json", auth="public")
    def sync_pos_restaurant_order(self, sync_session_id, message):
        return request.env["pos.sync_session"].with_context(phantomtest=request.httprequest.headers.get('phantomtest')).browse(int(sync_session_id)).message_update(message)

    @http.route('/sync_pos_restaurant_order/test/gc', type="http", auth="user")
    def sync_pos_restaurant_order_test_gc(self):
        if not odoo.tools.config['test_enable']:
            _logger.warning('Run odoo with --test-enable to use test GC')
            return 'Run odoo with --test-enable to use test GC'
        timeout_ago = datetime.datetime.utcnow()
        bus_id = request.env['bus.bus'].sudo().search([('create_date', '<=', timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])
        for res in bus_id:
            _logger.info('removed message: %s', res.message)
        ids = bus_id.ids
        bus_id.unlink()
        return json.dumps(ids)

    @http.route('/pos_longpolling/update', type="json", auth="public")
    def longpolling_update(self, pos_id, message):
        return request.env["pos.config"].browse(int(pos_id))._send_to_channel('pos.longpolling', message)
