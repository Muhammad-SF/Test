# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, api, fields


class GlobalSearchConfigBatch(models.Model):
    _name = 'global.search.config.batch'
    _rec_name = 'model_id'

    @api.multi
    def write(self, vals):
        '''Override to manage customized boolean'''
        if not vals.has_key('customized') and ((vals.get('user_id') and len(vals.keys())>1) or not vals.get('user_id')):
            vals['customized'] = True
        if vals.has_key('template_id') and not vals.get('model_id', False):
            vals['model_id'] = self.env['global.search.config.template'].search([('id','=',vals.get('template_id'))]).model_id.id
        res = super(GlobalSearchConfigBatch, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        '''Override check the values'''
        if vals.has_key('template_id') and not vals.get('model_id', False):
            vals['model_id'] = self.env['global.search.config.template'].search([('id','=',vals.get('template_id'))]).model_id.id
        return super(GlobalSearchConfigBatch, self).create(vals)

    @api.onchange('template_id')
    def _onchange_template_id(self):
        '''To set fields as per template selection.'''
        for rec in self:
            rec.field_ids = [(6, 0, rec.template_id.field_ids.ids)]
            rec.model_id = rec.template_id.model_id.id
            rec.customized = False

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.template_id:
            self._onchange_template_id()
        else:
            self.field_ids = [(6, 0, [])]

    template_id = fields.Many2one('global.search.config.template', 'Template', domian="[('id', in, [])]")
    searches_ids = fields.One2many('global.search.config', 'batch_id', 'User(s)', required=False, readonly=True)
    customized = fields.Boolean('Customized')
    model_id = fields.Many2one('ir.model', 'Model', required=True, )
    field_ids = fields.Many2many('ir.model.fields', string='Fields', domain="[('model_id', '=', model_id), ('name', '!=', 'id'), ('ttype', '!=', 'boolean'), ('selectable', '=', True)]", required="1")

    _sql_constraints = [
        ('uniq_model',
         "UNIQUE(model_id)",
         "The model must be unique."),
    ]

    @api.multi
    def apply_changes_in_searches(self):
        """ Its calling for effects on searches."""
        for rec in self.searches_ids:
            if not rec.customized:
                rec.set_values_template_batch(rec.batch_id)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: