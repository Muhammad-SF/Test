# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class mail_mail(models.Model):
    _inherit = 'mail.mail'

    def _get_unsubscribe_url(self, email_to):
        url = ""
        return url
