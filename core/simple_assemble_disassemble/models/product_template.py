# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    material_ids = fields.One2many('component.materials', 'component_id', string='Disassemble')

    @api.multi
    def check_allocation_cost(self):
        self.ensure_one()

        if self.material_ids and len(self.material_ids.ids) > 0:
            total_allocation_cost = 0
            for material in self.material_ids:
                total_allocation_cost += material.allocation_cost

            if int(total_allocation_cost) != 100:
                raise UserError('Allocation Cost (%) must be equal to 100%')

    @api.model
    def create(self, values):
        result = super(ProductTemplate, self).create(values)
        result.check_allocation_cost()
        return result

    @api.multi
    def write(self, values):
        result = super(ProductTemplate, self).write(values)
        for record in self:
            record.check_allocation_cost()
        return result

    @api.multi
    def disassemble_form_view(self):
        self.ensure_one()

        ctx = dict()
        form_id = self.env['ir.model.data'].sudo().get_object_reference('simple_assemble_disassemble', 'res_disassemble_form_view')[1]
        ctx.update({
            'default_product_id': self.id,
        })

        action = {
            'type'      : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'res.disassemble',
            'views'     : [(form_id, 'form')],
            'view_id'   : form_id,
            'target'    : 'new',
            'context'   : ctx,
        }
        return action