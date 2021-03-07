# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import _, api, exceptions, fields, models


class FloorSyncLog(models.Model):
    _name = "floor.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class TableSyncLog(models.Model):
    _name = "table.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
    
class MasterFloorTableSyncLog(models.Model):
    _name = "master.floor.table.sync.log"
    
    date = fields.Date(string="Date", readonly=True)
    status = fields.Selection([('Success','Success'),('Failed','Failed')], string="Status",readonly=True)
        

