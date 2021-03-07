from odoo import models, fields, api


class mrp_workcenter(models.Model):
    _inherit = 'mrp.workcenter'

    location_id = fields.Many2one('stock.location', 'Location')
    finised_good_location_id = fields.Many2one('stock.location', 'Finished Good Location')
    lost_good_location_id = fields.Many2one('stock.location', 'Lost Good Location')
