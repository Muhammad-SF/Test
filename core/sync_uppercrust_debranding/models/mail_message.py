# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging
from odoo import models, api
from .ir_translation import debrand

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, values):
        subject = values.get('subject')
        channel_all_employees = self.env.ref('mail.channel_all_employees', raise_if_not_found=False)
        if channel_all_employees \
                and subject \
                and values.get('model') == 'mail.channel' \
                and channel_all_employees.id == values.get('res_id') \
                and subject.endswith('application installed!'):
            values['body'] = debrand(self.env, values.get('body', ''))
        return super(MailMessage, self).create(values)
