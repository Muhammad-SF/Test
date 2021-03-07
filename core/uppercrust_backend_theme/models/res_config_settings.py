# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    selected_theme = fields.Many2one('ir.web.theme', string='Selected Theme')

    @api.model
    def get_default_theme(self, fields):
        selected_theme = self.env['ir.config_parameter'].sudo().get_param('uppercrust_backend_theme.selected_theme', default=False)
        return dict(selected_theme=selected_theme)

    @api.multi
    def set_default_theme(self):
        self.env['ir.config_parameter'].sudo().set_param("uppercrust_backend_theme.selected_theme", self.selected_theme.id)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
