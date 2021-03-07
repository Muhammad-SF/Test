# -*- coding: utf-8 -*-

from odoo import models, fields, api

class WorkCenterBasedAsset(models.Model):
    _inherit = 'mrp.workcenter'

    name_assest = fields.Many2one('asset.master','Work Center Name')

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.name_assest.name or ''
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        records = self.search([('name_assest.name', operator, name)], limit=limit)
        return records.name_get()