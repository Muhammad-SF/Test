# -*- coding: utf-8 -*-

import json
import logging
import pprint
import urllib
import urllib2
import werkzeug

from odoo import http
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class DokuController(http.Controller):
    _notify_url = '/payment/doku/notify'
    _redirect_url = '/shop'
    _cancel_url = '/payment/doku/cancel'

    def _get_redirect_url(self, **post):
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        return base_url + self._redirect_url

    def doku_validate_data(self, **post):
        """ Doku Notify:
            doku sends this post parameters
                AMOUNT
                TRANSIDMERCHANT
                WORDS
                STATUSTYPE
                RESPONSECODE = sukses:0000, gagal:9999
                APPROVALCODE
                RESULTMSG *)
                PAYMENTCHANNEL
                PAYMENTCODE
                SESSIONID
                BANK
                MCN
                PAYMENTDATETIME
                VERIFYID
                VERIFYSCORE
                VERIFYSTATUS
                CURRENCY
                PURCHASECURRENCY
                BRAND
                CHNAME
                THREEDSECURESTATUS
                LIABILITY
                EDUSTATUS
                CUSTOMERID
                TOKENID
            Once data is validated, we send: CONTINUE.
        """
        resp = post.get('RESPONSECODE')
        status = post.get('STATUSCODE')
        if resp == '0000' or status=='0000':
            _logger.info('Doku: validated data')

            res = True
            tx = None

            TRANSIDMERCHANT = post.get('TRANSIDMERCHANT')
            _logger.info('Doku: Doku: controller/main.py:86: TRANSIDMERCHANT=%s' % (TRANSIDMERCHANT))
            reference = post.get('SESSIONID')
            _logger.info('Doku: Doku: controller/main.py:87: reference=%s' % (reference))


            if reference:
                tx = request.env['payment.transaction'].search([('reference', '=', reference)])
                _logger.info('Doku: controller/main.py:93: tx=%s' % (tx))
            res = request.env['payment.transaction'].sudo().form_feedback(post, 'doku')
        else:
            _logger.info('Doku: controller/main.py:95: Failed Notify response %s', pprint.pformat(post))  # debug
            res = False
        return res

    @http.route('/payment/doku/notify', type='http', auth='none', methods=['POST'], csrf=False)
    def doku_notify(self, **post):

        _logger.info('Beginning Doku Notify with post data %s', pprint.pformat(post))  # debug
        try:
            self.doku_validate_data(**post)
            return 'CONTINUE'
        except ValidationError:
            _logger.exception('Unable to validate the Doku payment')
            return ""


    @http.route('/payment/doku/redirect', type='http', auth="none", methods=['POST', 'GET'], csrf=False)
    def doku_redirect(self, **post):
        """ Doku Redirect
        doku send these post paremeters:
            AMOUNT
            TRANSIDMERCHANT
            WORDS
            STATUSCODE
            PAYMENTCHANNEL
            SESSIONID
            PAYMENTCODE
            CURRENCY
            PURCHASECURRENCY

        """
        _logger.info('Beginning Doku Redirect with post data %s', pprint.pformat(post))  # debug
        redirect_url = self._get_redirect_url(**post)
        return werkzeug.utils.redirect(redirect_url)

    @http.route('/payment/doku/cancel', type='http', auth="none", csrf=False)
    def doku_cancel(self, **post):
        """ When the user cancels its Doku payment: GET on this route """
        _logger.info('Beginning Doku cancel with post data %s', pprint.pformat(post))  # debug
        redirect_url = self._get_redirect_url(**post)
        return werkzeug.utils.redirect(redirect_url)

    @http.route('/payment/doku/preview', type='http', auth="none", csrf=False)
    def doku_cancel(self, **post):
        """ When the user cancels its Doku payment: GET on this route """
        _logger.info('Beginning Doku preview with post data %s', pprint.pformat(post))  # debug
        redirect_url = self._get_redirect_url(**post)
        return werkzeug.utils.redirect(redirect_url)
