# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResZone(models.Model):
    _name = 'res.zone'
    _description = 'Res Zone'

    name = fields.Char('Zone')
    company_id = fields.Many2one('res.company','Company')
    branch_ids = fields.Many2many('res.branch', id1='user_id', id2='branch_id', string='Branch')
    company_brand_ids = fields.Many2many('company.brand', id1='user_id', id2='company_id', string="Company Brand")


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self.env.context.get('branch_id'):
            print ("cccc--------------------")
            res_ids = []
            for zone in self.search([('branch_ids','in',[self.env.context.get('branch_id')] )]):
                res_ids.append(zone.id)
            args += [['id','in',res_ids]]
        
        return super(ResZone, self).name_search(name, args, operator, limit)



# class ResCompany(models.Model):
#     _inherit = 'res.company'

#     res_zone_id = fields.Many2one('res.zone', 'Zone')

class PosConfig(models.Model):
    _inherit = 'pos.config'

    res_zone_id = fields.Many2one('res.zone', 'Zone')

class PosOrder(models.Model):
    _inherit = 'pos.order'

    res_zone_id = fields.Many2one('res.zone', 'Zone', related='config_id.res_zone_id',readonly=True)