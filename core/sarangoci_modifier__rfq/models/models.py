# -*- coding: utf-8 -*-

from odoo import models, fields, api,SUPERUSER_ID

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    approver_id     = fields.Many2one('hr.employee','Approver')
    approval_ok     = fields.Boolean(compute='check_amount_total')
    check_approver  = fields.Boolean(compute='check_approver_user')
    # type_order      = fields.Selection([('internal','Internal Order'),('external','External Order')],string='Type of Order',default='internal')

    @api.depends('approver_id')
    def check_approver_user(self):
        for record in self:
            if record.approver_id and record.approver_id.user_id == self.env.user or self._uid == SUPERUSER_ID:
                record.check_approver = True
            else:
                record.check_approver = False
            if record.amount_total < 10000000:
                record.check_approver = True

    @api.depends('amount_total')
    def check_amount_total(self):
        for record in self:
            if record.amount_total >= 10000000 and not self.env.user.has_group('purchase.group_purchase_manager'):
                record.approval_ok = True
            else:
                record.approval_ok = False

    @api.multi
    def get_signup_url(self):
        contex_signup = dict(self._context, signup_valid=True)
        url = \
        self.env.user.partner_id._get_signup_url_for_action(action='/mail/view', model=self._name, res_id=self.id)[
            self.env.user.partner_id.id]
        url_data = str(url).split('web/')
        actual_url = ''
        if '&token=' in url_data[1]:
            token_value = str(url_data[1].split('&token=')[1]).split('&db')[0]
            actual_url = url_data[0] + 'web/#db=' + self._cr.dbname + '&model=' + self._name + '&id=' + str(
                self.id) + '&view_type=form&token=' + token_value
        else:
            actual_url = url_data[0] + 'web/#db=' + self._cr.dbname + '&model=' + self._name + '&id=' + str(
                self.id) + '&view_type=form'
        return actual_url

    @api.multi
    def send_email(self):
        mail_vals = {}
        for mail in self:
            url = self.get_signup_url()
            email_from = self.env.user.login
            email_to = mail.approver_id.user_id.login
            subject = 'You have a RFQ need approval'
            message = """
                            <html>
                                <head>
                                    Dear %s,
                                </head></br>
                                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<body>
                                    You have a RFQ (<a href="%s" target="_blank">%s</a>) waiting for your approval.<br/><br/>
                                    Requestor : %s. <br/>
                                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>Thank You</strong>
                                </body>
                            <html>""" % (mail.approver_id.user_id.name, url, mail.name, self.env.user.name)
            mail_vals['email_from'] = email_from
            mail_vals['email_to'] = email_to
            mail_vals['subject'] = subject
            mail_vals['body_html'] = message
            self.env['mail.mail'].create(mail_vals)
        return True

    # Mail creation for approval user
    @api.multi
    def button_confirm(self):
        
        if self.approval_ok == True:

            for order in self:
                if order.state not in ['draft', 'sent']:
                    continue
                order._add_supplier_to_product()
                if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()

                mail_vals = {}
                if order.approver_id.user_id:
                    partner_id = self.env['res.partner'].search([('name', '=', order.approver_id.user_id.name)])
                    url = self.get_signup_url()
                    email_from = self.env.user.login
                    subject = 'You have a RFQ need approval'
                    message = """
                                    <html>
                                        <head>
                                            Dear %s,
                                        </head>
                                        <body>
                                            You have a RFQ (<a href="%s" target="_blank">%s</a>) waiting for your approval.<br/><br/>
                                            Requestor : %s. <br/>
                                            <strong>Thank You</strong>
                                        </body>
                                    <html>""" % (order.approver_id.user_id.name, url, order.name, self.env.user.name)
                    mail_vals['subject'] = subject
                    mail_vals['body'] = '<pre>%s</pre>' % message
                    mail_vals['email_from'] = email_from
                    mail_vals['partner_ids'] = [(6, 0, [partner_id.id])],
                    mail_vals['needaction_partner_ids'] = [(6, 0, [partner_id.id])]
                    thread_pool = self.env['mail.message'].create(mail_vals)
                    thread_pool.needaction_partner_ids = [(6, 0, [partner_id.id])]
                    order.send_email()
                    order.write({'state': 'to approve'})
            return True
        else:
            res = super(purchase_order,self).button_confirm()
            return res

    @api.multi
    def button_approve(self, force=False):
        for record in self:
            record._create_picking()
            if record.company_id.po_lock == 'lock':
                record.write({'state': 'done'})
            if record.check_approver == True:
                record.write({'state': 'purchase', 'date_approve': fields.Date.context_today(self)})
        return {}

# class stock_move(models.Model):
#     _inherit = 'stock.move'

    # type_order = fields.Selection([('internal','Internal Order'),('external','External Order')],string='Type of Order',related='purchase_line_id.order_id.type_order')