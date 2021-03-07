from odoo import models,fields,api

class InheritStocklanded(models.Model):
    _inherit = 'stock.landed.cost'
    
    Seq_num = fields.Char(string = 'Sequence number', index=True, default='/')
    
    
    @api.model
    def create(self,vals):
        obj = super(InheritStocklanded,self).create(vals)
        if obj.Seq_num == '/':
            number = self.env['ir.sequence'].get('landed.cost.sequence') or '/'
            obj.write({'Seq_num': number})
            
        return obj