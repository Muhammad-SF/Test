from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import ustr
from odoo.exceptions import UserError



class MrpConfigSettings(models.TransientModel):
    _inherit = 'mrp.config.settings'

    send_whatsapp_notification = fields.Boolean(string="Send Whatsapp Notification when SO Confirm", default=False)
    user_ids = fields.Many2many('res.users', 'mrp_config_user_rel', 'config_id', 'user_id', string="Send Notification To")
    
    send_email_notification = fields.Boolean(string="Send Email Notification when SO Confirm", default=False)
    send_email_user_ids = fields.Many2many('res.users', 'mrp_config_email_user_rel', 'config_id', 'email_user_id', string="Send Email Notification To")
    
    send_dashboard_notification = fields.Boolean(string="Send Dashboard Notification when SO Confirm", default=False)
    send_dashboard_user_ids = fields.Many2many('res.users', 'mrp_config_dashboard_user_rel', 'config_id', 'dahsboard_user_id', string="Send Dashboard Notification To")
    
    
    @api.model
    def get_default_send_whatsapp_notification(self, fields):
        send_whatsapp_notification = self.env.ref('so_to_mo_whatsapp.send_whatsapp_notification').value
        if send_whatsapp_notification == 'False':
            return {'send_whatsapp_notification': False}
        if send_whatsapp_notification == 'True':
            return {'send_whatsapp_notification': True}

    @api.multi
    def set_default_send_whatsapp_notification(self):
        for record in self:
            if record.send_whatsapp_notification:
                self.env.ref('so_to_mo_whatsapp.send_whatsapp_notification').write({'value': 'True'})
            else:
                self.env.ref('so_to_mo_whatsapp.send_whatsapp_notification').write({'value': 'False'})
    
    ########email
    @api.model
    def get_default_send_email_notification(self, fields):
        send_email_notification = self.env.ref('so_to_mo_whatsapp.send_email_notification_id').value
        if send_email_notification == 'False':
            return {'send_email_notification': False}
        if send_email_notification == 'True':
            return {'send_email_notification': True}

    @api.multi
    def set_default_send_email_notification(self):
        for record in self:
            if record.send_email_notification:
                self.env.ref('so_to_mo_whatsapp.send_email_notification_id').write({'value': 'True'})
            else:
                self.env.ref('so_to_mo_whatsapp.send_email_notification_id').write({'value': 'False'})

    ########Dashboard notification
    @api.model
    def get_default_send_dashboard_notification(self, fields):
        send_dashboard_notification = self.env.ref('so_to_mo_whatsapp.send_dashboard_notification_id').value
        if send_dashboard_notification == 'False':
            return {'send_dashboard_notification': False}
        if send_dashboard_notification == 'True':
            return {'send_dashboard_notification': True}

    @api.multi
    def set_default_send_dashboard_notification(self):
        for record in self:
            if record.send_dashboard_notification:
                self.env.ref('so_to_mo_whatsapp.send_dashboard_notification_id').write({'value': 'True'})
            else:
                self.env.ref('so_to_mo_whatsapp.send_dashboard_notification_id').write({'value': 'False'})
                
    
    @api.model
    def get_default_values(self, fields):
        IrValues = self.env['ir.values'].sudo()
        user_ids = IrValues.get_default('mrp.config.settings', 'user_ids')
        email_user_ids = IrValues.get_default('mrp.config.settings', 'send_email_user_ids')
        notification_user_ids = IrValues.get_default('mrp.config.settings', 'send_dashboard_user_ids')
        lines = False
        email_lines = False
        notification_lines = False
        if user_ids:
            lines = [(6, 0, user_ids)]
        if email_user_ids:
            email_lines = [(6, 0, email_user_ids)]
        if notification_user_ids:
            notification_lines = [(6, 0, notification_user_ids)]
        return {
            'user_ids': lines,
            'send_email_user_ids': email_lines,
            'send_dashboard_user_ids': notification_lines,
        }

    @api.multi
    def set_default_values(self):
        IrValues = self.env['ir.values'].sudo()
        IrValues.set_default('mrp.config.settings', 'user_ids', self.user_ids.ids)
        IrValues.set_default('mrp.config.settings', 'send_email_user_ids', self.send_email_user_ids.ids)
        IrValues.set_default('mrp.config.settings', 'send_dashboard_user_ids', self.send_dashboard_user_ids.ids)
        
