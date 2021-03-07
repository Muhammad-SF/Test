
from odoo import models, fields, api, _

class ShowMaterialDonePopup(models.TransientModel):
    _name = 'show.material.done.popup'

    @api.multi
    def force_done_material_request(self):
        for record in self:
            material_request_id = self.env['std.material.request'].browse(self._context.get('active_ids'))
            material_request_id.write({'status': 'done'})