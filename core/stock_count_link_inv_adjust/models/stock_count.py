from odoo import fields, models, api

class StockCountInherit(models.Model):
    _inherit = "stock.count"

    def action_done(self):
        self.action_inventory_adjustment()
        self.inv_id.action_done()
        print("inv id=====1111111=======", self.inv_id)
        self.inv_id.write({'state': 'confirm'})
        self.write({'state': 'close'})
