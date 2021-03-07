# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, api, _

class ReceiptPaymentApprovingMatrix(models.Model):
    _name = 'receipt.payment.approving.matrix'
    _description = 'Customer Receipt / Supplier Payment Approving Matrix'
    _inherit = ['mail.thread']
    _rec_name = 'name'

    name = fields.Char('Name')
    receipt_payment_branch_ids = fields.Many2many('res.branch', string='Branch')
    receipt_payment_approving_matrix_line_ids = fields.One2many('receipt.payment.approving.matrix.line', 'receipt_payment_approving_matrix_id', string='Approving Matrix Lines')
    company_id = fields.Many2one('res.company', string='Company')
    is_customer_supplier = fields.Boolean('Is Customer Supplier')
    type = fields.Selection([('customer_receipt', 'Customer Receipt'), ('supplier_payment', 'Supplier Payment')], default='customer_receipt', required=True, string='Type')

    @api.onchange('company_id', 'receipt_payment_branch_ids')
    def onchange_branch(self):
        if self.company_id:
            self.receipt_payment_branch_ids = []
            self.receipt_payment_approving_matrix_line_ids = []
        if self.receipt_payment_branch_ids:
            if self.receipt_payment_approving_matrix_line_ids:
                line_list = []
                for line in self.receipt_payment_approving_matrix_line_ids:
                    user_list = []
                    if line.receipt_payment_user_ids:
                        for user in line.receipt_payment_user_ids:
                            for cmp in user.company_ids:
                                receipt_payment_branch_company_ids = [receipt_payment_branch.company_id for
                                                                     receipt_payment_branch in
                                                                     self.receipt_payment_branch_ids]
                                if cmp in receipt_payment_branch_company_ids:
                                    user_list.append(user.id)

                    if user_list:
                        line.receipt_payment_user_ids = user_list
                        line.write({'receipt_payment_user_ids': user_list})
                        line.write({'receipt_payment_user_ids': [(6, 0, user_list)]})
                        del user_list[:]
                        line_list.append(line.id)
                self.receipt_payment_approving_matrix_line_ids = line_list

ReceiptPaymentApprovingMatrix()

class ReceiptPaymenthApprovingMatrixLines(models.Model):
    _name = 'receipt.payment.approving.matrix.line'
    _description = 'Customer Receipt / Supplier Payment Approving Matrix Lines'

    @api.depends('receipt_payment_approving_matrix_id.receipt_payment_approving_matrix_line_ids',
                 'receipt_payment_approving_matrix_id.receipt_payment_approving_matrix_line_ids.receipt_payment_user_ids')
    def _get_receipt_payment_matrix_sequence(self):
        for line in self:
            no = 0
            for matrix in line.receipt_payment_approving_matrix_id.receipt_payment_approving_matrix_line_ids:
                no += 1
                matrix.sequence = no

    sequence = fields.Integer(compute='_get_receipt_payment_matrix_sequence', string='Sequence')
    receipt_payment_user_ids = fields.Many2many('res.users', string='Users')
    min_amount = fields.Float('Minimum Amount')
    max_amount = fields.Float('Maximum Amount')
    min_approver = fields.Integer('Minimum Approver', default=1)
    receipt_payment_approving_matrix_id = fields.Many2one('receipt.payment.approving.matrix', string='Customer Receipt / Supplier Payment Approving Matrix')

    # @api.model
    # def default_get(self, fields):
    #     res = super(ReceiptPaymenthApprovingMatrixLines, self).default_get(fields)
    #     next_sequence = 1
    #     if self._context.get('receipt_payment_approving_matrix_line_ids'):
    #         if len(self._context.get('receipt_payment_approving_matrix_line_ids')) > 0:
    #             next_sequence = len(self._context.get('receipt_payment_approving_matrix_line_ids')) + 1
    #     res.update({'sequence': next_sequence})
    #     return res

ReceiptPaymenthApprovingMatrixLines()

