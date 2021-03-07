from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import requests
from odoo.http import request


class WhatsappBlast(models.Model):
    _name = 'whatsapp.blast'

    name = fields.Char('Name')
    partner_ids = fields.One2many('res.partner','whatsapp_id','Partners')
    content = fields.Text('Content')
    state = fields.Selection([
            ('draft','Draft'),
            ('sent', 'Sent'),
            ('fail', 'Failed'),
        ], string='Status', index=True, readonly=True, default='draft')
    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id)
    
    @api.multi
    def action_sent_message(self):
        if self.company_id:
            success = False
            for partner in self.partner_ids:
                apikey = self.company_id.api_key
                number = partner.whatsapp_no
                msg = self.content
                url = """https://panel.apiwha.com/send_message.php?apikey="""+apikey+"""&number="""+number+"""&text="""+msg+""""""
                r = requests.get(url = url) 
                data = r.json()
                if data.get('success') == False:
                    self.write({'state': 'fail'})
                else:
                    self.write({'state': 'sent'})

class ResCompany(models.Model):
    _inherit = 'res.company'

    api_key = fields.Char('Whatsapp API Key')


class WhatsappBlast(models.Model):
    _inherit = 'res.partner'

    whatsapp_id = fields.Many2one('whatsapp.blast','Whatsapp')
    whatsapp_no = fields.Char('Whatsapp Number')