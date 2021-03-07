from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class PosConfigImage(models.Model):
    _inherit = 'pos.config'

    image = fields.Binary(string='Image')
    
class PosConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_coupon_code = fields.Selection([
        (1, "Alphanumeric"),
        (2, "Numbers"),
        (3, "Alphabet")
    ], string="Auto Generated Code")

    @api.model
    def get_default_pos_coupon_code(self, fields):
        ir_conf_param_obj = self.env['ir.config_parameter']
        return {
            'pos_coupon_code': safe_eval(ir_conf_param_obj.get_param('voucher_gift_pos.pos_coupon_code', 'False')),
        }

    @api.multi
    def set_pos_coupon_code(self):
        self.ensure_one()
        ir_conf_param_obj = self.env['ir.config_parameter']
        ir_conf_param_obj.set_param('voucher_gift_pos.pos_coupon_code', repr(self.pos_coupon_code))