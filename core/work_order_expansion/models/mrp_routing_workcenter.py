from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
import math


class mrp_routing_workcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    is_sequence = fields.Boolean()
    sequence_run = fields.Integer('Sequence', readonly=False)

class mrp_routing(models.Model):
    _inherit = 'mrp.routing'

    @api.model
    def create(self, vals):
        res = super(mrp_routing, self).create(vals)
        sequence = 1
        for line in res.operation_ids.sorted('id', reverse=False):
            line.sequence_run = sequence
            sequence += 1
        return res

    @api.multi
    def write(self, values):
        res = super(mrp_routing, self).write(values)
        sequence = 1
        for line in self.operation_ids.sorted('id', reverse=False):
            line.sequence_run = sequence
            sequence += 1
        return res