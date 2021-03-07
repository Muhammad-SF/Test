# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountCommonReport(models.TransientModel):
    _inherit = 'account.common.report'

    def _build_contexts(self,data):
        result = {}
        if (data['model'] == 'ir.ui.menu'):
            result['chart_account_id'] = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
        return super(AccountCommonReport, self)._build_contexts(data)

AccountCommonReport()