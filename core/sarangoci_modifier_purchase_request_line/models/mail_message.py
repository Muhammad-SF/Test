from odoo import models, fields, api,_
import logging

from email.utils import formataddr
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

class mail_message(models.Model):
    _inherit = 'mail.message'

    @api.model
    def _get_default_from(self):
        if self.env.user.email or self.env.user.login:
            return formataddr((self.env.user.email or self.env.user.login,self.env.user.email or self.env.user.login))
        raise UserError(_("Unable to send email, please configure the sender's email address."))