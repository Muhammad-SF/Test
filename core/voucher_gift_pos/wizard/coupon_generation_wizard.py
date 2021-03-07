from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
# from pip import req


class CouponGenerateFromVoucherWizard(models.TransientModel):
    _name = 'coupon.voucher.wizard'

    no_of_coupon = fields.Integer(string="No of Coupons per Branch", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    limit_to_partner = fields.Many2many("res.partner", string="Limit to Partner(s)")
    limit_per_partner = fields.Integer(string="Limit per Partner")
    voucher = fields.Many2one('gift.voucher.pos', string="Voucher")
    coupon_branch = fields.Many2many('res.branch', string="Branch", required=True)

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date and self.end_date != fields.Date.today():
            s_date1 = datetime.strptime(self.start_date, '%Y-%m-%d')
            e_date1 = datetime.strptime(self.end_date, '%Y-%m-%d')
            if s_date1 > e_date1:
                self.end_date = False
                return {
                    'warning': {'title': _('Error'), 'message': _('End Date can not below the Start Date'),},
                     }
            ################ Added by Krutarth ################
            """ In this, done when Applicable Start Date below Vouchers Applicable Start Date 
            and when Applicable End Date above Vouchres Applicable End Date."""
            if self.voucher:
                if self.voucher.s_date and self.voucher.e_date:
                    voucher_start_date = datetime.strptime(self.voucher.s_date, '%Y-%m-%d')
                    voucher_end_date = datetime.strptime(self.voucher.e_date, '%Y-%m-%d')
                    if voucher_start_date > s_date1:
                        self.start_date = False
                        return {
                            'warning': {'title': _('Error'), 'message': _('Applicable Start Date can not below Vouchers Applicable Start Date.')}
                        }
                    if voucher_end_date < e_date1:
                        self.end_date = False
                        return {
                            'warning': {'title': _('Error'), 'message': _('Applicable End Date can not set above Vouchres Applicable End Date')}
                        }
            ################ ################ ################

    @api.multi
    def create_coupon_from_voucher(self):
        if self.start_date and self.end_date:
            s_date1 = datetime.strptime(self.start_date, '%Y-%m-%d')
            e_date1 = datetime.strptime(self.end_date, '%Y-%m-%d')
            if s_date1 > e_date1:
                raise ValidationError(_('End Date can not below the Start Date'))
        if self.voucher:
            maximum_coupon_limit = self.voucher.total_number_coupons
            generated_coupon = self.voucher.total_generated_coupons
            selected_branches = len(self.coupon_branch)
            new_coupons = selected_branches * self.no_of_coupon
            check_coupon_total_amount = new_coupons+generated_coupon 
            if maximum_coupon_limit<check_coupon_total_amount:
                raise UserError(_('Exceeding Limit of Maximum token!'))
            for each_branch in self.coupon_branch:
                for i in range(0, self.no_of_coupon):
                    self.env['gift.coupon.pos'].create({
                        'name': self.voucher.name +" "+str(each_branch.name)+" "+ str(i),
                        'voucher': self.voucher.id,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'partner_id': [(6, 0, self.limit_to_partner.ids)],
                        'limit': self.limit_per_partner,
                        'voucher_val': self.voucher.voucher_val,
                        'type': self.voucher.type,
                        'coupon_branch':each_branch.id,
                        # 'state'
                    })