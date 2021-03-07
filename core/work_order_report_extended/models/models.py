# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime


class workOrder(models.Model):
    _inherit = 'mrp.workorder'
    
    @api.multi
    def print_wo_report(self):
        res = self.env['report'].get_action(self,'work_order_report_extended.wo_extended_report')
        return res
    
    
    def check_consumed(self):
        
        product_list = {}
        if self.material_consumed_line_id:
            for line in self.material_consumed_line_id:
                product_list[line.product_id.id] = line.quantity
        print("===product_list===",product_list)
        return product_list
        
        