# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError,UserError


class ProductAttribute(models.Model):
    _inherit = "product.attribute"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ProductAttribute, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.branch_id:
                branch_id = str(rec.create_uid.branch_id.id)
            else:
                raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ProductAttributeValue, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.branch_id:
                branch_id = str(rec.create_uid.branch_id.id)
            else:
                raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    pt_pos_sync_id = fields.Char(string="Product Template POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ProductTemplate, self).create(vals)
        if not rec.pt_pos_sync_id:
            branch_id = ''
            if rec.company_id:
                if rec.company_id.branch_id:
                    branch_id = str(rec.company_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in company.'))
            rec.pt_pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class ProductProduct(models.Model):
    _inherit = "product.product"
    
    pos_sync_id = fields.Char(string="Product Variant POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ProductProduct, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.company_id:
                if rec.company_id.branch_id:
                    branch_id = str(rec.company_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in company.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class PosCategory(models.Model):
    _inherit = "pos.category"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(PosCategory, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.company_id:
                if rec.create_uid.company_id.branch_id:
                    branch_id = str(rec.create_uid.company_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in company.'))
            else:
                raise UserError(_('Please configure company in user.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class ProductCategory(models.Model):
    _inherit = "product.category"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ProductCategory, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.company_id:
                if rec.create_uid.company_id.branch_id:
                    branch_id = str(rec.create_uid.company_id.branch_id.id)
                else:
                    raise UserError(_('Please configure branch in company.'))
            else:
                raise UserError(_('Please configure company in user.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec
        
class ProductBrand(models.Model):
    _inherit = "product.brand"
    
    pos_sync_id = fields.Char(string="POS Sync ID", readonly=True)
    
    @api.model
    def create(self, vals):
        rec = super(ProductBrand, self).create(vals)
        if not rec.pos_sync_id:
            branch_id = ''
            if rec.create_uid.branch_id:
                branch_id = str(rec.create_uid.branch_id.id)
            else:
                raise UserError(_('Please configure branch in User.'))
            rec.pos_sync_id = branch_id+'pos'+str(rec.id)
        return rec

    

