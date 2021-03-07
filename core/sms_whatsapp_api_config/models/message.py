# -*- coding: utf-8 -*-
from odoo import models, fields, api
import urllib
import requests

class MailMessageSettings(models.Model):
    _name = 'mail.message.settings'
    _description = 'Mail Message Settings'

    name = fields.Char('Name', required=True)
    message_type = fields.Selection([('sms','SMS'),('whatsapp','WhatsApp')], default='sms', string='Message Type')
    auth_type = fields.Selection([('username','Username & Password'),('apikey','API Key / Token')], default='username', string='Type')
    username = fields.Char('Username')
    password = fields.Char('Password')
    url = fields.Char('Service URL')
    key_token = fields.Char('API Key / Token')
    default = fields.Boolean('Is Default?')

    @api.multi
    def set_default(self):
        self.write({'default': True})
        other_ids = self.search([('id','not in', self.ids),('message_type','=',self.message_type)])
        other_ids.write({'default': False})

MailMessageSettings()

class MailMessageLog(models.Model):
    _name = 'mail.message.log'
    _description = 'Mail Message Log'
    _rec_name = 'mobile_no'
    _order = 'id desc'

    mobile_no = fields.Char('Mobile Number')
    creation_date = fields.Datetime('Creation Date', default=fields.Datetime.now)
    message = fields.Text('Message')
    url = fields.Char('Service URL')
    response = fields.Text('Response')
    state = fields.Selection([('draft','Draft'),('done','Sent'),('fail','Failed')], default='draft', string='Status')
    message_settings_id = fields.Many2one('mail.message.settings', 'Settings')

    @api.multi
    def prepare_url(self):
        url = self.message_settings_id.url
        if '<%username%>' in url:
            url = url.replace('<%username%>', self.message_settings_id.username)
        if '<%password%>' in url:
            url = url.replace('<%password%>', self.message_settings_id.password)
        if '<%key_token%>' in url:
            url = url.replace('<%key_token%>', self.message_settings_id.key_token)
        if '<%message%>' in url:
            message = urllib.quote_plus(self.message)
            url = url.replace('<%message%>', message)
        if '<%number%>' in url:
            number = urllib.quote_plus(self.mobile_no)
            url = url.replace('<%number%>', number)
        return url

    @api.multi
    def action_send(self):
        try:
            url = self.prepare_url()
            response = requests.get(url)
            self.write({'state': 'done', 'url': url, 'response': response.text})
        except Exception, e:
            self.write({'state': 'fail', 'response': str(e)})

    @api.multi
    def action_retry(self):
        self.write({'state': 'draft'})

MailMessageLog()