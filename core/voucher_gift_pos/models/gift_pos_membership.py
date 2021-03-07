from odoo import api,fields,models

class PosMember(models.Model):
    _inherit = 'gift.voucher.pos'
    
    limit_to_membership = fields.Many2one('loyalty.program', string='Limit to Membership')
    
class GiftCouponPOS(models.Model):
    _inherit = 'gift.coupon.pos'
    
    membership_related = fields.Many2one('loyalty.program',
    'Membership', related='voucher.limit_to_membership',
     readonly=True) 
    
    
