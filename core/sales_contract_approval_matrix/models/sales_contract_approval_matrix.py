from odoo import api, fields, models, _
from odoo.exceptions import UserError
from urllib import urlencode


class SalesContractApprovalMatrix(models.Model):
    _name = 'sales.contract.approval.matrix'

    name = fields.Char(string='Name', size=128, required=1)
    contract_type_id = fields.Many2one('account.analytic.account.contracttype', string='Contract Type')
    approval_lines = fields.One2many('sales.contract.approval.matrix.line', 'matrix_id', string='Approval Lines')


class SalesContractApprovalMatrixLine(models.Model):
    _name = 'sales.contract.approval.matrix.line'
    _order = "name"

    name = fields.Integer(string='Sequence', size=16, required=1)
    user_ids = fields.Many2many('res.users', id1='approval_id', id2='user_id', string='Users')
    matrix_id = fields.Many2one('sales.contract.approval.matrix', string='Contract Approval Matrix', ondelete='cascade')


class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    STATE_ADD = [
        ('waiting_approval', 'Waiting Approval'),
        ('rejected', 'Rejected'),
    ]

    state = fields.Selection(selection_add=STATE_ADD)
    last_approval_seq = fields.Integer('Last Approval Sequence')

    @api.multi
    def set_open(self):
        res = {}
        #print str(self.contract_type_id)
        for contract in self:
            if contract.contract_type_id:
                search_matrix = self.env['sales.contract.approval.matrix'].search([('contract_type_id', '=', contract.contract_type_id.id)], limit=1)
                if search_matrix:
                    if search_matrix.approval_lines:
                        app_lines = self.env['sales.contract.approval.matrix.line'].search([('matrix_id', '=', search_matrix.id)], limit=1, order='name')
                        seq_no = ''

                        for lines in app_lines:
                            seq_no = lines.name
                            self.send_email_to_approver(contract, lines.user_ids)

                        res = self.write({'state': 'waiting_approval', 'last_approval_seq': int(seq_no)})
                else:
                    res = self.write({'state': 'open'})
            else:
                res = self.write({'state': 'open'})
        return res

    # Send Emails to Approver for accepting/rejecting the contract
    def send_email_to_approver(self, contract, users):
        template_obj = self.env['mail.template'].sudo().search([('name', '=', 'Sales Contract Approval e-mail template for approver')], limit=1)
        if template_obj:

            #   Get user's name and email list
            receipient_username = ''
            receipient_email = ''

            for user in users:
                if receipient_username=='':
                    receipient_username += user.name
                else:
                    receipient_username += ', ' + user.name

                if receipient_email=='':
                    receipient_email += user.partner_id.email
                else:
                    receipient_email += ';' + user.partner_id.email

            # Prepare link to redirect user when click in email
            action = self.env.ref('stable_account_analytic_analysis.action_account_analytic_overdue_all').id
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            contract_url = _("/web#id=%s&view_type=form&model=account.analytic.account&action=%s") % (int(contract.id), int(action))
            contract_url = base_url + contract_url

            subject = template_obj.subject
            subject = subject.replace('--name--', contract.name)

            body = template_obj.body_html
            body = body.replace('--user--', receipient_username)
            body = body.replace('--link--', contract_url)
            body = body.replace('--name--', contract.name)
            body = body.replace('--customer--', contract.partner_id and contract.partner_id.name or '')
            body = body.replace('--manager--', contract.manager_id and contract.manager_id.name or '')

            email_from = contract.manager_id and contract.manager_id.partner_id.email

            mail_values = {'subject': subject, 'body_html': body, 'email_to': receipient_email, 'email_from': email_from}
            create_and_send_email = self.env['mail.mail'].create(mail_values).send()
        return True

    # Send Approved Contract Email Notification to Manager
    def send_approved_email_to_manager(self, contract):
        template_obj = self.env['mail.template'].sudo().search([('name', '=', 'Sales Contract Approved e-mail template for manager')], limit=1)
        if template_obj:

            #   Get user's name and email list
            receipient_username = contract.manager_id and contract.manager_id.name or ''
            receipient_email = contract.manager_id and contract.manager_id.partner_id and contract.manager_id.partner_id.email or ''

            # Prepare link to redirect user when click in email
            action = self.env.ref('stable_account_analytic_analysis.action_account_analytic_overdue_all').id
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            contract_url = _("/web#id=%s&view_type=form&model=account.analytic.account&action=%s") % (int(contract.id), int(action))
            contract_url = base_url + contract_url

            subject = template_obj.subject
            subject = subject.replace('--name--', contract.name)

            body = template_obj.body_html
            body = body.replace('--user--', receipient_username)
            body = body.replace('--link--', contract_url)
            body = body.replace('--name--', contract.name)
            body = body.replace('--customer--', contract.partner_id and contract.partner_id.name or '')

            email_from = contract.manager_id and contract.manager_id.partner_id.email

            mail_values = {'subject': subject, 'body_html': body, 'email_to': receipient_email, 'email_from': email_from}
            create_and_send_email = self.env['mail.mail'].create(mail_values).send()
        return True

    # Send Rejected Contract Email Notification to Manager (this method is called from Wizard)
    def send_rejection_email_to_manager(self, contract, reason):
        template_obj = self.env['mail.template'].sudo().search([('name', '=', 'Sales Contract Rejected e-mail template for manager')], limit=1)
        if template_obj:

            #   Get user's name and email list
            receipient_username = contract.manager_id and contract.manager_id.name or ''
            receipient_email = contract.manager_id and contract.manager_id.partner_id and contract.manager_id.partner_id.email or ''

            # Prepare link to redirect user when click in email
            action = self.env.ref('stable_account_analytic_analysis.action_account_analytic_overdue_all').id
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            contract_url = _("/web#id=%s&view_type=form&model=account.analytic.account&action=%s") % (int(contract.id), int(action))
            contract_url = base_url + contract_url

            reject_reason = reason

            subject = template_obj.subject
            subject = subject.replace('--name--', contract.name)

            body = template_obj.body_html
            body = body.replace('--user--', receipient_username)
            body = body.replace('--link--', contract_url)
            body = body.replace('--name--', contract.name)
            body = body.replace('--customer--', contract.partner_id and contract.partner_id.name or '')
            body = body.replace('--reason--', reject_reason)

            email_from = contract.manager_id and contract.manager_id.partner_id.email

            mail_values = {'subject': subject, 'body_html': body, 'email_to': receipient_email, 'email_from': email_from}
            create_and_send_email = self.env['mail.mail'].create(mail_values).send()

        return True

    @api.multi
    def set_accept(self):
        res = {}

        last_approved_seq = 0
        email_to_approver = False

        for contract in self:
            if contract.last_approval_seq:
                last_approved_seq = int(contract.last_approval_seq)

            if contract.contract_type_id:
                search_matrix = self.env['sales.contract.approval.matrix'].search([('contract_type_id', '=', contract.contract_type_id.id)], limit=1)
                if search_matrix:
                    if search_matrix.approval_lines:
                        app_lines = self.env['sales.contract.approval.matrix.line'].search([('matrix_id', '=', search_matrix.id)], limit=1, order='name desc')
                        higest_seq = int(app_lines.name)

                        next_lines = self.env['sales.contract.approval.matrix.line'].search([('matrix_id', '=', search_matrix.id), ('name', '>', last_approved_seq), ('name', '<=', higest_seq)], limit=1, order='name')
                        if next_lines:
                            if int(next_lines.name)==int(higest_seq):
                                email_to_approver = self.send_email_to_approver(contract, next_lines.user_ids)
                                res = self.write({'state': 'open'})
                            else:
                                email_to_approver = self.send_email_to_approver(contract, next_lines.user_ids)
                                res = self.write({'last_approval_seq': int(next_lines.name)})
                        else:
                            email_to_approver = self.send_approved_email_to_manager(contract)
                            res = self.write({'state': 'open'})
            else:
                res = self.write({'state': 'open'})

            if email_to_approver:
                user = self.env['res.users'].sudo().search([('id', '=', int(self._uid))])
                if user:
                    msg = _("<p><ul><li>Contract Accepted by: %s</li><li>Contract Type: %s</li></ul></p>") % (str(user.name), str(contract.contract_type_id.name))
                    contract.sudo().message_post(body=msg)
        return res


