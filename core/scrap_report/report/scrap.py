# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ReturnAnalysis(models.Model):
    _name = "scrap.report"
    _description = "Scrap Report"
    _auto = False
    _rec_name = 'product_id'
    _order = 'product_id desc'

    qty = fields.Float(string='Quantity', readonly=True)
    owner_id = fields.Many2one('res.partner', string="Owner", readonly=True)
    origin = fields.Char(string="Source Document", readonly=True)
    scrap_id = fields.Char(string="Scrap ID")
    reason = fields.Char(string="Reason")
    date_submitted = fields.Date(string='Date Submitted')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)

    def _select(self):
        select_str = """
        SELECT
            min(ss.id) as id,
            ss.name as scrap_id,
            ss.product_id as product_id,
            ss.scrap_qty as qty,
            ss.location_id as location_id,
            ss.owner_id as owner_id,
            ss.origin as origin,
            sr.name as reason,
            ss.date_submitted as date_submitted
        """
        return select_str

    def _from(self):
        from_str = """
             stock_scrap ss left join scrap_reason sr on sr.id = ss.reason_id 
            """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY ss.product_id,
                     ss.scrap_qty,
                     ss.location_id,
                     ss.owner_id,
                     ss.origin,
                     ss.name,
                     sr.name,
                     ss.date_submitted
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM %s
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))
