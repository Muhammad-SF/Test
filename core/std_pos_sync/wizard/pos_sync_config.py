# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, exceptions, fields, models


class POSSyncConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'pos.sync.config'

    master_url = fields.Char(string="Master URL")
    database_name = fields.Char(string="Database Name")
    company_name = fields.Char(string="Company Name")
    username = fields.Char(string="Username")
    password = fields.Char(string="Password")
    
    @api.model
    def get_default_master_url(self, fields):
        master_url = self.env.ref('std_pos_sync.master_url').value
        return {'master_url': str(master_url)}

    @api.multi
    def set_default_master_url(self):
        for record in self:
            self.env.ref('std_pos_sync.master_url').write({'value': str(record.master_url)})
            
    @api.model
    def get_default_database_name(self, fields):
        database_name = self.env.ref('std_pos_sync.database_name').value
        return {'database_name': str(database_name)}

    @api.multi
    def set_default_database_name(self):
        for record in self:
            self.env.ref('std_pos_sync.database_name').write({'value': str(record.database_name)})
            
    @api.model
    def get_default_company_name(self, fields):
        company_name = self.env.ref('std_pos_sync.company_name').value
        return {'company_name': str(company_name)}

    @api.multi
    def set_default_company_name(self):
        for record in self:
            self.env.ref('std_pos_sync.company_name').write({'value': str(record.company_name)})
            
    @api.model
    def get_default_username(self, fields):
        username = self.env.ref('std_pos_sync.username').value
        return {'username': str(username)}

    @api.multi
    def set_default_username(self):
        for record in self:
            self.env.ref('std_pos_sync.username').write({'value': str(record.username)})
            
    @api.model
    def get_default_password(self, fields):
        password = self.env.ref('std_pos_sync.password').value
        return {'password': str(password)}

    @api.multi
    def set_default_password(self):
        for record in self:
            self.env.ref('std_pos_sync.password').write({'value': str(record.password)})
            
