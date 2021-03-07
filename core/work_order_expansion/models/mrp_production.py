from odoo import models, fields, api, _
from datetime import datetime, timedelta

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _generate_raw_moves(self, exploded_lines):
        self.ensure_one()
        moves = self.env['stock.move']
        for bom_lines, line_data in exploded_lines:
            if not bom_lines.is_wip:
                moves += self._generate_raw_move(bom_lines, line_data)
        return moves

