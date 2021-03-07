from odoo import api, fields, models


class PosPromotion(models.Model):
    _inherit = 'pos.promotion'

    is_generate_coupon = fields.Boolean("Generate Coupon", )

    voucher = fields.Many2one('gift.voucher.pos', string="Voucher")
    no_of_coupon = fields.Integer(string="No of Coupons")
    is_stackable = fields.Boolean("Stackable", )
    # start_date = fields.Date(string="Start Date")
    # end_date = fields.Date(string="End Date")
    limit_to_partner = fields.Boolean(string="Limit to Partner", )
    voucher_amount = fields.Float(string="Voucher Amount")
    amount_type = fields.Selection([('fixed', 'Fixed Amount'), ('percentage', 'Percentage'), ],
                                   store=True, string="Type", default='fixed')
