# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, api, _
from odoo.exceptions import ValidationError

class IncomeExpenseApprovingMatrix(models.Model):
    _name = 'income.expense.approving.matrix'
    _description = 'Other Income / Other Expense Approving Matrix'
    _inherit = ['mail.thread']
    _rec_name = 'name'

    name = fields.Char('Name')
    income_expense_branch_ids = fields.Many2many('res.branch', string='Branch')
    income_expense_approving_matrix_line_ids = fields.One2many('income.expense.approving.matrix.line', 'income_expense_approving_matrix_id', string='Approving Matrix Lines')
    company_id = fields.Many2one('res.company', string='Company')
    is_income_expense = fields.Boolean('Is Income Expense')
    type = fields.Selection([('income', 'Income'), ('expense', 'Expense')], default='income', required=True, string='Type')

    @api.onchange('company_id', 'income_expense_branch_ids')
    def onchange_branch(self):
        if self.company_id:
            self.income_expense_branch_ids = []
            self.income_expense_approving_matrix_line_ids = []
        if self.income_expense_branch_ids:
            if self.income_expense_approving_matrix_line_ids:
                line_list = []
                for line in self.income_expense_approving_matrix_line_ids:
                    user_list = []
                    if line.income_expense_user_ids:
                        for user in line.income_expense_user_ids:
                            for cmp in user.company_ids:
                                income_expense_branch_company_ids = [income_expense_branch.company_id for income_expense_branch in
                                                              self.income_expense_branch_ids]
                                if cmp in income_expense_branch_company_ids:
                                    user_list.append(user.id)

                    if user_list:
                        line.income_expense_user_ids = user_list
                        line.write({'income_expense_user_ids': user_list})
                        line.write({'income_expense_user_ids' : [(6,0,user_list)]})
                        del user_list[:]
                        line_list.append(line.id)
                self.income_expense_approving_matrix_line_ids = line_list

IncomeExpenseApprovingMatrix()

class IncomeExpenseApprovingMatrixLine(models.Model):
    _name = 'income.expense.approving.matrix.line'
    _description = 'Other Income / Other Expense Approving Matrix Lines'

    @api.depends('income_expense_approving_matrix_id.income_expense_approving_matrix_line_ids',
                 'income_expense_approving_matrix_id.income_expense_approving_matrix_line_ids.income_expense_user_ids')
    def _get_income_expense_matrix_sequence(self):
        for line in self:
            no = 0
            for matrix in line.income_expense_approving_matrix_id.income_expense_approving_matrix_line_ids:
                no += 1
                matrix.sequence = no

    sequence = fields.Integer(compute='_get_income_expense_matrix_sequence', string='Sequence')
    income_expense_user_ids = fields.Many2many('res.users', string='Users')
    min_amount = fields.Float('Minimum Amount')
    max_amount = fields.Float('Maximum Amount')
    min_approver = fields.Integer('Minimum Approver', default=1)
    income_expense_approving_matrix_id = fields.Many2one('income.expense.approving.matrix', string='Other Income / Other Expense Approving Matrix')

    # @api.model
    # def default_get(self, fields):
    #     res = super(IncomeExpenseApprovingMatrixLine, self).default_get(fields)
    #     next_sequence = 1
    #     if self._context.get('income_expense_approving_matrix_line_ids'):
    #         if len(self._context.get('income_expense_approving_matrix_line_ids')) > 0:
    #             next_sequence = len(self._context.get('income_expense_approving_matrix_line_ids')) + 1
    #     res.update({'sequence': next_sequence})
    #     return res

IncomeExpenseApprovingMatrixLine()

