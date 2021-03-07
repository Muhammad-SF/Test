# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class AccountReportContextTax(models.TransientModel):
    _inherit = "account.report.context.tax"

    def get_columns_names(self):
        return ['Date', 'Account', 'Ref No', 'Partner', 'Nomor Faktur Pajak', 'Currency', 'Untaxed Amount', 'GST', 'Total']

    @api.multi
    def get_columns_types(self):
        return ['date', 'text', 'text', 'text', 'text', 'number', 'number', 'number', 'number']

AccountReportContextTax()

class ReportAccountGenericTaxReport(models.AbstractModel):
    _inherit = 'account.generic.tax.report'

    @api.model
    def _lines(self, line_id=None):
        lines = []
        context = self.env.context
        unfold_taxes = context.get('context_id').unfolded_tax_ids.ids
        tax_ids = self.env['account.tax'].search([])
        company_ids = context.get('context_id').multicompany_manager_id.company_ids
        if company_ids:
            tax_ids = self.env['account.tax'].search([('company_id','in',company_ids.ids)])
        if context.get('context_id').tax_ids:
            tax_ids = context.get('context_id').tax_ids
        if line_id:
            tax_ids = self.env['account.tax'].search([('id','=',line_id)])

        final_untaxed_amount_total = 0.0
        final_gst_total = 0.0
        final_amount_total = 0.0
        for tax in tax_ids:
            domain = [('date','>=',context.get('date_from')),('date','<=',context.get('date_to'))]
            domain += [('tax_line_id','=',tax.id)]
            if company_ids:
                domain += [('company_id','in',company_ids.ids)]
            states = []
            if context.get('context_id').tax_report_unpost:
                states.append('draft')
            if context.get('context_id').tax_report_post:
                states.append('posted')
            if not states:
                states = ['draft','posted']
            domain += [('move_id.state', 'in', states)]
            if context.get('context_id').account_ids:
                domain += [('account_id','in',context.get('context_id').account_ids.ids)]
            if context.get('context_id').currency_ids:
                domain += [('currency_id','in',context.get('context_id').currency_ids.ids)]
            untaxed_amount_total = 0.0
            gst_total = 0.0
            amount_total = 0.0

            move_ids = self.env['account.move.line'].search(domain)
            for move in move_ids:
                try:
                    print 'Move : ', move, 'invoice Id : ', move.invoice_id
                    if move.invoice_id:
                        print 'Untaxed Amount', move.invoice_id.amount_untaxed
                        sub_total = move.invoice_id.amount_untaxed
                    else:
                        sub_total = move.balance / (tax.amount / 100)
                except:
                    sub_total = 0.0
                gst_amount = move.balance
                untaxed_amount_total += sub_total
                gst_total += gst_amount
                amount_total += (sub_total + gst_amount)
                # Final total
                final_untaxed_amount_total += sub_total
                final_gst_total += gst_amount
                final_amount_total += (sub_total + gst_amount)

            lines.append({
                'id': tax.id,
                'type': 'line',
                'name': tax.name + ' (' + str(tax.amount) + ')',
                'footnotes': self.env.context.get('context_id')._get_footnotes('line', tax.id),
                'columns': ['', '', '', '', '', '', self._format(untaxed_amount_total), self._format(gst_total), self._format(amount_total)],
                'level': 2,
                'unfoldable': True,
                'unfolded': tax.id in unfold_taxes,
            })

            if tax.id in unfold_taxes:
                move_ids = self.env['account.move.line'].search(domain)
                for move in move_ids:
                    date = datetime.strptime(move.date, DEFAULT_SERVER_DATE_FORMAT).strftime('%d-%m-%Y')
                    account_name = move.account_id.code + ' - ' + move.account_id.name
                    ref_no = move.invoice_id.reference or move.move_id.ref
                    nomor_faktur_pajak = move.invoice_id.efaktur_masukan or ''
                    if move.invoice_id.type == 'out_invoice':
                        ref_no = move.invoice_id.name or move.move_id.ref
                        nomor_faktur_pajak = move.invoice_id.efaktur_id.name or ''
                    gst_amount = move.balance
                    try:
                        if move.invoice_id:
                            sub_total = move.invoice_id.amount_untaxed
                        else:
                            sub_total = move.balance / (tax.amount / 100)
                    except:
                        sub_total = 0.0
                    currency = move.currency_id.name or move.company_id.currency_id.name
                    lines.append({
                        'id': tax.id,
                        'name': move.move_id.name or '/',
                        'type': 'move_line_id',
                        'action': ['account.move', move.move_id.id, _('View Journal Entry'), False],
                        'footnotes': self.env.context.get('context_id')._get_footnotes('tax_id', tax.id),
                        'columns': [date, account_name, ref_no, move.partner_id.name, nomor_faktur_pajak, currency, self._format(sub_total), self._format(gst_amount), self._format(sub_total+gst_amount)],
                        'level': 1,
                    })
                lines.append({
                    'id': tax.id,
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total') + ' ' + (tax.name),
                    'footnotes': self.env.context.get('context_id')._get_footnotes('o_account_reports_domain_total', tax.id),
                    'columns': ['', '', '', '', '', '', self._format(untaxed_amount_total), self._format(gst_total), self._format(amount_total)],
                    'level': 1,
                })
        # Final total
        if not line_id:
            lines.append({
                'id': 0,
                'type': 'o_account_reports_domain_total',
                'name': _('Total'),
                'footnotes': self.env.context.get('context_id')._get_footnotes('o_account_reports_domain_total', 0),
                'columns': ['', '', '', '', '', '', self._format(final_untaxed_amount_total), self._format(final_gst_total), self._format(final_amount_total)],
                'level': 0,
            })
        return lines

ReportAccountGenericTaxReport()



