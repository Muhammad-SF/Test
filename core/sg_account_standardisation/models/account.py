# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ReportAgedPartnerBalance(models.Model):

    _inherit = 'account.move.line'

    @api.model
    def list_journals(self):
        '''returns the list of journal to selection widget'''
        journals = dict(self.env['account.journal'].name_search('',[]))
        ids = journals.keys()
        result = []
        for journal in self.env['account.journal'].browse(ids):
            result.append((journal.id,journals[journal.id],journal.type))
        return result


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        invoice_tax_obj = self.env['account.invoice.tax']
        for inv in self:
            invoice_tax_rec = invoice_tax_obj.search([('amount','=',0),('invoice_id','=',inv.id)])
            if invoice_tax_rec:
                self._cr.execute("""update account_move set state='draft' where id = %s""",(inv.move_id.id,))
                for tax_line in invoice_tax_rec:
                    inv.move_id.line_ids = [(0, 0, {'invoice_id': inv.id,
                                                    'credit': 0.0,
                                                    'debit': 0.0,
                                                    'quantity': 0,

                                                    'name': tax_line.account_id.name,
                                                    'partner_id': inv.partner_id.id,
                                                    'account_id': tax_line.account_id.id,
                                                    'company_id': inv.company_id.id,})]
                inv.move_id.post()
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        context = self.env.context
        if (context.get('active_model') == 'account.invoice') and context.get('active_id'):
            invoice = self.env['account.invoice'].browse(self._context['active_id'])
            full_reconcile_id = False
            for line in invoice.move_id.line_ids:
                if line.full_reconcile_id:
                    full_reconcile_id = line.full_reconcile_id
                    for general in full_reconcile_id.reconciled_line_ids:
                        if general.journal_id.type == 'general':
                            if invoice.type == 'out_invoice':
                                account_id = self.env.ref("l10n_sg.1_account_account_791")
                                self._cr.execute("""update account_move set state='draft' where id = %s""", (general.move_id.id,))
                                self.env['account.move.line'].create({'invoice_id': invoice.id,
                                                                'credit': 0.0,
                                                                'debit': 0.0,
                                                                'quantity': 0,
                                                                'move_id': general.move_id.id,
                                                                'name': account_id.name,
                                                                'partner_id': invoice.partner_id.id,
                                                                'account_id': account_id.id,
                                                                'currency_id':invoice.currency_id.id,
                                                                'company_id': invoice.company_id.id,})
                                general.move_id.post()


        return res

