from odoo import api, fields, models, SUPERUSER_ID, _


class StdMaterialRequest(models.Model):
    _inherit = 'std.material.request'

    @api.model
    def default_get(self, fields):
        res = super(StdMaterialRequest, self).default_get(fields)
        warehouse_id = self.env['stock.warehouse'].sudo().search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        if warehouse_id:
            picking_type_id = self.env['stock.picking.type'].sudo().search([('warehouse_id', '=', warehouse_id.id),('code','=','internal')], limit=1)
            if picking_type_id:
                res['picking_type'] = picking_type_id.id
        return res