from odoo import fields, api, models, _
from odoo.exceptions import UserError


class mrp_material_consumed(models.Model):
    _inherit = 'mrp.material.consumed'

    @api.multi
    def update_current_bom(self):
        print"update_current_bom "
        print"del ",self
        bom_id = self.workorder_id.production_id.bom_id
        if bom_id:
            bom_line_obj = self.env['mrp.bom.line']
            bom_existing_lines = self.workorder_id.production_id.bom_id.bom_line_ids
            if self.line_ids:
                if bom_existing_lines:
                    bom_existing_lines.unlink()
                for line in self.line_ids:
                    # bom_lines = []
                    # for bom_line in self.workorder_id.production_id.bom_id.bom_line_ids:
                    #     if line.product_id.id == bom_line.product_id.id:
                    #         bom_line.unlink()
                    bom_line_obj.create({
                        'product_id': line.product_id.id,
                        'product_qty': line.quantity,
                        'product_uom_id': line.product_uom_id.id,
                        'bom_id': bom_id.id,
                    })
                    print"bom_line_obj ",bom_line_obj
                    # else:
                    #     bom_line_obj.create({
                    #         'product_id': line.product_id.id,
                    #         'product_qty': line.quantity,
                    #         'product_uom_id': line.product_uom_id.id,
                    #         'bom_id': bom_id.id
                    #     })
                print"self.workorder_id.production_id.bom_id ",self.workorder_id.production_id.bom_id
                self.workorder_id.production_id.bom_id.write({'product_qty':self.finished_goods,'code':self.name})
                return {
                    'name': _('Bill Of Matrial'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.bom',
                    'res_id': self.workorder_id.production_id.bom_id.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {}
                }
            else:
                raise UserError(_("There is no Material(s) added inside 'Material Consumed' lines! "))
        else:
            raise UserError(_("Bom is not define"))

    @api.multi
    def create_new_bom(self):
        bom_id = self.workorder_id.production_id.bom_id
        bom_obj = self.env['mrp.bom']
        bom_line_obj = self.env['mrp.bom.line']
        if bom_id:
            bom_new_id = bom_obj.create({
                'product_tmpl_id': bom_id.product_tmpl_id.id,
                'product_qty': bom_id.product_qty,
                'routing_id':bom_id.routing_id.id,
            })
            if bom_new_id:
                for line in self.line_ids:
                    bom_line_obj.create({
                        'product_id': line.product_id.id,
                        'product_qty': line.quantity,
                        'product_uom_id': line.product_uom_id.id,
                        'bom_id': bom_new_id.id
                    })
                bom_new_id.write({'product_qty':self.finished_goods,'code':self.name})
                return {
                    'name': _('Bill Of Matrial'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'mrp.bom',
                    'res_id': bom_new_id.id,
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {}
                }
        else:
            raise UserError(_("Bom is not define"))
