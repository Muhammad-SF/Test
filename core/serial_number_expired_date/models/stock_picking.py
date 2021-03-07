# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api , _
import datetime
# from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round

class PackOperation(models.Model):
    _inherit = 'stock.pack.operation.lot'
    
    expired_date = fields.Datetime(string='Expiry Date', store=True)
    
class Picking(models.Model):
    _inherit = "stock.picking"
    
    def _create_lots_for_picking(self):
        Lot = self.env['stock.production.lot']
        for pack_op_lot in self.mapped('pack_operation_ids').mapped('pack_lot_ids'):
            if not pack_op_lot.lot_id:
                lot = Lot.create({'name': pack_op_lot.lot_name, 'product_id': pack_op_lot.operation_id.product_id.id, 'use_date':pack_op_lot.expired_date,'expired_date':pack_op_lot.expired_date})
                pack_op_lot.write({'lot_id': lot.id})
        # TDE FIXME: this should not be done here
        self.mapped('pack_operation_ids').mapped('pack_lot_ids').filtered(lambda op_lot: op_lot.qty == 0.0).unlink()
    create_lots_for_picking = _create_lots_for_picking

class Quant(models.Model):
    _inherit = "stock.quant"
    
    expired_date = fields.Date(related='lot_id.use_date',string='Expiry Date', store=True)
    


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    expired_date = fields.Datetime(string='Expiry Date', store=True)

    # Assign dates according to products data
    @api.model
    def create(self, vals):
        dates = self._get_dates(vals.get('product_id'))
        product_id = vals.get('product_id')
        exp_date = vals.get('expired_date')
        
        if exp_date: 
            expired_date = datetime.datetime.strptime(exp_date, DEFAULT_SERVER_DATETIME_FORMAT)
        else:
            expired_date = datetime.datetime.now()

        product = self.env['product.product'].browse(product_id)

        if product:
            for d in dates.keys():
                if d in ['use_date']:
                    date = (expired_date - datetime.timedelta(days=product.removal_time)) + datetime.timedelta(days=product.use_time)
                    vals['use_date'] = fields.Datetime.to_string(date)
                
                if d in ['life_date']:
                    date = (expired_date - datetime.timedelta(days=product.removal_time)) + datetime.timedelta(days=product.life_time)
                    vals['life_date'] = fields.Datetime.to_string(date)
                
                if d in ['alert_date']:
                    date = (expired_date - datetime.timedelta(days=product.removal_time)) + datetime.timedelta(days=product.alert_time)
                    vals['alert_date'] = fields.Datetime.to_string(date)

                if d in ['removal_date']:
                    date = expired_date
                    vals['removal_date'] = fields.Datetime.to_string(date)

        return super(StockProductionLot, self).create(vals)


