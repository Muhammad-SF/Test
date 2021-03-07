# -*- coding: utf-8 -*-

from odoo import fields, models, exceptions, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def compute_default_product_id(self):
        context = self.env.context
        employee_obj = self.env['hr.employee']
        employee = employee_obj.search([('user_id', '=', context.get('user_id') or self.env.uid)])
        for emp in employee:
            if emp and emp.id:
                if emp.product_id:
                    return emp.product_id
        return False

    @api.model
    def compute_default_journal_id(self):
        journal_id = False
        context = self.env.context
        invoice = context.get('invoice', False)
        if invoice and invoice.id:
            origin = invoice.origin
            sale = self.env['sale.order'].search([
                ('name', '=', origin)
            ], limit=1)
            if sale and sale.id:
                journal_id = self.env.ref('stable_hr_timesheet_invoice.sale_journal')
        if not journal_id:
            active_model = context.get('active_model')
            if active_model == 'hr.expense' or context.get('search_default_submitted', False):
                journal_id = self.env.ref('stable_hr_timesheet_invoice.expense_journal')
        if not journal_id:
            ju = context.get('invoice')
            if ju:
                pu = self.env['account.invoice'].search([('id', '=', ju.id)], limit=1)
                if pu and pu.id:
                    if context.get('journal_type') == 'sale':
                        journal_id = self.env['account.journal'].search([('name', '=', 'Customer Invoices')]).id
                    if context.get('journal_type') == 'purchase':
                        journal_id = self.env['account.journal'].search([('name', '=', 'Vendor Bills')]).id
        if not journal_id:
            employee_obj = self.env['hr.employee']
            employees = employee_obj.search([('user_id', '=', context.get('user_id') or self.env.uid)])
            if employees:
                for employee in employees:
                    if employee.journal_id:
                        journal_id = employee.journal_id
                    else:
                        journal_id = self.env.ref('stable_hr_timesheet_invoice.timesheet_journal', False)
        return journal_id

    @api.model
    def compute_default_general_account_id(self):
        employee_obj = self.env['hr.employee']
        employees = employee_obj.search([('user_id', '=', self.env.uid)], limit=1)
        if employees:
            employee = employees[0]
            if employee.product_id and employee.product_id.property_account_income_id:
                return employee.product_id.property_account_income_id
            else:
                return employee.product_id.categ_id.property_account_income_categ_id.id

    journal_id         = fields.Many2one('account.journal', 'Journal', default=compute_default_journal_id)
    product_id         = fields.Many2one('product.product', 'Product', default=compute_default_product_id)
    general_account_id = fields.Many2one('account.account', 'Financial Account', ondelete='restrict', default=compute_default_general_account_id, domain=[('deprecated', '=', False)])

    @api.multi
    def compute_general_account_id(self):
        for record in self:
            if record.move_id and record.move_id.account_id:
                record.general_account_id = record.move_id.account_id
            else:
                employee_obj = self.env['hr.employee']
                employees    = employee_obj.search([('user_id', '=', self.env.uid)], limit=1)
                if employees:
                    employee = employees[0]
                    if employee.product_id and employee.product_id.property_account_income_id:
                        record.general_account_id = employee.product_id.property_account_income_id
                    else:
                        record.general_account_id = employee.product_id.categ_id.property_account_income_categ_id.id


    @api.depends('date', 'user_id', 'project_id', 'account_id', 'sheet_id_computed.date_to', 'sheet_id_computed.date_from', 'sheet_id_computed.employee_id')
    def _compute_sheet(self):
        """Links the timesheet line to the corresponding sheet
        """
        for ts_line in self:
            # TODO: Disable project_id
            # if not ts_line.project_id:
            #     continue
            timeshet_journal = self.env.ref('stable_hr_timesheet_invoice.timesheet_journal')
            if timeshet_journal and timeshet_journal.id:
                if ts_line.journal_id and ts_line.journal_id.id:
                    if ts_line.journal_id.id == timeshet_journal.id:
                        sheets = self.env['hr_timesheet_sheet.sheet'].search(
                            [('date_to', '>=', ts_line.date), ('date_from', '<=', ts_line.date),
                             ('employee_id.user_id.id', '=', ts_line.user_id.id),
                             ('state', 'in', ['draft', 'new'])])
                        if sheets:
                            # [0] because only one sheet possible for an employee between 2 dates
                            ts_line.sheet_id_computed = sheets[0]
                            ts_line.sheet_id = sheets[0]