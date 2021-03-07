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

from odoo import models, fields, api
from odoo import tools

class commission_report(models.Model):
    """Commission Analysis"""
    _name = "commission.report"
    # _order = 'event_date desc'
    _auto = False


    sale_order = fields.Many2one('sale.order', 'Order Reference', required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    amount_total = fields.Float( string="Total", store=True)

    @api.model_cr
    def init(self):
        """Initialize the sql view for the event registration """
        tools.drop_view_if_exists(self.env.cr, 'commission_report')

        self.env.cr.execute(""" CREATE VIEW commission_report AS (
            SELECT
                e.id::varchar || '/' || coalesce(r.id::varchar,'') AS id,
                e.id AS commission_id,
                e.sale_order AS sale_order,
                e.partner_id AS partner_id,
                e.amount_total As amount_total
            FROM
                commission_commission e
                LEFT JOIN commission_lines r ON (e.sale_order=r.id)

            GROUP BY
                commission_id,
                r.id,
                sale_order,
                e.id,
                e.partner_id,
                e.amount_total
        )
        """)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
