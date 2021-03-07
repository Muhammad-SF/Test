# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProjectConfigSettings(models.TransientModel):
    _inherit = 'project.config.settings'

    proj_limit = fields.Selection([
        ('in_project', "In each project"),
        ('cross_project', "Cross project")
        ], string="Project Limit", default='in_project')
    
    limit_task = fields.Integer(string="Task Limit")


    @api.multi
    def set_default_proj_limit(self):
#         check = self.env.user.has_group('base.group_system')
        Values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            Values.set_default('project.config.settings', 'proj_limit', config.proj_limit)

    @api.multi
    def set_default_limit_task(self):
#         check = self.env.user.has_group('base.group_system')
        Values = self.env['ir.values'].sudo() or self.env['ir.values']
        for config in self:
            Values.set_default('project.config.settings', 'limit_task', int(config.limit_task))
