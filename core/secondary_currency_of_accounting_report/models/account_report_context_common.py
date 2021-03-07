# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _, osv
try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter
from odoo.exceptions import Warning
from datetime import timedelta, datetime
import babel
import calendar
import json
import StringIO
from odoo.tools import config, posix_to_ldml



class AccountReportContextCommon(models.TransientModel):
	_inherit = "account.report.context.common"

	current_currency_id = fields.Many2one('res.currency')
	change_currency_id = fields.Many2one('res.currency')


	@api.model
	def return_context(self, report_model, given_context, report_id=None):
		context_model = self._report_model_to_report_context()[report_model]
		# Fetch the context_id or create one if none exist.
		# Look for a context with create_uid = current user (and with possibly a report_id)
		domain = [('create_uid', '=', self.env.user.id)]
		if report_id:
			domain.append(('report_id', '=', int(report_id)))
		context = False
		for c in self.env[context_model].search(domain):
			if c.available_company_ids and c.available_company_ids <= self.env['account.report.multicompany.manager']._default_company_ids():
				context = c
				break
		if context and (report_model == 'account.bank.reconciliation.report' and given_context.get('active_id')):
			context.unlink()
			context = self.env[context_model].browse([]) # set it to an empty set to indicate the contexts have been removed
		if not context:
			create_vals = {}
			if report_id:
				create_vals['report_id'] = report_id
			if report_model == 'account.bank.reconciliation.report' and given_context.get('active_id'):
				create_vals['journal_id'] = given_context['active_id']
			context = self.env[context_model].create(create_vals)
		if 'force_account' in given_context:
			context.unfolded_accounts = [(6, 0, [given_context['active_id']])]
			context.account_ids = [(6, 0, [given_context['active_id']])]

		update = {}
		for field in given_context:
			if field.startswith('add_'):
				if field.startswith('add_tag_'):
					ilike = self.env['account.report.tag.ilike'].create({'text': given_context[field]})
					update[field[8:]] = [(4, ilike.id)]
				else:
					update[field[4:]] = [(4, int(given_context[field]))]
			if field.startswith('update_'):
					update[field[7:]] =  int(given_context[field])
			if field.startswith('old_update_'):
				update[field[11:]] = int(given_context[field])
			if field.startswith('remove_all_'):
					update[field[4:]] =  int(given_context[field])
			if field.startswith('remove_'):
				update[field[7:]] = [(3, int(given_context[field]))]
			if field.startswith('currency_remove_'):
					update[field[16:]] =  ''
			if context._fields.get(field) and given_context[field] != 'undefined':
				if given_context[field] == 'false':
					given_context[field] = False
				if given_context[field] == 'none':
					given_context[field] = None
				if field in ['analytic_account_ids', 'analytic_tag_ids', 'company_ids', 'account_ids']: #  Needs to be treated differently as they are many2many
					update[field] = [(6, 0, [int(id) for id in given_context[field]])]
				else:
					update[field] = given_context[field]

		if given_context.get('from_report_id') and given_context.get('from_report_model') and report_model == 'account.financial.html.report' and report_id:
			from_report = self.env[given_context['from_report_model']].browse(given_context['from_report_id'])
			to_report = self.env[report_model].browse(report_id)
			if not from_report.get_report_type().date_range and to_report.get_report_type().date_range:
				dates = self.env.user.company_id.compute_fiscalyear_dates(datetime.today())
				update['date_from'] = fields.Datetime.to_string(dates['date_from'])
		if update:
			context.write(update)
		return [context_model, context.id ,update]

	@api.multi
	def get_html_and_data(self, given_context=None):
		result = super(AccountReportContextCommon, self).get_html_and_data(given_context)
		result['report_context']['currency_ids'] = self.currency_ids.ids
		result['report_context']['change_currency_id'] = self.change_currency_id.id
		return result

