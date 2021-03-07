# -*- coding: utf-8 -*
from openerp import api, fields, models,tools,SUPERUSER_ID, _
from odoo.exceptions import UserError
from lxml import etree

class UntakenStock(models.Model):
    _name = "untaken.stock"
            
    @api.model
    def default_get(self, fields):
        res = super(UntakenStock, self).default_get(fields)
        '''inv_lines = self.env['stock.inventory.line'].search([])
        used_products =inv_lines.mapped('product_id') 
        #print"used_products==>>",used_products
        if used_products:
            used_products_lst = used_products.ids
            #print"used_products_lst==>>",used_products_lst
            products = self.env['product.product'].search([('type','=','product')]).filtered(lambda product: product.id not in used_products_lst)
            if products:
                res['product_ids'] = products.ids'''
        return res
        
    name = fields.Char(string='Reference', index=True, required=True)
    date = fields.Datetime('Date', default=fields.Datetime.now, required=True, readonly=True, copy=False)
    action_to_check = fields.Selection([
        ('untakenstock', 'Untaken Stock'),
    ], required=True, string='Action To check', default='untakenstock')
    state = fields.Selection([
        ('draft', 'DAFT'),
        ('in_progress', 'IN PROGRESS'),
        ('validate', 'VALIDATE')
    ], readonly=True, required=True, string='State', default='draft')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',required=True)
    location_id  = fields.Many2one('stock.location','Location',related='warehouse_id.lot_stock_id',required=True, domain=lambda self: [('id', '=', self.warehouse_id.lot_stock_id.id)])
    #product_ids = fields.One2many('product.product', 'untaken_stock_id', string='Untaken Stock Products')
    untaken_stock_line = fields.One2many('untaken.stock.line', 'untaken_stock_id', string='Untaken Stock Products')
    
    
    @api.multi
    def btn_start(self):
        self.state = 'in_progress'
        inv_lines = self.env['stock.inventory.line'].search([])
        used_products =inv_lines.mapped('product_id') 
        if used_products:
            used_products_lst = used_products.ids
            products = self.env['product.product'].search([('type','=','product')]).filtered(lambda product: product.id not in used_products_lst)
            if products:
                for product in products:
                    if product.stock_quant_ids:
                        quant_lst = []
                        for quant in product.stock_quant_ids:
                            str_quant = str(quant.product_id.name) + '=' + str(quant.location_id.id)
                            warehouse_id = False
                            if str_quant not in quant_lst:
                                warehouse = self.env['stock.warehouse'].search([('lot_stock_id','=',quant.location_id.id)],limit=1)
                                if warehouse:
                                    warehouse_id = warehouse.id
                                quant_lst.append(str_quant)
                                if self.warehouse_id.id == warehouse_id:
                                    self.env['untaken.stock.line'].create({'product_id':quant.product_id.id,
                                                                            'untaken_stock_id':self.id,
                                                                            'location_id':quant.location_id.id,
                                                                            'warehouse_id':warehouse_id})
                                                                            
                #self.product_ids = products.ids
        return True
        
    @api.multi
    def btn_end(self):
        self.state = 'validate'
        return True

class UntakenStockLine(models.Model):
    _name = "untaken.stock.line"
    
    untaken_stock_id = fields.Many2one('untaken.stock', string='Untaken Stock')
    product_id = fields.Many2one('product.product', string='Product')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_id  = fields.Many2one('stock.location','Location',required=True)
    
    
'''class ProductProduct(models.Model):
    _inherit = "product.product"
    
    untaken_stock_id = fields.Many2one('untaken.stock', string='Untaken Stock')'''
