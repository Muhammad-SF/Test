# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from lxml import etree


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    def _get_income_expense_config(self):
        for voucher in self:
            is_other_income_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
                                                                                        'is_other_income_approving_matrix')
            is_other_expense_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
                                                                                         'is_other_expense_approving_matrix')
            if is_other_income_approving_matrix and is_other_income_approving_matrix == True:
                voucher.is_income_matrix = True
            if is_other_expense_approving_matrix and is_other_expense_approving_matrix == True:
                voucher.is_expense_matrix = True

    def _get_approved_user(self):
        for record in self:
            if record.income_expense_approved_user_id == self.env.user:
                record.is_approved_user = True

    @api.depends('income_expense_approving_matrix_id')
    def _get_approval_matrix_lines(self):
        for record in self:
            approval_matrix_lines = []
            if record.income_expense_approving_matrix_id and record.income_expense_approving_matrix_id.income_expense_approving_matrix_line_ids:
                for line in record.income_expense_approving_matrix_id.income_expense_approving_matrix_line_ids:
                    approval_matrix_lines.append((0, 0, {'sequence': line.sequence,
                                         'user_ids': [(6, 0, line.income_expense_user_ids.ids)],
                                         'min_amount': line.min_amount,
                                         'max_amount': line.max_amount,
                                         'min_approver': line.min_approver,
                                         }))
            if approval_matrix_lines:
                record.income_expense_approving_line_ids = approval_matrix_lines

    account_id = fields.Many2one('account.account', 'Bank/Cash Account',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        domain="[('deprecated', '=', False), ('internal_type','=', (pay_now == 'pay_now' and 'liquidity' or voucher_type == 'purchase' and 'payable' or 'receivable'))]")
    pay_now = fields.Selection([
            ('pay_now', 'Pay Directly'),
        ], 'Payment', index=True, readonly=True, states={'draft': [('readonly', False)]}, default='pay_now')
    income_expense_approving_matrix_id = fields.Many2one('income.expense.approving.matrix', string='Approving Matrix')
    income_expense_approved_user_id = fields.Many2one('res.users', string='Approved User')
    is_approved_user = fields.Boolean(compute='_get_approved_user', string='User Approved')
    income_expense_approving_line_ids = fields.One2many('income.expense.approving.matrix.lines', 'income_expense_approving_id',
                                                         string='Approving Matrix Lines', compute='_get_approval_matrix_lines', store=True)
    state = fields.Selection(selection_add=[('request_for_approval', 'Request For Approval')])
    is_income_matrix = fields.Boolean(compute='_get_income_expense_config', string='Income Matrix')
    is_expense_matrix = fields.Boolean(compute='_get_income_expense_config', string='Expense Matrix')

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(AccountVoucher, self).default_get(fields_list)
    #     is_other_income_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
    #                                                                                 'is_other_income_approving_matrix')
    #     is_other_expense_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
    #                                                                                  'is_other_expense_approving_matrix')
    #     if is_other_income_approving_matrix and is_other_income_approving_matrix == True:
    #         other_income = True
    #     else:
    #         other_income = False
    #     if is_other_expense_approving_matrix and is_other_expense_approving_matrix == True:
    #         other_expense = True
    #     else:
    #         other_expense = False
    #     print"\n\nother incoem:", other_income
    #     print"\n\nOther expense", other_expense
    #     res.update({'is_income_matrix': other_income, 'is_expense_matrix': other_expense})
    #     return res

    @api.model
    def _apply_state_label(self, view_arch, status):
        doc = etree.XML(view_arch)
        is_other_income_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_income_approving_matrix')
        is_other_expense_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_expense_approving_matrix')
        if status:
            for node in doc.xpath("//field[@name='state']"):
                if is_other_income_approving_matrix == True or is_other_expense_approving_matrix == True:
                    node.set('statusbar_visible', "draft,request_for_approval,posted")
                else:
                    node.set('statusbar_visible', "draft,posted")
            # if is_other_income_approving_matrix == False or is_other_expense_approving_matrix == False:
                # for node in doc.xpath("//field[@name='income_expense_approving_matrix_id']"):
                #     node.set("modifiers", '{"invisible":true, "required":false}')
                # for node in doc.xpath("//field[@name='income_expense_approving_line_ids']"):
                #     node.set("modifiers", '{"invisible":true}')
                # for node in doc.xpath("//page[@name='income_approving']"):
                #     node.set("modifiers", '{"invisible":true}')
                # for node in doc.xpath("//page[@name='expense_approving']"):
                #     node.set("modifiers", '{"invisible":true}')
                # for node in doc.xpath("//button[@name='action_request_approval']"):
                #     node.set("modifiers", '{"invisible":true}')
            # if is_other_income_approving_matrix == True or is_other_expense_approving_matrix == True:
            #     for node in doc.xpath("//button[@name='proforma_voucher']"):
            #         node.set("modifiers", '{"invisible":true}')
        return etree.tostring(doc, encoding='unicode')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Hide/Show 'Approving Matrix and Next Approver' fields of other income and other expense form view according to account.config.settings's other income / other expense Approving Matrix field. """
        result = super(AccountVoucher, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            status = True
            result['arch'] = self._apply_state_label(result['arch'], status)
        return result

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(AccountVoucher, self).fields_get(allfields, attributes=attributes)
        is_other_income_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_income_approving_matrix')
        is_other_expense_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_expense_approving_matrix')
        if is_other_income_approving_matrix == False or is_other_expense_approving_matrix == False:
            res['state']['selection'] = [('draft', 'Draft'), ('cancel', 'Cancelled'), ('proforma', 'Pro-forma'),
                                         ('posted', 'Posted')]
        else:
            res['state']['selection'] = [('draft', 'Draft'), ('request_for_approval', 'Request For Approval'),
                                         ('cancel', 'Cancelled'), ('proforma', 'Pro-forma'), ('posted', 'Posted')]
        return res

    @api.multi
    def action_request_approval(self):
        for voucher in self:
            is_other_income_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_income_approving_matrix')
            is_other_expense_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_expense_approving_matrix')
            #For other income
            if is_other_income_approving_matrix == True and voucher.income_expense_approving_matrix_id.type == 'income':
                if voucher.branch_id and voucher.income_expense_approving_matrix_id and voucher.income_expense_approving_matrix_id.income_expense_branch_ids and voucher.branch_id not in voucher.income_expense_approving_matrix_id.income_expense_branch_ids:
                    raise ValidationError(_('Other income and approving matrix branches should be same.'))
                voucher.write({'state': 'request_for_approval', 'move_id': False, 'income_expense_approved_user_id': False})
            # else:
            #     voucher.sudo().action_move_line_create()
            # For other expense
            elif is_other_expense_approving_matrix == True and voucher.income_expense_approving_matrix_id.type == 'expense':
                if voucher.branch_id and voucher.income_expense_approving_matrix_id and voucher.income_expense_approving_matrix_id.income_expense_branch_ids and voucher.branch_id not in voucher.income_expense_approving_matrix_id.income_expense_branch_ids:
                    raise ValidationError(_('Other expense and approving matrix branches should be same.'))
                voucher.write(
                    {'state': 'request_for_approval', 'move_id': False, 'income_expense_approved_user_id': False})
            else:
                voucher.sudo().action_move_line_create()
        return True

    @api.multi
    def action_approve(self):
        for record in self:
            is_other_income_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_income_approving_matrix')
            is_other_expense_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_other_expense_approving_matrix')
            #For other income
            if is_other_income_approving_matrix == True and record.income_expense_approving_matrix_id.type == 'income':
                lines_amount = record.income_expense_approving_line_ids.filtered(
                    lambda r: r.approved == False and record.amount >= r.min_amount and record.amount <= r.max_amount)
                sorted_seq_data = lines_amount.sorted('sequence')
                next_seq = 0
                if sorted_seq_data:
                    next_seq = sorted_seq_data[0].sequence
                approving_matrix_lines = lines_amount.filtered(lambda r: r.sequence == next_seq)
                approved_list = []
                if lines_amount:
                    for approve_matrix_line in approving_matrix_lines:
                        if approve_matrix_line.user_ids and len(approve_matrix_line.user_ids) > 0:
                            if approve_matrix_line.min_approver >= 1:
                                if is_other_income_approving_matrix == True and record.branch_id in record.income_expense_approving_matrix_id.income_expense_branch_ids and record.amount >= approve_matrix_line.min_amount and record.amount <= approve_matrix_line.max_amount:
                                    if self.env.user.id not in approve_matrix_line.user_ids.ids:
                                        raise ValidationError(str(self.env.user.name) + ' ' + 'is not an approver/does not belongs to sequence!')
                                    if self.env.user.id in approve_matrix_line.user_ids.ids and approve_matrix_line.min_approver > 0 and (
                                            (len(approve_matrix_line.user_ids.ids) <= approve_matrix_line.min_approver and len(approve_matrix_line.user_ids.ids) == (len(approve_matrix_line.approved_user_ids.ids) + 1)) or (len(approve_matrix_line.user_ids.ids) >= approve_matrix_line.min_approver and (len(approve_matrix_line.approved_user_ids.ids) + 1) == approve_matrix_line.min_approver)):
                                        approve_matrix_line.write({'approved': True})
                                        approved_list.append(approve_matrix_line)
                                        if len(approved_list) == len(lines_amount):
                                            record.sudo().action_move_line_create()
                                    else:
                                        approve_matrix_line.approved_user_ids += self.env.user
                                    record.write({'income_expense_approved_user_id': self.env.user.id})
                                else:
                                    record.sudo().action_move_line_create()
                            else:
                                record.sudo().action_move_line_create()
                        else:
                            record.sudo().action_move_line_create()
            # else:
            #     record.sudo().action_move_line_create()
            # For other income
            elif is_other_expense_approving_matrix == True and record.income_expense_approving_matrix_id.type == 'expense':
                lines_amount = record.income_expense_approving_line_ids.filtered(
                    lambda
                        r: r.approved == False and record.amount >= r.min_amount and record.amount <= r.max_amount)
                sorted_seq_data = lines_amount.sorted('sequence')
                next_seq = 0
                if sorted_seq_data:
                    next_seq = sorted_seq_data[0].sequence
                approving_matrix_lines = lines_amount.filtered(lambda r: r.sequence == next_seq)
                approved_list = []
                if lines_amount:
                    for approve_matrix_line in approving_matrix_lines:
                        if approve_matrix_line.user_ids and len(approve_matrix_line.user_ids) > 0:
                            if approve_matrix_line.min_approver >= 1:
                                if is_other_expense_approving_matrix == True and record.branch_id in record.income_expense_approving_matrix_id.income_expense_branch_ids and record.amount >= approve_matrix_line.min_amount and record.amount <= approve_matrix_line.max_amount:
                                    if self.env.user.id not in approve_matrix_line.user_ids.ids:
                                        raise ValidationError(str(
                                            self.env.user.name) + ' ' + 'is not an approver/does not belongs to sequence!')
                                    if self.env.user.id in approve_matrix_line.user_ids.ids and approve_matrix_line.min_approver > 0 and (
                                            (len(
                                                approve_matrix_line.user_ids.ids) <= approve_matrix_line.min_approver and len(
                                                approve_matrix_line.user_ids.ids) == (
                                                     len(approve_matrix_line.approved_user_ids.ids) + 1)) or (len(
                                        approve_matrix_line.user_ids.ids) >= approve_matrix_line.min_approver and (
                                                                                                                      len(
                                                                                                                          approve_matrix_line.approved_user_ids.ids) + 1) == approve_matrix_line.min_approver)):
                                        approve_matrix_line.write({'approved': True})
                                        approved_list.append(approve_matrix_line)
                                        if len(approved_list) == len(lines_amount):
                                            record.sudo().action_move_line_create()
                                    else:
                                        approve_matrix_line.approved_user_ids += self.env.user
                                    record.write({'income_expense_approved_user_id': self.env.user.id})
                                else:
                                    record.sudo().action_move_line_create()
                            else:
                                record.sudo().action_move_line_create()
                        else:
                            record.sudo().action_move_line_create()
            else:
                record.sudo().action_move_line_create()
        return True

    @api.multi
    def action_decline(self):
        for voucher in self:
            voucher.write({'income_expense_approved_user_id': False, 'move_id': False, 'state': 'draft'})
            if voucher.income_expense_approving_line_ids:
                for approval_line in voucher.income_expense_approving_line_ids:
                    approval_line.approved = False
        return True

AccountVoucher()

class accountvoucherline(models.Model):
    _inherit='account.voucher.line'

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id.default_code:
            self.name = self.product_id.default_code
        else:
            self.name = self.product_id.name

    @api.onchange('product_id')
    def onchange_product_account(self):
        if self.voucher_id.voucher_type == 'sale' and self.product_id.categ_id.property_account_income_categ_id:
            self.account_id = self.product_id.categ_id.property_account_income_categ_id.id

        if self.voucher_id.voucher_type == 'purchase' and self.product_id.categ_id.property_account_expense_categ_id:
            self.account_id = self.product_id.categ_id.property_account_expense_categ_id.id

accountvoucherline()

class IncomeExpenseApprovingMatrixLines(models.Model):
    _name = 'income.expense.approving.matrix.lines'
    _description = 'Approving Matrix Lines'

    sequence = fields.Integer('Sequence')
    user_ids = fields.Many2many('res.users', string='Users')
    approved_user_ids = fields.Many2many('res.users', 'approved_users_income_expense_amount_rel', 'user_ids', 'income_expense_matrix_line_id', string='Approved Users')
    min_amount = fields.Float('Minimum Amount')
    max_amount = fields.Float('Maximum Amount')
    min_approver = fields.Integer('Minimum Approver', default=1)
    approved = fields.Boolean("Approved")
    income_expense_approving_id = fields.Many2one('account.voucher', string='Voucher')

IncomeExpenseApprovingMatrixLines()