# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    group_income_expense_matrix = fields.Boolean("Use for income approving matrix menu", implied_group='sg_expensevoucher.group_income_expense_matrix',
                                       help="""Allows to show Income Approving Matrix menu. """)
    group_expense_matrix = fields.Boolean("Use for expense approving matrix menu",
                                                 implied_group='sg_expensevoucher.group_expense_matrix',
                                                 help="""Allows to show Expense Approving Matrix menu. """)

    @api.onchange('is_other_income_approving_matrix','is_other_expense_approving_matrix')
    def onchange_income_expense_matrix(self):
        if self.is_other_income_approving_matrix:
            self.group_income_expense_matrix = True
        else:
            self.group_income_expense_matrix = False
        if self.is_other_expense_approving_matrix:
            self.group_expense_matrix = True
        else:
            self.group_expense_matrix = False

AccountConfigSettings()