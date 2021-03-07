
from odoo import fields, models, tools, api


class SupplierRatingReportView(models.Model):
    _name = 'supplier.rating.report.view'
    _auto = False

    name = fields.Many2one('supplier.rating', string='Supplier Rating')
    date_rating = fields.Datetime('Rating Date')
    average_rating_next = fields.Float('Average Rating')
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate')], string='State')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    name_rating = fields.Char('Rating Name')
    value_value = fields.Float('Total Rating Value')
    score = fields.Float('Score')

    def _select(self):
        select_str = """
        min(sr.id) as id, 
        sr.id as name, 
        sr.average_rating_next as average_rating_next, 
        sr.date_rating as date_rating,
        sr.state as state,
        sr.partner_id as partner_id,
        rl.name as name_rating,
        rl.value_value as value_value,
        rl.score_one as score
        """
        return select_str

    def _from(self):
        from_str = """
            supplier_rating sr
            join ratings_lines as rl on (rl.rating_id=sr.id)
         """
        return from_str

    def _group_by(self):
        group_by_str = """
            group by sr.id, sr.average_rating_next, sr.date_rating, sr.state, sr.partner_id, rl.name, rl.value_value, rl.score_one
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as ( SELECT
                   %s
                   FROM %s
                   %s
                   )""" % (self._table, self._select(), self._from(), self._group_by()))