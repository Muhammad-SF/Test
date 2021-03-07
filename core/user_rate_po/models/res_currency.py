# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class res_currency(models.Model):
    _inherit = 'res.currency'

    conversion = fields.Float(compute='_compute_current_conversion', string='Conversion')

    @api.multi
    @api.depends('rate_ids.conversion')
    def _compute_current_conversion(self):
        date = self._context.get('date') or fields.Datetime.now()
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        query = """SELECT c.id, (SELECT r.conversion FROM res_currency_rate r
                                      WHERE r.currency_id = c.id AND r.name <= %s
                                        AND (r.company_id IS NULL OR r.company_id = %s)
                                   ORDER BY r.company_id, r.name DESC
                                      LIMIT 1) AS conversion
                       FROM res_currency c
                       WHERE c.id IN %s"""
        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_conversions = dict(self._cr.fetchall())
        for currency in self:
            currency.conversion = currency_conversions.get(currency.id) or 0.00

res_currency()