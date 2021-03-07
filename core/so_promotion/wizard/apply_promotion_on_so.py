from odoo import api, fields, models, _


class apply_promotion_on_so(models.TransientModel):
    
    _name = "apply.sale.promotion"
    
    sale_promotion_id = fields.Many2one('sale.promotion', string='Discounts')

    @api.multi
    def action_apply(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        if active_id:
            sale = self.env['sale.order'].browse(active_id)
            sale.apply_promotion(self.sale_promotion_id)
        return True
