# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models

class ProductAttributeSyncLog(models.Model):
    _name = "product.attribute.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)

class ProductAttrValueSyncLog(models.Model):
    _name = "product.attrs.value.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)

class ProductSyncLog(models.Model):
    _name = "product.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class CustomerSyncLog(models.Model):
    _name = "customer.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
        
class ProductCategSyncLog(models.Model):
    _name = "product.categ.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)

class POSProductCategSyncLog(models.Model):
    _name = "posproduct.categ.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)

class AccountJournalSyncLog(models.Model):
    _name = "account.journal.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class PosPromotionSyncLog(models.Model):
    _name = "pos.promotion.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class LoyaltyProgramSyncLog(models.Model):
    _name = "loyalty.program.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)

class GiftVoucherSyncLog(models.Model):
    _name = "gift.voucher.pos.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)

class GiftCouponSyncLog(models.Model):
    _name = "gift.coupon.pos.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class MasterGiftCouponSyncLog(models.Model):
    _name = "master.gift.coupon.pos.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)

class MasterCustomerSyncLog(models.Model):
    _name = "master.customer.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class ProductBrandSyncLog(models.Model):
    _name = "product.brand.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class POSConfigSyncLog(models.Model):
    _name = "pos.config.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