class SaleOrder(models.Model):
    _inherit = "sale.order"

    
    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        whatsapp_message = self.env['whatsapp.message']
        user_pool = self.env['res.users']
        IrValue = self.env['ir.values'].sudo()
        user_ids = IrValue.get_default('mrp.config.settings', 'user_ids')
        send_whatsapp_notification = self.env.ref('so_to_mo_whatsapp.send_whatsapp_notification').value
        #print "\n\n=send_whatsapp_notification======",send_whatsapp_notification,type(send_whatsapp_notification),user_ids,type(user_ids)
        
        send_email_notification = self.env.ref('so_to_mo_whatsapp.send_email_notification_id').value
        #print"send_email_notification==>>",send_email_notification
        send_dashboard_notification = self.env.ref('so_to_mo_whatsapp.send_dashboard_notification_id').value
        #sss
        temp = 0
        if str(send_whatsapp_notification) == 'True':
            for line in self.order_line:
                if line.product_id.mo_creation_settings == 'mp' or line.product_id.mo_creation_settings == 'mo':
                    #print "\n\n===line.product_id======",line.product_id.name
                    temp = 1
                    continue
        login_user = self.env.user
        if temp == 1:
            for user_id in user_ids:
                user_obj = user_pool.browse(user_id)
                msg = '''Dear %s,\r\n\r\n'''
                msg += '''%s has just approved the Sales Order %s on %s .\r\n\r\n'''
                msg += '''Click here to view: \r\n\r\n'''
                body = ustr(msg)%(user_obj.name,login_user.name,self.name,self.confirmation_date)
                            
                whatsapp_number = user_obj.whatsapp_number
                whatsapp_message_id = whatsapp_message.create({'number': whatsapp_number, 'body': body, 'state': 'draft'})
                whatsapp_message_id.action_sent_message()
                
                
                self._cr.execute('select value from ir_config_parameter where key=%s',('web.base.url',))
                server = str(self._cr.fetchone()[0])
                productions_ids = self.env['mrp.production'].search([('sale_id','in',self.id)])
                for mrp_id in productions_ids:
                    url = server+'/web#id=%s&view_type=%s&model=%s'%(mrp_id.id,'form','mrp.production')
                    whatsapp_message_id2 = whatsapp_message.create({'number': whatsapp_number, 'body': url, 'state': 'draft'})
                    whatsapp_message_id2.action_sent_message()
        
        temp_email = 0
        if str(send_email_notification) == 'True':
            user_ids = IrValue.get_default('mrp.config.settings', 'send_email_user_ids')
            #print"user_ids==>>",user_ids
            #bbbbbbbb
            for line in self.order_line:
                if line.product_id.mo_creation_settings == 'mp' or line.product_id.mo_creation_settings == 'mo':
                    temp_email = 1
                    #aaaaaaa
                    continue
            if temp_email == 1:
                #ssssss
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                for user_id in user_ids:
                    user_obj = user_pool.browse(user_id)
                    #print"user_obj==>>",user_obj,user_obj.name
                    body_dynamic_html = '<p>Dear %s </p>' % user_obj.name
                    body_dynamic_html += '<p>%s has just approved the Sales Order %s on %s .</p>' % (login_user.name,self.name,self.confirmation_date)
                    productions_ids = self.env['mrp.production'].search([('sale_id','in',self.id)])
                    for mrp_id in productions_ids:
                        link = base_url + '/web#id=%s&view_type=form&model=mrp.production' % (mrp_id.id)
                        body_dynamic_html += '<div style = "margin: 16px;">\
                                    <a href=%s style = "padding: 5px 10px; font-size: 12px; line-height: 18px;\
                                     color: #FFFFFF; border-color:#875A7B; text-decoration: none; display: inline-block; \
                                     margin-bottom: 0px; font-weight: 400; text-align: center; vertical-align: middle; \
                                     cursor: pointer; white-space: nowrap; background-image: none; background-color: #875A7B;\
                                     border: 1px solid #875A7B; border-radius:3px">View MO</a></div>' % (link)
                    body_dynamic_html += '<p> Best regards.</div>'
                    #email_from = ''
                    #email_from += user_obj.login+', '
                    #print"email_from===>>>",email_from,email_from[:-2]
                    #ssss
                    if not login_user.partner_id.email:
                        raise UserError(_('Please enter email for partner - %s.')%login_user.partner_id.name)
                    if not user_obj.partner_id.email:
                        raise UserError(_('Please enter email for partner - %s.')%user_obj.partner_id.name)

                    mail_values = {
                        'email_from': login_user.partner_id.email,
                        'reply_to': False,
                        'email_to': user_obj.partner_id.email,
                        'subject': 'SO Confirm Notification',
                        'body_html': body_dynamic_html,
                        'notification': True,
                    }
                    mail = self.env['mail.mail'].create(mail_values)
                    mail.send()
        ####dashboard
        temp_dashboard = 0
        if str(send_dashboard_notification) == 'True':
            user_ids = IrValue.get_default('mrp.config.settings', 'send_dashboard_user_ids')
            for line in self.order_line:
                if line.product_id.mo_creation_settings == 'mp' or line.product_id.mo_creation_settings == 'mo':
                    temp_email = 1
                    continue
            if temp_email == 1:
                #ssssss
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                for user_id in user_ids:
                    user_obj = user_pool.browse(user_id)
                    body_dynamic_html = '<p>Dear %s </p>' % user_obj.name
                    body_dynamic_html += '<p>%s has just approved the Sales Order %s on %s .</p>' % (login_user.name,self.name,self.confirmation_date)
                    productions_ids = self.env['mrp.production'].search([('sale_id','in',self.id)])
                    for mrp_id in productions_ids:
                        link = base_url + '/web#id=%s&view_type=form&model=mrp.production' % (mrp_id.id)
                        body_dynamic_html += '<div style = "margin: 16px;">\
                                    <a href=%s style = "padding: 5px 10px; font-size: 12px; line-height: 18px;\
                                     color: #FFFFFF; border-color:#875A7B; text-decoration: none; display: inline-block; \
                                     margin-bottom: 0px; font-weight: 400; text-align: center; vertical-align: middle; \
                                     cursor: pointer; white-space: nowrap; background-image: none; background-color: #875A7B;\
                                     border: 1px solid #875A7B; border-radius:3px">View MO</a></div>' % (link)
                    body_dynamic_html += '<p> Best regards.</div>'
                    
                    thread_pool = self.env['mail.message'].create({'res_id': self.id,
                                         'subject': 'SO Confirm Notification',
                                         'model': 'sale.order',
                                         'date': datetime.now(),
                                         'email_from': login_user.login,
                                         'author_id': self.env.user.partner_id.id,
                                         'message_type': 'notification',
                                         'body': body_dynamic_html,
                                         'partner_ids': [(6, 0, login_user.mapped('partner_id').ids)],
                                         'needaction_partner_ids': [(4, user_obj.partner_id.id)],})
                    #thread_pool.write({'needaction_partner_ids': [(6, 0, user_obj.mapped('partner_id').ids)]})
                    thread_pool.write({'needaction_partner_ids': [(4, user_obj.partner_id.id)]})
                    
        return res
    
    	
