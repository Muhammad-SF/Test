# coding: utf-8

import json
import logging
import urlparse

import dateutil.parser
import pytz

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.vit_payment_doku.controllers.main import DokuController
from odoo.tools.float_utils import float_compare
import time
import hashlib
import random, string

_logger = logging.getLogger(__name__)

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))


class AcquirerDoku(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('doku', 'Doku')])
    doku_sharedkey = fields.Char('Doku Shared Key', required_if_provider='doku', groups='base.group_user')
    doku_mall_id = fields.Char(
        'Doku Mall ID', groups='base.group_user',
        help='The Mall ID is used to ensure communications coming from Doku are valid and secured.')
    doku_use_notify = fields.Boolean('Use Notify', default=True, help='Doku Payment Notification', groups='base.group_user')
    doku_chain_merchant = fields.Char(string="Chain Merchant", required=False, )

    # Default doku fees
    fees_dom_fixed = fields.Float(default=0.35)
    fees_dom_var = fields.Float(default=3.4)
    fees_int_fixed = fields.Float(default=0.35)
    fees_int_var = fields.Float(default=3.9)

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(AcquirerDoku, self)._get_feature_support()
        res['fees'].append('doku')
        return res

    @api.model
    def _get_doku_urls(self, environment):
        """ Doku URLS """
        if environment == 'prod':
            return {
                'doku_form_url': 'https://pay.doku.com/Suite/Receive',
            }
        else:
            return {
                'doku_form_url': 'http://staging.doku.com/Suite/Receive',
            }

    @api.multi
    def doku_compute_fees(self, amount, currency_id, country_id):
        """ Compute doku fees.

            :param float amount: the amount to pay
            :param integer country_id: an ID of a res.country, or None. This is
                                       the customer's country, to be compared to
                                       the acquirer company country.
            :return float fees: computed fees
        """
        if not self.fees_active:
            return 0.0
        country = self.env['res.country'].browse(country_id)
        if country and self.company_id.country_id.id == country.id:
            percentage = self.fees_dom_var
            fixed = self.fees_dom_fixed
        else:
            percentage = self.fees_int_var
            fixed = self.fees_int_fixed
        fees = (percentage / 100.0 * amount + fixed) / (1 - percentage / 100.0)
        return fees

    @api.multi
    def doku_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        doku_tx_values = dict(values)
        doku_mall_id = self.doku_mall_id
        doku_sharedkey = self.doku_sharedkey
        doku_transid_merchant =  randomword(12)
        doku_sessionid =  values['reference']
        amount = "{:0.2f}".format(float(values['amount']))
        words = hashlib.sha1("%s%s%s%s" % (amount, doku_mall_id, doku_sharedkey, doku_transid_merchant)).hexdigest()
        doku_tx_values.update({
            'cmd': '_xclick',
            'basket': 'Item 1,10000.00,1,10000.00',
            'reference': values['reference'],
            'amount': amount,
            'currency_code':360,
            #'currency_code': values['currency'] and values['currency'].name or '',
            'address1': values.get('partner_address'),
            'city': values.get('partner_city'),
            #'country': values.get('partner_country') and values.get('partner_country').code or '',
            'country': 360,
            'state': values.get('partner_state') and (values.get('partner_state').code or values.get('partner_state').name) or '',
            'email': values.get('partner_email'),
            'zip_code': values.get('partner_zip'),
            'first_name': values.get('partner_first_name'),
            'last_name': values.get('partner_last_name'),
            'phone': values.get('partner_phone'),

            'doku_redirect': '%s' % urlparse.urljoin(base_url, DokuController._redirect_url),
            'notify_url': '%s' % urlparse.urljoin(base_url, DokuController._notify_url),
            'cancel_return': '%s' % urlparse.urljoin(base_url, DokuController._cancel_url),
            'handling': '%.2f' % doku_tx_values.pop('fees', 0.0) if self.fees_active else False,

            'custom': json.dumps({'return_url': '%s' % doku_tx_values.pop('return_url')}) if doku_tx_values.get('return_url') else False,

            'doku_mall_id': doku_mall_id,
            'doku_sharedkey': doku_sharedkey,
            'doku_transid_merchant': doku_transid_merchant,
            'doku_sessionid': doku_sessionid,

            'words': words,
            'datetime': time.strftime("%Y%m%d%H%M%S"),

        })
        return doku_tx_values

    @api.multi
    def doku_get_form_action_url(self):
        return self._get_doku_urls(self.environment)['doku_form_url']


class TxDoku(models.Model):
    _inherit = 'payment.transaction'

    doku_txn_type = fields.Char('Transaction type')

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _doku_form_get_tx_from_data(self, data):
        reference = data.get('SESSIONID')
        if not reference:
            error_msg = _('Doku: model/payment.py:155 received data with missing reference (%s) ') % (reference)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'Doku: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    @api.multi
    def _doku_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        reference = data['SESSIONID']
        if reference != self.reference:
            invalid_parameters.append(('Reference', reference, self.reference))
        return invalid_parameters


    @api.multi
    def _doku_form_validate(self, data):
        status = data.get('RESPONSECODE')
        res = {
            'acquirer_reference': data.get('TOKENID'),
            'doku_txn_type': data.get('STATUSTYPE'),
        }
        if status in ['0000']:
            _logger.info('Validated Doku payment for tx %s: set as done' % (self.reference))
            try:
                # dateutil and pytz don't recognize abbreviations PDT/PST
                tzinfos = {
                    'PST': -8 * 3600,
                    'PDT': -7 * 3600,
                }
                date_validate = dateutil.parser.parse(data.get('payment_date'), tzinfos=tzinfos).astimezone(pytz.utc)
            except:
                date_validate = fields.Datetime.now()

            res.update(state='done', date_validate=date_validate)
            return self.write(res)
        else:
            error = 'Received unrecognized status for Doku payment %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            res.update(state='error', state_message=error)
            return self.write(res)
