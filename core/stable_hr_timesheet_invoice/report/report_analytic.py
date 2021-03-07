# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from odoo import fields, models
from odoo import tools
from odoo.addons import decimal_precision as dp


class report_analytic_account_close(models.Model):
    _name = "report.analytic.account.close"
    _description = "Analytic account to close"
    _auto = False

    name = fields.Many2one('account.analytic.account', 'Analytic account', readonly=True)
    # state = fields.Char('Status', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    # quantity_max = fields.Float('Max. Quantity', readonly=True)
    balance = fields.Float('Balance', readonly=True)
    # date_deadline = fields.Date('Deadline', readonly=True)

    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'report_analytic_account_close')
        cr.execute("""
            create or replace view report_analytic_account_close as (
                select
                    a.id as id,
                    a.id as name,
                    sum(l.unit_amount) as quantity,
                    sum(l.amount) as balance,
                    a.partner_id as partner_id
                from
                    account_analytic_line l
                right join
                    account_analytic_account a on (l.account_id=a.id)
                group by
                    a.id,a.partner_id
            )""")

class report_account_analytic_line_to_invoice(models.Model):
    _name = "report.account.analytic.line.to.invoice"
    _description = "Analytic lines to invoice report"
    _auto = False

    name = fields.Char('Year', required=False, readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    account_id = fields.Many2one('account.analytic.account', 'Analytic account', readonly=True)
    product_uom_id = fields.Many2one('product.uom', 'Unit of Measure', readonly=True)
    unit_amount = fields.Float('Units', readonly=True)
    sale_price = fields.Float('Sale price', readonly=True, digits=dp.get_precision('Product Price'))
    amount = fields.Float('Amount', readonly=True, digits=dp.get_precision('Account'))
    month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'), ('06', 'June'),
         ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'), ('11', 'November'),
         ('12', 'December')], 'Month', readonly=True)

    _order = 'name desc, product_id asc, account_id asc'

    def init(self):
        cr = self._cr
        tools.drop_view_if_exists(cr, 'report_account_analytic_line_to_invoice')
        cr.execute("""
            CREATE OR REPLACE VIEW report_account_analytic_line_to_invoice AS (
                SELECT
                    DISTINCT(to_char(l.date,'MM')) as month,
                    to_char(l.date, 'YYYY') as name,
                    MIN(l.id) AS id,
                    l.product_id,
                    l.account_id,
                    SUM(l.amount) AS amount,
                    SUM(l.unit_amount*t.list_price) AS sale_price,
                    SUM(l.unit_amount) AS unit_amount,
                    l.product_uom_id
                FROM
                    account_analytic_line l
                left join
                    product_product p on (l.product_id=p.id)
                left join
                    product_template t on (p.product_tmpl_id=t.id)
                WHERE
                    (invoice_id IS NULL) and (to_invoice IS NOT NULL)
                GROUP BY
                    to_char(l.date, 'YYYY'), to_char(l.date,'MM'), product_id, product_uom_id, account_id
            )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

