# -*- coding: utf-8 -*-


import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountAgedTrialBalance(models.TransientModel):

    _inherit = 'account.aged.trial.balance'

    @api.onchange('result_selection')
    def onchange_result_selection(self):
        print 'onchange'
        if self.result_selection=='customer':
            return {'domain': {'partner_ids' : [('customer', '=', True)]}}
        elif self.result_selection=='supplier':
            return {'domain': {'partner_ids' : [('supplier', '=', True)]}}
        else:
            return {'domain': {'partner_ids' : ['|', ('customer', '=', True), ('supplier', '=', True)]}}


    partner_ids = fields.Many2many('res.partner', string='Partners')

    def _print_report(self, data):
        """To add partners in report"""
    	data['form'].update({'partner_ids': self.read(['partner_ids'])[0]['partner_ids']})
    	return super(AccountAgedTrialBalance, self)._print_report(data)

class ReportAgedPartnerBalance(models.AbstractModel):

    _inherit = 'report.account.report_agedpartnerbalance'

    @api.model
    def render_html(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = data['form'].get('target_move', 'all')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']

        movelines, total, dummy = self._get_partner_move_lines(account_type, date_from, target_move, data['form']['period_length'])
        # Filtering account.move.line of selected partners
        if data['form'].get('partner_ids'):
        	movelines = [line for line in movelines if line['partner_id'] in data['form'].get('partner_ids')]
        docargs = {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
        }
        return self.env['report'].render('account.report_agedpartnerbalance', docargs)