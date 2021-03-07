from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import float_round
from datetime import datetime, date
from lxml import etree

# class AccountPayment(models.Model):
#     _inherit = 'account.payment'
#
#     state = fields.Selection(selection_add=[('cancel', 'Cancelled')], string="Status")

class ReceiptPayment(models.Model):
    _name = 'receipt.payment'
    _inherit = ['mail.thread']
    _description = 'Customer Receipts and Supplier Payments'
    _order = 'id desc'

    @api.depends('payment_ids')
    def compute_payment_count(self):
        for record in self:
            record.payment_count = len(record.payment_ids.ids)

    @api.depends('line_cr_ids', 'line_cr_ids.amount', 'line_dr_ids', 'line_dr_ids.amount', 'amount')
    def _compute_amount(self):
        for record in self:
            credit = 0.0
            debit = 0.0
            for line in record.line_cr_ids:
                credit += float_round(line.amount, 2)
            for line in record.line_dr_ids:
                debit += float_round(line.amount, 2)
            if record.type == 'customer':
                diff_amount = record.currency_id.round(float_round(record.amount, 2) + credit - debit)
            else:
                diff_amount = record.currency_id.round(float_round(record.amount, 2) + debit - credit)
            record.diff_amount = float_round(diff_amount, 2)

    def _get_approved_user(self):
        for record in self:
            if record.receipt_payment_approved_user_id == self.env.user:
                record.is_approved_user = True

    def _get_customer_supplier_config(self):
        for receipt in self:
            is_customer_receipt_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
                                                                                            'is_customer_receipt_approving_matrix')
            is_supplier_payment_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
                                                                                            'is_supplier_payment_approving_matrix')
            if is_customer_receipt_approving_matrix and is_customer_receipt_approving_matrix == True:
                receipt.is_customer_matrix = True
            if is_supplier_payment_approving_matrix and is_supplier_payment_approving_matrix == True:
                receipt.is_supplier_matrix = True

    @api.depends('receipt_payment_approving_matrix_id')
    def _get_approval_matrix_lines(self):
        for record in self:
            approval_matrix_lines = []
            if record.receipt_payment_approving_matrix_id and record.receipt_payment_approving_matrix_id.receipt_payment_approving_matrix_line_ids:
                for line in record.receipt_payment_approving_matrix_id.receipt_payment_approving_matrix_line_ids:
                    approval_matrix_lines.append((0, 0, {'sequence': line.sequence,
                                         'user_ids': [(6, 0, line.receipt_payment_user_ids.ids)],
                                         'min_amount': line.min_amount,
                                         'max_amount': line.max_amount,
                                         'min_approver': line.min_approver,
                                         }))
            if approval_matrix_lines:
                record.receipt_payment_approving_line_ids = approval_matrix_lines

    name = fields.Char(default='/', readonly=True, required=True, copy=False, string='Number')
    partner_id = fields.Many2one('res.partner', required=True, string='Partner')
    state = fields.Selection([('draft', 'Draft'), ('request_for_approval', 'Request For Approval'),
                              ('cancel', 'Cancelled'), ('in_progress', 'In Progress'), ('posted', 'Posted')],
        default='draft', copy=False, track_visibility='onchange', string='Status')
    type = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier')], default='customer', required=True, string='Type')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.user.company_id.id, string='Company')
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.user.company_id.currency_id.id, string='Currency')
    amount = fields.Monetary(currency_field='currency_id', string='Total')
    journal_id = fields.Many2one('account.journal', required=True, domain=[('type', 'in', ('bank', 'cash'))], string='Payment Method')
    date = fields.Date('Date', copy=False, required=True, help='Effective date for accounting entries', default=fields.Date.context_today)
    payment_ref = fields.Char('Payment Ref', help='Transaction reference number')
    memo = fields.Char(size=256)
    line_cr_ids = fields.One2many('receipt.payment.credit', 'receipt_payment_id', copy=False, string='Credits')
    line_dr_ids = fields.One2many('receipt.payment.debit', 'receipt_payment_id', copy=False, string='Debits')
    diff_amount = fields.Monetary(compute='_compute_amount', currency_id='currency_id', string='Difference Amount')
    payment_id = fields.Many2one('account.payment', copy=False, string='Payments')
    payment_ids = fields.Many2many('account.payment', 'receipt_payment_rel', copy=False, string='Payments')
    payment_count = fields.Integer(compute='compute_payment_count', string='# of Payments')
    payment_difference_handling = fields.Selection([('without_writeoff', 'Keep Open'), ('reconcile', 'Reconcile Payment Balance')],
        'Payment Difference', default='without_writeoff', state={'draft': [('readonly', False)]},
        help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the payment(s)")
    comment = fields.Char('Counterpart Comment', readonly=True, states={'draft': [('readonly', False)]}, default='Conterpart')
    writeoff_acc_id = fields.Many2one('account.account', 'Counterpart Account', readonly=True, states={'draft': [('readonly', False)]})
    narration = fields.Text('Notes', readonly=True, states={'draft': [('readonly', False)]})
    move_line_id = fields.Char('Move Line ID')
    journal_entry_id = fields.Many2one('account.move', 'Journal Entry')
    receipt_payment_approving_matrix_id = fields.Many2one('receipt.payment.approving.matrix', string='Approving Matrix')
    receipt_payment_approved_user_id = fields.Many2one('res.users', string='Approved User')
    is_approved_user = fields.Boolean(compute='_get_approved_user', string='User Approved')
    receipt_payment_approving_line_ids = fields.One2many('receipt.payment.approving.matrix.lines', 'receipt_payment_approving_id',
                                                   string='Approving Matrix Lines',
                                                   compute='_get_approval_matrix_lines', store=True)
    branch_id = fields.Many2one('res.branch', string='Branch')
    is_customer_matrix = fields.Boolean(compute='_get_customer_supplier_config', string='Customer Matrix')
    is_supplier_matrix = fields.Boolean(compute='_get_customer_supplier_config', string='Supplier Matrix')

    # @api.model
    # def default_get(self, fields_list):
    #     res = super(ReceiptPayment, self).default_get(fields_list)
    #     is_customer_receipt_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
    #                                                                                     'is_customer_receipt_approving_matrix')
    #     is_supplier_payment_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings',
    #                                                                                     'is_supplier_payment_approving_matrix')
    #     if is_customer_receipt_approving_matrix and is_customer_receipt_approving_matrix == True:
    #         customer_matrix = True
    #     else:
    #         customer_matrix = False
    #     if is_supplier_payment_approving_matrix and is_supplier_payment_approving_matrix == True:
    #         supplier_matrix = True
    #     else:
    #         supplier_matrix = False
    #     res.update({'is_customer_matrix': customer_matrix, 'is_supplier_matrix': supplier_matrix})
    #     return res

    @api.onchange('line_cr_ids','line_dr_ids')
    def onchange_allocate_total(self):
        if self.line_dr_ids or self.line_cr_ids:
            if self._context.get('form_view_ref') and (self._context.get('form_view_ref') == 'sg_partner_payment.view_customer_receipt_form' or self._context.get('form_view_ref') == 'sg_partner_payment.view_supplier_payment_form'):
                debit_amount = 0.0
                for debit in self.line_dr_ids:
                    debit_amount += debit.amount
                credit_amount = 0.0
                for credit in self.line_cr_ids:
                    credit_amount += credit.amount
                if self.type == 'customer':
                    self.amount = debit_amount - credit_amount
                else:
                    self.amount = credit_amount - debit_amount
            else:
                amount = 0.0
                for debit in self.line_dr_ids:
                    if debit.reconcile:
                        amount += debit.amount
                for credit in self.line_cr_ids:
                    if credit.reconcile:
                        amount += credit.amount
                self.amount = amount

    @api.onchange('payment_difference_handling')
    def onchange_payment_difference_handling(self):
        if self.payment_difference_handling != 'reconcile':
            self.writeoff_acc_id = ''

    @api.model
    def create(self, vals):
        if 'type' in vals and vals['type'] and vals['type'] == 'customer':
            vals['name'] = self.env['ir.sequence'].next_by_code('receipt.payment.customer')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('receipt.payment.supplier')
        receipt_payment_id = super(ReceiptPayment, self).create(vals)
        message_ids = receipt_payment_id.sudo().message_ids.ids
        if message_ids:
            message = ''
            message_id = self.env['mail.message'].sudo().browse(min(message_ids))
            if receipt_payment_id.type == 'customer':
                message = '<p>Customer Receipts created</p>'
            elif receipt_payment_id.type == 'supplier':
                message = '<p>Supplier Payments created</p>'
            if message_id and message:
                message_id.sudo().write({'body': message})
        return receipt_payment_id

    @api.model
    def _apply_state_label(self, view_arch, status):
        doc = etree.XML(view_arch)
        is_customer_receipt_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_customer_receipt_approving_matrix')
        is_supplier_payment_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_supplier_payment_approving_matrix')
        if status:
            for node in doc.xpath("//field[@name='state']"):
                if is_customer_receipt_approving_matrix == True or is_supplier_payment_approving_matrix == True:
                    node.set('statusbar_visible', "draft,request_for_approval,posted")
                else:
                    node.set('statusbar_visible', "draft,posted")
            # if is_customer_receipt_approving_matrix == False or is_supplier_payment_approving_matrix == False:
            #     for node in doc.xpath("//field[@name='receipt_payment_approving_matrix_id']"):
            #         node.set("modifiers", '{"invisible":true, "required":false}')
            #     for node in doc.xpath("//field[@name='receipt_payment_approving_line_ids']"):
            #         node.set("modifiers", '{"invisible":true}')
            #     for node in doc.xpath("//field[@name='branch_id']"):
            #         node.set("modifiers", '{"invisible":true, "required":false}')
            #     for node in doc.xpath("//page[@name='receipt_approving']"):
            #         node.set("modifiers", '{"invisible":true}')
            #     for node in doc.xpath("//page[@name='payment_approving']"):
            #         node.set("modifiers", '{"invisible":true}')
            # if is_customer_receipt_approving_matrix == True and is_supplier_payment_approving_matrix == True:
            #     for node in doc.xpath("//button[@name='action_validate']"):
            #         node.set('string', "Request For Approval")
            # if is_supplier_payment_approving_matrix == True and self.type == 'supplier':
            #     for node in doc.xpath("//button[@name='action_validate']"):
            #         node.set('string', "Request For Approval")
        return etree.tostring(doc, encoding='unicode')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Hide/Show 'Approving Matrix and Next Approver' fields of customer receipt and supplier payment form view according to account.config.settings's customer receipt / supplier payment Approving Matrix field. """
        if not self._context.get('default_is_giro') and view_type == 'form':
            if self._context.get('default_type') == 'customer':
                view_id = self.env.ref('sg_partner_payment.view_customer_receipt_form').id
            else:
                view_id = self.env.ref('sg_partner_payment.view_supplier_payment_form').id
        result = super(ReceiptPayment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            if not self._context.get('default_is_giro'):
                status = True
                result['arch'] = self._apply_state_label(result['arch'], status)
        return result

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(ReceiptPayment, self).fields_get(allfields, attributes=attributes)
        is_customer_receipt_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_customer_receipt_approving_matrix')
        is_supplier_payment_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_supplier_payment_approving_matrix')
        if is_customer_receipt_approving_matrix == False or is_supplier_payment_approving_matrix == False:
            res['state']['selection'] = [('draft', 'Draft'), ('cancel', 'Cancelled'), ('in_progress', 'In Progress'),
                                         ('posted', 'Posted')]
        else:
            res['state']['selection'] = [('draft', 'Draft'), ('request_for_approval', 'Request For Approval'),
                                         ('cancel', 'Cancelled'), ('in_progress', 'In Progress'), ('posted', 'Posted')]
        return res

    @api.onchange('journal_id')
    def onchange_journal(self):
        if self.journal_id and self.journal_id.currency_id:
            self.currency_id = self.journal_id.currency_id.id
        else:
            self.currency_id = self.company_id.currency_id.id

    @api.multi
    def compute_values(self):
        for record in self:
            record.line_cr_ids.unlink()
            record.line_dr_ids.unlink()
            line_cr_lst, line_dr_lst = record.load_data()
            record.write({'line_cr_ids': line_cr_lst, 'line_dr_ids': line_dr_lst})

    @api.multi
    def load_data(self):
        line_cr_lst = []
        line_dr_lst = []
        if self.partner_id:
            # Query to load the data from account.move.line for Cr and Dr
            base_currency_id = self.company_id.currency_id
            currency_id = self.currency_id
            self.env.cr.execute('''
                SELECT id as invoice_id,state,date_invoice as date,date_due as date_maturity,account_id,amount_total as balance,
                type,credit_note,residual as amount_unreconciled_currency,debit_note,amount_untaxed as original_amount,currency_id as move_currency_id,residual_signed as amount_unreconciled,
                amount_total_company_signed as original_amount_currency
                FROM account_invoice WHERE state = 'open' and partner_id = %s''' % (self.partner_id.id))
            credit_amount = 0.0
            debit_amount = 0.0
            for result in self.env.cr.dictfetchall():
                invoice_id = self.env['account.invoice'].browse(result['invoice_id'])
                if result['balance'] != 0:
                    if not result['move_currency_id']:
                        result['move_currency_id'] = base_currency_id.id
                    result['residual_balance'] = abs(result['amount_unreconciled_currency'])
                    result['amount_unreconciled'] = invoice_id.currency_id.with_context(date=invoice_id.date_invoice).compute(abs(result['amount_unreconciled_currency']), base_currency_id, False)
                    result['amount_unreconciled_currency'] = abs(result['amount_unreconciled_currency'])
                    result['original_amount_currency'] = abs(result['balance'])

                    if invoice_id.type in ['out_invoice','in_refund']:
                        original_amount = invoice_id.currency_id.with_context(date=invoice_id.date_invoice).compute(abs(result['balance']), base_currency_id, False)
                        debit_amount += result['amount_unreconciled_currency']
                        result['original_amount'] = original_amount
                        line_dr_lst.append((0, 0, result))

                    elif invoice_id.type in ['out_refund','in_invoice']:
                        original_amount = invoice_id.currency_id.with_context(date=invoice_id.date_invoice).compute(abs(result['balance']), base_currency_id, False)
                        credit_amount += result['amount_unreconciled_currency']
                        result['original_amount'] = original_amount
                        line_cr_lst.append((0, 0, result))

            # Code to auto-fill Reconcile and Allocation amount
            dr_index = -1
            cr_index = -1
            if self.type == 'customer':
                credit_amount += self.amount
                # debit_amount = 0.0
                for dr_lst in line_dr_lst:
                    dr_index += 1
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = currency_id.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(abs(credit_amount), invoice_currency_obj, False)
                    if credit_amount > 0:
                        amt = line_dr_lst[dr_index][2]['residual_balance']
                        if amt > credit_amount:
                            amt = credit_amount
                            credit_amount -= amt
                            reconcile = False
                        else:
                            credit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(line_dr_lst[dr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        # line_dr_lst[dr_index][2].update({'reconcile': reconcile})
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = invoice_currency_obj.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(abs(credit_amount), currency_id, False)

                debit_amount = debit_amount-self.amount if debit_amount > self.amount else 0.00
                for cr_lst in line_cr_lst:
                    cr_index += 1
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = currency_id.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(abs(debit_amount), invoice_currency_obj, False)

                    if debit_amount > 0:
                        amt = line_cr_lst[cr_index][2]['residual_balance']
                        if amt > debit_amount:
                            amt = debit_amount
                            debit_amount -= amt
                            reconcile = False
                        else:
                            debit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(line_cr_lst[cr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        # line_cr_lst[cr_index][2].update({'reconcile': reconcile})
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = invoice_currency_obj.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(abs(debit_amount), currency_id, False)
            else:
                debit_amount += self.amount
                for cr_lst in line_cr_lst:
                    cr_index += 1
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = currency_id.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(abs(debit_amount), invoice_currency_obj, False)
                    if debit_amount > 0:
                        amt = line_cr_lst[cr_index][2]['residual_balance']
                        if amt > debit_amount:
                            amt = debit_amount
                            debit_amount -= amt
                            reconcile = False
                        else:
                            debit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(line_cr_lst[cr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        # line_cr_lst[cr_index][2].update({'reconcile': reconcile})
                    if line_cr_lst[cr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_cr_lst[cr_index][2].get('move_currency_id'))
                        debit_amount = invoice_currency_obj.with_context(date=line_cr_lst[cr_index][2].get('date')).compute(abs(debit_amount), currency_id, False)

                credit_amount = credit_amount - self.amount if credit_amount > self.amount else 0.00
                for dr_lst in line_dr_lst:
                    dr_index += 1
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = currency_id.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(abs(credit_amount), invoice_currency_obj, False)
                    if credit_amount > 0:
                        amt = line_dr_lst[dr_index][2]['residual_balance']
                        if amt > credit_amount:
                            amt = credit_amount
                            credit_amount -= amt
                            reconcile = False
                        else:
                            credit_amount -= amt
                            reconcile = True
                        allocation_amount = amt
                        if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                            invoice_currency_obj = self.env['res.currency'].browse(line_dr_lst[dr_index][2].get('move_currency_id'))
                            allocation_amount = invoice_currency_obj.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(abs(amt), currency_id, False)
                        # line_dr_lst[dr_index][2].update({'reconcile': reconcile})
                    if line_dr_lst[dr_index][2].get('move_currency_id') != currency_id.id:
                        invoice_currency_obj = self.env['res.currency'].browse(line_dr_lst[dr_index][2].get('move_currency_id'))
                        credit_amount = invoice_currency_obj.with_context(date=line_dr_lst[dr_index][2].get('date')).compute(abs(credit_amount), currency_id, False)
        return line_cr_lst, line_dr_lst

    @api.onchange('partner_id', 'currency_id')
    def onchange_account_id(self):
        self.line_cr_ids = False
        self.line_dr_ids = False
        if self.partner_id:
            self.line_cr_ids, self.line_dr_ids = self.load_data()

    @api.multi
    def action_receipt_supplier_approve(self):
        for record in self:
            is_customer_receipt_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_customer_receipt_approving_matrix')
            is_supplier_payment_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_supplier_payment_approving_matrix')
            #For customer receipt
            if is_customer_receipt_approving_matrix == True and record.receipt_payment_approving_matrix_id.type == 'customer_receipt':
                lines_amount = record.receipt_payment_approving_line_ids.filtered(lambda r: r.approved == False and record.amount >= r.min_amount and record.amount <= r.max_amount)
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
                                if is_customer_receipt_approving_matrix == True and record.branch_id in record.receipt_payment_approving_matrix_id.receipt_payment_branch_ids and record.amount >= approve_matrix_line.min_amount and record.amount <= approve_matrix_line.max_amount:
                                    if self.env.user.id not in approve_matrix_line.user_ids.ids:
                                        raise ValidationError(str(self.env.user.name) + ' ' + 'is not an approver/does not belongs to sequence!')
                                    if self.env.user.id in approve_matrix_line.user_ids.ids and approve_matrix_line.min_approver > 0 and ((len(approve_matrix_line.user_ids.ids) <= approve_matrix_line.min_approver and len(approve_matrix_line.user_ids.ids) == (len(approve_matrix_line.approved_user_ids.ids) + 1)) or (len(approve_matrix_line.user_ids.ids) >= approve_matrix_line.min_approver and (len(
                                        approve_matrix_line.approved_user_ids.ids) + 1) == approve_matrix_line.min_approver)):
                                        approve_matrix_line.write({'approved': True})
                                        approved_list.append(approve_matrix_line)
                                        if len(approved_list) == len(lines_amount):
                                            record.sudo().payment_creation()
                                    else:
                                        approve_matrix_line.approved_user_ids += self.env.user
                                    record.write({'receipt_payment_approved_user_id': self.env.user.id})
                                else:
                                    record.sudo().payment_creation()
                            else:
                                record.sudo().payment_creation()
                        else:
                            record.sudo().payment_creation()
            # else:
            #     record.sudo().payment_creation()
            # For customer receipt
            elif is_supplier_payment_approving_matrix == True and record.receipt_payment_approving_matrix_id.type == 'supplier_payment':
                lines_amount = record.receipt_payment_approving_line_ids.filtered(lambda
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
                                if is_supplier_payment_approving_matrix == True and record.branch_id in record.receipt_payment_approving_matrix_id.receipt_payment_branch_ids and record.amount >= approve_matrix_line.min_amount and record.amount <= approve_matrix_line.max_amount:
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
                                            record.sudo().payment_creation()
                                    else:
                                        approve_matrix_line.approved_user_ids += self.env.user
                                    record.write({'receipt_payment_approved_user_id': self.env.user.id})
                                else:
                                    record.sudo().payment_creation()
                            else:
                                record.sudo().payment_creation()
                        else:
                            record.sudo().payment_creation()
            else:
                record.sudo().payment_creation()
        return True

    @api.multi
    def action_receipt_supplier_decline(self):
        for record in self:
            record.write({'receipt_payment_approved_user_id': False, 'state': 'draft'})
            if record.giro_approving_line_ids:
                for approval_line in record.receipt_payment_approving_line_ids:
                    approval_line.approved = False
        return True

    @api.multi
    def action_cancel(self):
        for record in self:
            for payment in record.payment_ids:
                payment.cancel()
                payment.write({'state': 'canceled'})
            if record.journal_entry_id:
                record.journal_entry_id.button_cancel()
                record.journal_entry_id.unlink()
            record.write({'state': 'cancel'})
        return True
            
    @api.multi
    def action_set_draft(self):
        for record in self:
            record.write({'state': 'draft'})
        return True

    @api.multi
    def check_values(self):
        if not self.amount and not self.line_dr_ids and not self.line_cr_ids:
            raise ValidationError('No data for validation.')
        msg = ''
        # Check Debit Entries
        self.env.cr.execute('''
            SELECT move_id.name FROM receipt_payment_debit as rpd, account_move_line as move_line, account_move as move_id
            WHERE rpd.receipt_payment_id=%s and move_line.id=rpd.move_line_id and move_id.id=move_line.move_id and rpd.amount>0 and abs(rpd.amount_residual) != abs(move_line.amount_residual)
            ''' % self.id)
        debit_items = ''
        cnt = 0
        for item in self.env.cr.fetchall():
            if item:
                cnt += 1
                debit_items += str(cnt) + '. ' + str(item[0]) + '\n'
        if debit_items:
            msg += '\nDebits:\n' + debit_items
        # Check Credit Entries
        self.env.cr.execute('''
            SELECT move_id.name FROM receipt_payment_credit as rpc, account_move_line as move_line, account_move as move_id
            WHERE rpc.receipt_payment_id=%s and move_line.id=rpc.move_line_id and move_id.id=move_line.move_id and rpc.amount>0 and abs(rpc.amount_residual) != abs(move_line.amount_residual)
            ''' % self.id)
        credit_items = ''
        cnt = 0
        for item in self.env.cr.fetchall():
            if item:
                cnt += 1
                credit_items += str(cnt) + '. ' + str(item[0]) + '\n'
        if credit_items:
            msg += '\nCredits:\n' + credit_items
        if msg:
            raise ValidationError('The following journal items are already proceed.\n' + msg)
        return True

    @api.multi
    def account_move_get(self, voucher_id):
        '''
        This method prepare the creation of the account move related to the given voucher.

        :param voucher_id: Id of voucher for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        context = self._context or {}
        seq_obj = self.env['ir.sequence']
        voucher = self.browse(voucher_id)
        #         if voucher.name:
        #             name = voucher.name
        if voucher.journal_id.sequence_id:
            if not self.journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = self.journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            print 'Please define a sequence on the journal.'
        # raise osv.except_osv(_('Error!'),
        #                         _('Please define a sequence on the journal.'))
        if not voucher.payment_ref:
            ref = name.replace('/', '')
        else:
            ref = voucher.payment_ref

        move = {
            'name': name,
            'journal_id': voucher.journal_id.id,
            'narration': voucher.narration,
            'date': voucher.date,
            'ref': ref,
            #             'period_id': voucher.period_id.id,
        }
        return move

    @api.multi
    def first_move_line_get(self, voucher_id, move_id, company_currency, current_currency):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        voucher = self
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        if voucher.type in ('purchase', 'payment', 'supplier'):
            credit = voucher.amount
        elif voucher.type in ('sale', 'receipt', 'customer'):
            debit = voucher.amount
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        # set the first line of the voucher
        move_line = {
            'name': voucher.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': voucher.writeoff_acc_id.id,
            'move_id': move_id.id,
            'journal_id': voucher.journal_id.id,
            #                 'period_id': voucher.period_id.id,
            'partner_id': voucher.partner_id.id,
            'currency_id': company_currency <> current_currency and current_currency or False,
            'amount_currency': (sign * abs(voucher.amount)  # amount < 0 for refunds
                                if company_currency != current_currency else 0.0),
            'date': voucher.date,
            #                 'date_maturity': voucher.date_due
        }
        return move_line

    @api.multi
    def get_account_move_line(self, move_id):
        line_dr_ids = self.line_dr_ids
        line_cr_ids = self.line_cr_ids
        line_dr_amount = []
        move_line_list = []
        for line_dr in line_dr_ids:
            dr_account_id = line_dr.account_id
            amount = line_dr.amount
            line_dr_amount.append(amount)
            dr_total_amount = sum(line_dr_amount)
            total_payment = self.amount
            debit = 0.0
            credit = 0.0
            move_line = {
                'name': '/',
                'account_id': self.journal_id.default_debit_account_id.id,
                'debit': total_payment,
                'credit': credit,
                'partner_id': self.partner_id.id,
                'date': self.date,
                'move_id': move_id.id,
                'journal_id': self.journal_id.id,
                'currency_id': self.currency_id.id or False,
            }
            move_line_list.append(move_line.copy())
            move_line['credit'] = dr_total_amount
            move_line['debit'] = 0.0
            move_line['account_id'] = dr_account_id.id
            move_line_list.append(move_line.copy())
            if self.payment_difference_handling == 'reconcile':
                move_line['credit'] = self.diff_amount
                move_line['name'] = self.comment or 'Counterpart'
                move_line['account_id'] = self.writeoff_acc_id.id
                move_line_list.append(move_line.copy())
            else:
                move_line['credit'] = self.diff_amount
                move_line['name'] = move_id.name
                move_line_list.append(move_line.copy())
        return move_line_list

    @api.multi
    def payment_creation(self):
        for record in self:
            record.check_values()
            # Creating the payment
            def create_payment(invoice_id, amount, type):
                if type == 'customer':
                    payment_method_id = self.env['ir.model.data'].xmlid_to_res_id('account.account_payment_method_manual_in')
                    payment_type = 'inbound'
                else:
                    payment_method_id = self.env['ir.model.data'].xmlid_to_res_id('account.account_payment_method_manual_out')
                    payment_type = 'outbound'
                payment = record.create_payments(invoice_id, payment_method_id, payment_type, amount)
                payment.post()
                record.write({'payment_ids': [(4, payment.id)]})
                return payment

            # Processing customer receipts
            if self.type == 'customer':
                for cr_line in record.line_cr_ids:
                    if cr_line and cr_line.amount:
                        if cr_line.invoice_id.type in ('out_invoice','in_refund'):
                            payment_id = create_payment(cr_line.invoice_id.id, cr_line.amount, 'customer')
                        else:
                            payment_id = create_payment(cr_line.invoice_id.id, cr_line.amount, 'supplier')
                        move_lines = payment_id.move_line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                        cr_line.invoice_id.register_payment(move_lines)
                total_amount = self.amount
                debit_total = sum([debit.amount for debit in record.line_dr_ids])
                count = 0
                for dr_line in record.line_dr_ids:
                    count += 1
                    amount = dr_line.amount
                    if dr_line.amount == 0.0:
                        continue
                    final_amount = amount
                    if final_amount < 0:
                        final_debit = -(final_amount)
                    else:
                        final_debit = final_amount
                    if final_debit > 0:
                        if dr_line.invoice_id.type in ('out_invoice', 'in_refund'):
                            payment_id = create_payment(dr_line.invoice_id.id, final_debit, 'customer')
                        else:
                            payment_id = create_payment(dr_line.invoice_id.id, final_debit, 'supplier')
                        move_lines = payment_id.move_line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                        dr_line.invoice_id.register_payment(move_lines)
                    total_amount -= final_debit
            else:
                # Processing supplier payments
                for dr_line in record.line_dr_ids:
                    if dr_line and dr_line.amount:
                        if dr_line.invoice_id.type in ('out_invoice', 'in_refund'):
                            payment_id = create_payment(dr_line.invoice_id.id, dr_line.amount, 'customer')
                        else:
                            payment_id = create_payment(dr_line.invoice_id.id, dr_line.amount, 'supplier')
                        move_lines = payment_id.move_line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                        dr_line.invoice_id.register_payment(move_lines)
                total_amount = self.amount
                credit_total = sum([credit.amount for credit in record.line_cr_ids])
                count = 0
                for cr_line in record.line_cr_ids:
                    count += 1
                    amount = cr_line.amount
                    if cr_line.amount == 0.0:
                        continue
                    final_amount = amount
                    if final_amount < 0:
                        final_credit = -(final_amount)
                    else:
                        final_credit = final_amount
                    if final_credit > 0:
                        if cr_line.invoice_id.type in ('out_invoice', 'in_refund'):
                            payment_id = create_payment(cr_line.invoice_id.id, final_credit, 'customer')
                        else:
                            payment_id = create_payment(cr_line.invoice_id.id, final_credit, 'supplier')
                        move_lines = payment_id.move_line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
                        cr_line.invoice_id.register_payment(move_lines)
                    total_amount -= final_credit

            # Handle difference amount
            if record.diff_amount:
                vals = {}
                vals['ref'] = record.name
                vals['date'] = record.date
                vals['partner_id'] = record.partner_id.id
                vals['journal_id'] = record.journal_id.id
                vals['currency_id'] = record.currency_id.id
                if record.type == 'customer':
                    if (record.diff_amount > 0.0 or (record.diff_amount < 0.0 and record.payment_difference_handling == 'reconcile')):
                        receivable_account_id = record.writeoff_acc_id.id or record.partner_id.property_account_receivable_id.id
                        second_account_id = record.journal_id.default_debit_account_id.id
                    else:
                        receivable_account_id = record.partner_id.property_account_receivable_id.id
                        if not receivable_account_id:
                            receivable_account_id = self.env['account.account'].search(
                                [('user_type_id.type', '=', 'receivable')], limit=1)
                            receivable_account_id = receivable_account_id and receivable_account_id.id
                        second_account_id = record.writeoff_acc_id.id or record.journal_id.default_credit_account_id.id

                    # Creating Peyment for Balance amount when the Payment difference is Keep Open
                    if record.payment_difference_handling == 'without_writeoff' and record.diff_amount > 0:
                        create_payment(False, record.diff_amount, 'customer')

                    diff_amount = record.currency_id.with_context(date=record.date).compute(abs(record.diff_amount), record.company_id.currency_id)
                    db_line = [debit.invoice_id.currency_id for debit in record.line_dr_ids if debit.amount and debit.invoice_id.currency_id != record.currency_id]
                    if record.diff_amount > 0.0:
                        credit_1 = diff_amount
                        credit_2 = 0.0
                        debit_1 = 0.0
                        debit_2 = diff_amount
                    else:
                        credit_1 = 0.0
                        credit_2 = diff_amount
                        debit_1 = diff_amount
                        debit_2 = 0.0

                    if ((record.payment_difference_handling == 'reconcile') or (record.payment_difference_handling == 'without_writeoff' and record.diff_amount < 0)):
                        move_line_1 = {
                            'name': 'Customer Payment',
                            'account_id': receivable_account_id,
                            'amount_currency': debit_1 and abs(record.diff_amount) or -(abs(record.diff_amount)),
                            'currency_id': record.currency_id.id,
                            'debit': debit_1 > 0.0 and diff_amount or 0.0,
                            'credit': credit_1 > 0.0 and diff_amount or 0.0,
                            'journal_id': record.journal_id.id,
                            'partner_id': record.partner_id.id,
                        }
                        move_line_2 = {
                            'name': self.comment or 'Counter Part',
                            'account_id': second_account_id,
                            'amount_currency': credit_2 and -(abs(record.diff_amount)) or abs(record.diff_amount),
                            'currency_id': record.currency_id.id,
                            'credit': credit_2 > 0.0 and diff_amount or 0.0,
                            'debit': debit_2 > 0.0 and diff_amount or 0.0,
                            'journal_id': record.journal_id.id,
                            'partner_id': record.partner_id.id,
                        }
                        vals['line_ids'] = [(0, 0, move_line_1), (0, 0, move_line_2)]
                        move = self.env['account.move'].create(vals)
                        move.post()
                        record.write({'journal_entry_id': move.id})
                        if record.diff_amount < 0.0 and record.payment_difference_handling == 'reconcile':
                            move_lines = move.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('receivable'))
                            for dr_line in record.line_dr_ids:
                                if dr_line.amount and dr_line.invoice_id.state == 'open':
                                    dr_line.invoice_id.register_payment(move_lines)
                else:
                    if (record.diff_amount > 0.0 or (record.diff_amount < 0.0 and record.payment_difference_handling == 'reconcile')):
                        payable_account_id = record.writeoff_acc_id.id or record.partner_id.property_account_payable_id.id
                        second_account_id = record.journal_id.default_debit_account_id.id
                    else:
                        payable_account_id = record.partner_id.property_account_payable_id.id
                        if not payable_account_id:
                            payable_account_id = self.env['account.account'].search(
                                [('user_type_id.type', '=', 'payable')], limit=1)
                            payable_account_id = payable_account_id and payable_account_id.id
                        second_account_id = record.writeoff_acc_id.id or record.journal_id.default_credit_account_id.id

                    # Creating Peyment for Balance amount when the Payment difference is Keep Open
                    if record.payment_difference_handling == 'without_writeoff' and record.diff_amount > 0:
                        create_payment(False, record.diff_amount, 'supplier')

                    diff_amount = record.currency_id.with_context(date=record.date).compute(abs(record.diff_amount), record.company_id.currency_id)
                    cr_line = [credit.invoice_id.currency_id for credit in record.line_cr_ids if credit.amount and credit.invoice_id.currency_id != record.currency_id]

                    if record.diff_amount > 0.0:
                        credit_1 = 0.0
                        credit_2 = diff_amount
                        debit_1 = diff_amount
                        debit_2 = 0.0
                    else:
                        credit_1 = diff_amount
                        credit_2 = 0.0
                        debit_1 = 0.0
                        debit_2 = diff_amount
                    if (record.payment_difference_handling == 'reconcile' or (record.payment_difference_handling == 'without_writeoff' and record.diff_amount < 0)):
                        move_line_1 = {
                            'name': 'Vendor Payment',
                            'account_id': payable_account_id,
                            'amount_currency': credit_1 and -(abs(record.diff_amount)) or abs(record.diff_amount),
                            'currency_id': record.currency_id.id,
                            'debit': debit_1 > 0.0 and diff_amount or 0.0,
                            'credit': credit_1 > 0.0 and diff_amount or 0.0,
                            'journal_id': record.journal_id.id,
                        }
                        move_line_2 = {
                            'name': record.comment or 'Counter Part',
                            'account_id': second_account_id,
                            'amount_currency': debit_2 and abs(record.diff_amount) or -(abs(record.diff_amount)),
                            'currency_id': record.currency_id.id,
                            'debit': debit_2 > 0.0 and diff_amount or 0.0,
                            'credit': credit_2 > 0.0 and diff_amount or 0.0,
                            'journal_id': record.journal_id.id,
                        }
                        vals['line_ids'] = [(0, 0, move_line_2), (0, 0, move_line_1)]
                        move = self.env['account.move'].create(vals)
                        move.post()
                        record.write({'journal_entry_id': move.id})
                        if record.diff_amount < 0.0 and record.payment_difference_handling == 'reconcile':
                            move_lines = move.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable'))
                            for cr_line in record.line_cr_ids:
                                if cr_line.amount and cr_line.invoice_id.state == 'open':
                                    cr_line.invoice_id.register_payment(move_lines)
            record.write({'state': 'posted'})
        return True

    @api.multi
    def action_validate(self):
        for record in self:
            if record.amount < 0.0:
                raise ValidationError(_('Total paid amount cannot be negative, please check again.'))
            is_customer_receipt_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_customer_receipt_approving_matrix')
            is_supplier_payment_approving_matrix = self.env['ir.values'].sudo().get_default('account.config.settings', 'is_supplier_payment_approving_matrix')
            if not self._context.get('default_is_giro'):
                #For customer receipt
                if is_customer_receipt_approving_matrix == True and record.receipt_payment_approving_matrix_id.type == 'customer_receipt':
                    if record.branch_id and record.receipt_payment_approving_matrix_id and record.receipt_payment_approving_matrix_id.receipt_payment_branch_ids and record.branch_id not in record.receipt_payment_approving_matrix_id.receipt_payment_branch_ids:
                        raise ValidationError(_('Customer receipt and approving matrix branches should be same.'))
                    record.write({'state': 'request_for_approval', 'receipt_payment_approved_user_id': False})
                #For supplier payment
                elif is_supplier_payment_approving_matrix == True and record.receipt_payment_approving_matrix_id.type == 'supplier_payment':
                    if record.branch_id and record.receipt_payment_approving_matrix_id and record.receipt_payment_approving_matrix_id.receipt_payment_branch_ids and record.branch_id not in record.receipt_payment_approving_matrix_id.receipt_payment_branch_ids:
                        raise ValidationError(_('Supplier payment and approving matrix branches should be same.'))
                    record.write({'state': 'request_for_approval', 'receipt_payment_approved_user_id': False})
                else:
                    record.payment_creation()

        return True

    @api.multi
    def create_payments(self, invoice_id, payment_method_id, payment_type, amount):
        payment_vals = {}
        payment_vals['payment_type'] = payment_type
        payment_vals['partner_type'] = self.type
        payment_vals['payment_method_id'] = payment_method_id
        payment_vals['partner_id'] = self.partner_id.id
        payment_vals['journal_id'] = self.journal_id.id
        payment_vals['currency_id'] = self.currency_id.id
        payment_vals['company_id'] = self.company_id.id
        payment_vals['communication'] = self.memo or ''
        payment_vals['amount'] = amount
        if invoice_id:
            payment_vals['invoice_ids'] = [(6, 0, [invoice_id])]
        payment_vals['payment_date'] = self.date
        payment_id = self.env['account.payment'].create(payment_vals)
        return payment_id

    @api.multi
    def update_move_line(self, line, amount, sign):
        convt_amount = line.currency_id.compute(amount, line.move_currency_id, False)
        if line.move_line_id and line.move_line_id.amount_residual_currency:
            amount_residual_currency = (line.amount_unreconciled_currency - convt_amount)
        else:
            amount_residual_currency = 0.0
        amount_residual = line.amount_unreconciled - amount
        if line.currency_id.id != self.env.user.company_id.currency_id.id:
            amount_residual = line.currency_id.compute(amount_residual, self.env.user.company_id.currency_id, False)
        if round(amount_residual) <= 0:
            reconciled = True
        else:
            reconciled = False
        if amount_residual_currency:
            if amount_residual == 0:
                amount_residual_currency = 0.0
            elif sign == '-ve':
                amount_residual_currency = -amount_residual_currency
                amount_residual = -amount_residual
            self.env.cr.execute('''
            UPDATE account_move_line SET amount_residual_currency=%s, amount_residual=%s, reconciled=%s WHERE id=%s
            ''', (amount_residual_currency, amount_residual, reconciled,
                  line.move_line_id.id if line.move_line_id else False))
        else:
            if sign == '-ve':
                amount_residual = -amount_residual
            self.env.cr.execute('''
            UPDATE account_move_line SET amount_residual=%s, reconciled=%s WHERE id=%s
            ''', (amount_residual, reconciled, line.move_line_id.id if line.move_line_id else False))

    @api.multi
    def unlink(self):
        for record in self:
            if record.type == 'customer' and record.state not in ['draft', 'cancel']:
                raise UserError('Cannot delete Customer Receipts in %s state.' % record.state)
            elif record.type == 'supplier' and record.state not in ['draft', 'cancel']:
                raise UserError('Cannot delete Supplier Payments in %s state.' % record.state)
        return super(ReceiptPayment, self).unlink()

    @api.multi
    def action_view_payments(self):
        action = self.env.ref('account.action_account_payments').read()[0]
        action['domain'] = [('id','in',self.payment_ids.ids)]
        return action

ReceiptPayment()

class ReceiptPaymentCredit(models.Model):
    _name = 'receipt.payment.credit'
    _description = 'Customer Receipts and Supplier Payments Lines'

    @api.multi
    def compute_base_currency(self):
        for record in self:
            record.base_currency_id = self.env.user.company_id.currency_id.id

    receipt_payment_id = fields.Many2one('receipt.payment', string='Recipt/Payment')
    move_line_id = fields.Many2one('account.move.line', string='Move Line')
    date = fields.Date(readonly=True)
    date_maturity = fields.Date(readonly=True, string='Due Date')
    account_id = fields.Many2one('account.account', required=True, string='Account')
    currency_id = fields.Many2one(related='receipt_payment_id.currency_id', string='Currency')
    move_currency_id = fields.Many2one('res.currency', string='Move Line Currency')
    base_currency_id = fields.Many2one('res.currency', compute='compute_base_currency', string='Move Line Currency')
    original_amount_currency = fields.Monetary(currency_field='move_currency_id', string='Original Currency Amount')
    original_amount = fields.Monetary(currency_field='base_currency_id', string='Base Currency Amount')
    amount_unreconciled_currency = fields.Monetary(currency_field='move_currency_id', string='Original Currency Open Balance')
    amount_unreconciled = fields.Monetary(currency_field='base_currency_id', string='Base Currency Open Balance')
    amount_residual = fields.Float(string='Amount Residual')
    reconcile = fields.Boolean('Full Reconcile')
    amount = fields.Monetary(currency_field='currency_id', string='Allocation')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        amount = self.move_currency_id.with_context(date=self.date).compute(abs(self.amount), self.currency_id, False)
        if self.reconcile:
            amount = self.amount_unreconciled_currency
        if amount > self.amount_unreconciled_currency:
            raise ValidationError('Allocation amount must be less than or equal to Residual Amount.')

    @api.onchange('reconcile', 'amount')
    def onchange_reconcile(self):
        ctx = self._context or {}
        if self.reconcile and ctx.get('reconcile'):
            allocation_amount = self.move_currency_id.with_context(date=self.date).compute(abs(self.amount_unreconciled_currency), self.currency_id, False)
            self.amount = allocation_amount
        elif ctx.get('reconcile') and not self.reconcile:
            self.amount = 0.0
        elif ctx.get('amount'):
            amount = self.move_currency_id.with_context(date=self.date).compute(abs(self.amount), self.currency_id, False)
            # if amount < self.amount_unreconciled_currency:
            #     self.reconcile = False
            # else:
            #     self.reconcile = True

ReceiptPaymentCredit()

class ReceiptPaymentDebit(models.Model):
    _name = 'receipt.payment.debit'
    _description = 'Customer Receipts and Supplier Payments Lines'

    @api.multi
    def compute_base_currency(self):
        for record in self:
            record.base_currency_id = self.env.user.company_id.currency_id.id

    receipt_payment_id = fields.Many2one('receipt.payment', string='Recipt/Payment')
    move_line_id = fields.Many2one('account.move.line', string='Move Line')
    account_id = fields.Many2one('account.account', required=True, string='Account')
    date = fields.Date(readonly=True)
    date_maturity = fields.Date(readonly=True, string='Due Date')
    currency_id = fields.Many2one(related='receipt_payment_id.currency_id', string='Currency')
    move_currency_id = fields.Many2one('res.currency', string='Move Line Currency')
    base_currency_id = fields.Many2one('res.currency', compute='compute_base_currency', string='Move Line Currency')
    original_amount_currency = fields.Monetary(currency_field='move_currency_id', string='Original Currency Amount')
    original_amount = fields.Monetary(currency_field='base_currency_id', string='Base Currency Amount')
    amount_unreconciled_currency = fields.Monetary(currency_field='move_currency_id', string='Original Currency Open Balance')
    amount_unreconciled = fields.Monetary(currency_field='base_currency_id', string='Base Currency Open Balance')
    amount_residual = fields.Float(string='Amount Residual')
    reconcile = fields.Boolean('Full Reconcile')
    amount = fields.Monetary(currency_field='currency_id', string='Allocation')
    invoice_id = fields.Many2one('account.invoice', string='Invoice')
    payment_id = fields.Many2one('account.payment', string='Payment')

    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        amount = self.currency_id.with_context(date=self.date).compute(abs(self.amount), self.move_currency_id, False)
        if self.reconcile:
            amount = self.amount_unreconciled_currency
        if amount > self.amount_unreconciled_currency:
            raise ValidationError('Allocation amount must be less than or equal to Residual Amount.')

    @api.onchange('reconcile', 'amount')
    def onchange_reconcile(self):
        ctx = self._context or {}
        if self.reconcile and ctx.get('reconcile'):
            allocation_amount = self.move_currency_id.with_context(date=self.date).compute(abs(self.amount_unreconciled_currency), self.currency_id, False)
            self.amount = allocation_amount
        elif ctx.get('reconcile') and not self.reconcile:
            self.amount = 0.0
        elif ctx.get('amount'):
            amount = self.currency_id.with_context(date=self.date).compute(abs(self.amount), self.move_currency_id, False)
            # if amount < self.amount_unreconciled_currency:
            #     self.reconcile = False
            # else:
            #     self.reconcile = True

ReceiptPaymentDebit()

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()
        for rec in self:
            if rec.name and not rec.ref:
                self.rec = rec.name
        return res

    # @api.multi
    # def assert_balanced(self):
    #     if not self.ids:
    #         return True
    #     prec = self.env['decimal.precision'].precision_get('Account')
    #
    #     self._cr.execute("""\
    #         SELECT      move_id
    #         FROM        account_move_line
    #         WHERE       move_id in %s
    #         GROUP BY    move_id
    #         HAVING      abs(sum(debit) - sum(credit)) > %s
    #         """, (tuple(self.ids), 10 ** (-max(5, prec))))
    #     if len(self._cr.fetchall()) != 0:
    #         raise UserError(_("Cannot create unbalanced journal entry for this move %s ." % (', '.join(str(i) for i in self.ids))))
    #     return True

AccountMove()

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    difference = fields.Char('Difference')
    total_residual = fields.Char('Residual')
    state = fields.Selection(selection_add=[('cancel', 'Cancelled')], string="Status")

    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id,
                                                          invoice_currency)

        move = self.env['account.move'].create(self._get_move_vals())

        # Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(
                self.payment_difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
            # the writeoff debit and credit must be computed from the invoice residual in company currency
            # minus the payment amount in company currency, and not from the payment difference in the payment currency
            # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
            total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
            total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount,
                                                                                                         self.company_id.currency_id)
            if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                amount_wo = total_payment_company_signed - total_residual_company_signed
            else:
                amount_wo = total_residual_company_signed - total_payment_company_signed
            # Align the sign of the secondary currency writeoff amount with the sign of the writeoff
            # amount in the company currency
            if amount_wo > 0:
                debit_wo = amount_wo
                credit_wo = 0.0
                amount_currency_wo = abs(amount_currency_wo)
            else:
                debit_wo = 0.0
                credit_wo = -amount_wo
                amount_currency_wo = -abs(amount_currency_wo)
            writeoff_line['name'] = _('Counterpart')
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit']:
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit']:
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo
        #############################
        elif self.payment_difference_handling == 'reconcile' and self.difference and self.total_residual:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(
                self.difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
            # the writeoff debit and credit must be computed from the invoice residual in company currency
            # minus the payment amount in company currency, and not from the payment difference in the payment currency
            # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
            total_residual_company_signed = self.total_residual
            total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount,
                                                                                                         self.company_id.currency_id)
            #             if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
            #                 amount_wo = total_payment_company_signed - total_residual_company_signed
            #             else:
            #                 amount_wo = total_residual_company_signed - total_payment_company_signed
            # Align the sign of the secondary currency writeoff amount with the sign of the writeoff
            # amount in the company currency
            amount_wo = -float(self.difference)
            if amount_wo > 0:
                debit_wo = amount_wo
                credit_wo = 0.0
                amount_currency_wo = abs(amount_currency_wo)
            else:
                debit_wo = 0.0
                credit_wo = -amount_wo
                amount_currency_wo = -abs(amount_currency_wo)
            writeoff_line['name'] = _('Counterpart')
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)

            if counterpart_aml['debit']:
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit']:
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        #############################
        if self.invoice_ids:
            self.invoice_ids.register_payment(counterpart_aml)

        # Write counterpart lines
        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
        aml_obj.create(liquidity_aml_dict)
        move.post()
        if self.difference and self.total_residual:
            self.env.cr.execute("SELECT id from receipt_payment ORDER BY id DESC")
            payment_reciept_id = self.env.cr.fetchone()[0]
            self.env['receipt.payment'].browse(payment_reciept_id).move_line_id = counterpart_aml.id
        return move

AccountPayment()

class ReceiptPaymentApprovingMatrixLines(models.Model):
    _name = 'receipt.payment.approving.matrix.lines'
    _description = 'Approving Matrix Lines'

    sequence = fields.Integer('Sequence')
    user_ids = fields.Many2many('res.users', string='Users')
    approved_user_ids = fields.Many2many('res.users', 'approved_users_receipt_payment_amount_rel', 'user_ids', 'receipt_payment_matrix_line_id', string='Approved Users')
    min_amount = fields.Float('Minimum Amount')
    max_amount = fields.Float('Maximum Amount')
    min_approver = fields.Integer('Minimum Approver', default=1)
    approved = fields.Boolean("Approved")
    receipt_payment_approving_id = fields.Many2one('receipt.payment', string='Pettycash Fund')

ReceiptPaymentApprovingMatrixLines()