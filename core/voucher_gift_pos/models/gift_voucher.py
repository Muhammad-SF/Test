# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
import string
import random
import logging

_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from datetime import date
from lxml import etree


class GiftVoucherPos(models.Model):
    _inherit = 'gift.voucher.pos'

    @api.one
    @api.depends('e_date')
    def _check_voucher_status(self):
        voucher_status = False
        current_datetime = fields.Date.today()
        if self.e_date:
            if self.e_date >= current_datetime:
                voucher_status = True
        self.check_voucher = voucher_status

    @api.one
    @api.depends('generated_coupons')
    def _token_issued(self):
        for rec in self:
            rec.total_generated_coupons = len(rec.generated_coupons)
            ############## Added by Krutarth ##############
            if rec.total_generated_coupons == rec.total_number_coupons:
                rec.state = 'complated'
            else:
                if rec.total_generated_coupons == 0:
                    rec.state = 'draft'
                else:
                    rec.state = 'inprogress'
            ###############################################

    min_value = fields.Integer(string="Minimum Voucher Value", required=False)
    max_value = fields.Integer(string="Maximum Voucher Value", required=False)
    total_number_coupons = fields.Integer(string="Maximum Coupons", required=True)
    generated_coupons = fields.One2many('gift.coupon.pos', 'voucher', string="Generated Coupons")
    check_voucher = fields.Boolean(compute='_check_voucher_status')
    voucher_type = fields.Selection(selection_add=[('Brand', 'Brand')])
    brand_ids = fields.Many2many('product.brand', string="Brand(s)")  # use from product_brand
    product_id = fields.Many2many('product.product', string="Product(s)")
    product_categ = fields.Many2many('pos.category', string="Product Category(s)")
    # coupon generation condition
    order_above = fields.Float(string="Order Above")
    min_order_value = fields.Float(string="Min Order Value")
    voucher_val = fields.Float(string="Voucher Value", required=True)
    total_generated_coupons = fields.Integer(compute='_token_issued')
    s_date = fields.Date("Applicable Start Date",
                         help="- This is used to tell the start date to use the coupons that have been generated previously.\n - This is used to determine how long the validity period of the coupons")
    e_date = fields.Date("Applicable End Date",
                         help="- This is used to tell the End Date to use the coupons that have been generated previously.\n - This is used to determine how long the validity period of the coupons")
    start_date = fields.Date("Start Date",
                             help="- This is used to notify users of the start date for this voucher to be used."
                                  "\n - This also gives the start date for the voucher to be generated")
    end_date = fields.Date("End Date",
                           help="- This is used to notify users of the End Date for this voucher to be used.\n - This also gives the End Date for the voucher to be generated")
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('inprogress', 'Inprogress'),
                   ('complated', 'Completed'),
                   ],
        string='State', default='draft', store=True, compute='_token_issued')
    type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ], store=True, default='fixed', required=True)
    customer_required = fields.Boolean('Customer is Compulsory')

    @api.multi
    def write(self, vals):
        res = super(GiftVoucherPos, self).write(vals)
        if 'total_number_coupons' in vals:
            for rec in self:
                if rec.total_number_coupons == rec.total_generated_coupons:
                    rec.state = 'complated'
        return res

    @api.model
    def create(self, vals):
        res = super(GiftVoucherPos, self).create(vals)
        if res.total_number_coupons == res.total_generated_coupons:
            res.state = 'complated'
        return res

    #  added by mayank=================

    @api.model
    def process_voucher_expiry_check_scheduler(self):
        loyalty_program_ids = self.env['gift.voucher.pos'].search([])
        for val in loyalty_program_ids:
            # expired_coupons_objs = self.env['gift.coupon.pos'].search([('voucher','=',val.id)])
            # total = len(expired_coupons_objs.ids)
            # flag = 0
            # for data in expired_coupons_objs:
            #     if data.total_avail == 0:
            #         flag += 1
            # today_date1 = date.today()
            if val.end_date:
                curr_date1 = datetime.now()
                curr_date = curr_date1.strftime("%Y-%m-%d")
                f_edate = val.end_date

                date_end = datetime.strptime(str(f_edate), '%Y-%m-%d')
                today_date_f = datetime.strptime(str(curr_date), '%Y-%m-%d')

                if date_end < today_date_f and val.state == 'inprogress':
                    val.state = 'complated'

            if val.total_number_coupons == val.total_generated_coupons and val.state == 'inprogress':
                val.state = 'complated'

            # if expired_coupons_objs:
            #     if total == flag and val.state == 'inprogress' :
            #         val.state = 'complated'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(GiftVoucherPos, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                          submenu=submenu)
        doc = etree.XML(res['arch'])
        if (view_type == 'form' or view_type == 'tree') and self.env.user.has_group(
                'voucher_gift_pos.group_gift_voucher_user') and not self.env.user.has_group(
            'voucher_gift_pos.group_gift_voucher_admin') and self.env.user.id != SUPERUSER_ID:
            for node in doc.xpath("//form"):
                node.set('create', 'false')
                node.set('edit', 'false')
            for node in doc.xpath("//tree"):
                node.set('create', 'false')
                node.set('edit', 'false')
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def approved_voucher_for_create_coupon(self):
        self.state = 'inprogress'

    @api.onchange('start_date', 'end_date')
    def onchangend_date(self):
        if self.start_date and self.end_date and self.end_date != fields.Date.today():
            start_date1 = datetime.strptime(self.start_date, '%Y-%m-%d')
            end_date1 = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start_date1 > end_date1:
                self.end_date = False
                return {
                    'warning': {'title': _('Error'), 'message': _('End Date can not below the Start Date'), },
                }

    @api.onchange('s_date', 'e_date')
    def onchange_date(self):
        if self.s_date and self.e_date and self.e_date != fields.Date.today():
            s_date1 = datetime.strptime(self.s_date, '%Y-%m-%d')
            e_date1 = datetime.strptime(self.e_date, '%Y-%m-%d')
            if s_date1 > e_date1:
                self.e_date = False
                return {
                    'warning': {'title': _('Error'), 'message': _('Applicable End Date can not below the Applicable Start Date'), },
                }

    @api.constrains('s_date', 'e_date', 'start_date', 'end_date')
    def constrain_date(self):
        if self.start_date and self.end_date:
            start_date1 = datetime.strptime(self.start_date, '%Y-%m-%d')
            end_date1 = datetime.strptime(self.end_date, '%Y-%m-%d')
            if start_date1 > end_date1:
                raise ValidationError(_('End Date can not below the Start Date'))
        if self.s_date and self.e_date:
            s_date1 = datetime.strptime(self.s_date, '%Y-%m-%d')
            e_date1 = datetime.strptime(self.e_date, '%Y-%m-%d')
            if s_date1 > e_date1:
                raise ValidationError(_('Applicable End Date can not below the Applicable Start Date'))

    @api.constrains('min_value','max_value')
    def check_minmax(self):
        if self.type == 'percentage':
            if self.max_value < self.min_value:
                raise UserError(_("Please check the Max/Min value"))

    @api.multi
    def create_coupon_from_voucher(self):
        self.state = 'inprogress'
        """
        :return:
        Action for wizard
        """
        return {
            'name': _("Generate Coupon"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('voucher_gift_pos.coupon_voucher_wizard_form_view').id,
            'view_type': 'form',
            'res_model': 'coupon.voucher.wizard',
            'target': 'new',
            'context': {'default_voucher': self.id, 'default_customer_required': self.customer_required,
                        'default_start_date': self.s_date}
        }


class PosOrder(models.Model):
    _inherit = 'pos.order'
    coupon_availed = fields.Many2one('gift.coupon.pos', string="Coupons")

    @api.model
    def create_from_ui(self, orders):
        order_ids = super(PosOrder, self).create_from_ui(orders)
        for order in orders:
            order_name = order['data']['name']
            pos_order = self.env['pos.order'].sudo().search([('pos_reference', '=', str(order_name))], limit=1)
            if pos_order and ('coupon_availed' in order['data']):
                if order['data']['coupon_availed']:
                    pos_order.write({'coupon_availed': int(order['data']['coupon_availed'])})
        return order_ids


class GiftCouponPos(models.Model):
    _inherit = 'gift.coupon.pos'

    def get_code_by_settings(self):
        size = 7
        code_type = self.env['ir.config_parameter'].get_param('voucher_gift_pos.pos_coupon_code', False)
        if code_type:
            if code_type and int(code_type) == 3:
                chars = string.ascii_uppercase
                return ''.join(random.choice(chars) for _ in range(size))
            elif code_type and int(code_type) == 2:
                chars = string.digits
                return ''.join(random.choice(chars) for _ in range(size))
            else:
                chars = string.ascii_uppercase + string.digits
                return ''.join(random.choice(chars) for _ in range(size))
        else:
            chars = string.ascii_uppercase + string.digits
            return ''.join(random.choice(chars) for _ in range(size))

    code = fields.Char(string="Code", default=get_code_by_settings)
    min_order_value = fields.Float(string="Min Order Value")
    partner_id = fields.Many2many('res.partner', string="Limit to Partner(s)")
    is_stackable = fields.Boolean("Stackable")
    sequence = fields.Integer(string="Sequence")
    check_coupon = fields.Boolean(compute='_check_coupon_status')
    coupon_branch = fields.Many2one('res.branch', string="Branch")
    customer_required = fields.Boolean('Customer is Compulsory')

    @api.one
    @api.depends('partner_id', 'voucher')
    def _check_coupon_status(self):
        coupon_status = False
        if (not self.partner_id) and self.voucher.check_voucher:
            coupon_status = True
        self.check_coupon = coupon_status

    @api.multi
    def check_stackable_coupon(self, args):
        coupon_code = str(args['coupon_pos'])
        order_name = str(args['ordername'])
        coupon_obj = self.env['gift.coupon.pos']
        used_coupons = self.env['partner.coupon.pos']
        coupon_ids = used_coupons.search([('order_name', '=', order_name)])

        allow_new_coupon = True
        if coupon_ids:
            for each_coupon in coupon_ids:
                used_coupon = each_coupon.coupon_pos
                used_coupon_id = coupon_obj.search([('code', '=', used_coupon)])
                if used_coupon_id:
                    allow_new_coupon = False
                    if used_coupon_id.is_stackable:
                        allow_new_coupon = True

        if allow_new_coupon and coupon_ids:
            new_coupon = coupon_obj.search([('code', '=', coupon_code)])
            if new_coupon:
                allow_new_coupon = False
                if new_coupon.is_stackable:
                    allow_new_coupon = True
        return allow_new_coupon

    @api.multi
    def find_coupon(self, args, order_dict):
        today = datetime.today()
        sql_query = """SELECT DISTINCT coupon_availed AS id FROM pos_order """
        self.env.cr.execute(sql_query)
        exclude_ids = [line.get('id') for line in self.env.cr.dictfetchall() if (line.get('id') != None)]
        voucher_id = int(args['voucher_id'])
        branch_id = int(args['branch_id'])
        coupon_obj = self.env['gift.coupon.pos']
        coupon_ids = coupon_obj.search(
            [('coupon_branch', '=', branch_id), ('voucher', '=', voucher_id), ('total_avail', '>', 0),
             ('end_date', '>=', str(today)), ('id', 'not in', exclude_ids)], limit=1)
        return_dict = {}
        if coupon_ids:
            return_dict = {'coupon_id': coupon_ids.id, 'coupon_code': coupon_ids.code}
        return return_dict

    @api.model
    def get_gift_voucher_from_pos(self, data=None):
        if data:
            coupon = self.env['gift.coupon.pos'].search([('name', '=', data['name'])], limit=1)
            return {'coupon': coupon.code}

    @api.model
    def create_gift_voucher_from_pos(self, data=None):
        if data:
            voucher = self.env['gift.voucher.pos'].search(
                [('min_order_value', '<=', data['amount_total']), ('min_order_value', '>', 0)],
                order='min_order_value asc', limit=1)
            if voucher:
                coupon_name = voucher.name
                if 'name' in data:
                    coupon_name = data['name']
                create_dict = {'name': coupon_name,
                               'voucher': voucher.id,
                               'min_order_value': voucher.min_order_value,
                               'voucher_val': voucher.voucher_val,
                               'type': voucher.type}
                if data['partner_id'] and 1 != 1:
                    create_dict['partner_id'] = [(6, 0, [data['partner_id']])]
                coupon = self.env['gift.coupon.pos'].create(create_dict)
                return {'coupon': coupon.code}


class CouponPartnerPos(models.Model):
    _inherit = 'partner.coupon.pos'

    voucher = fields.Many2one('gift.voucher.pos', string="Voucher", )
    date_used = fields.Date(string="Date Used")
    coupon_amount = fields.Float(string="Coupon Amount")
    order_amount = fields.Float(string="Order Amount")
    order_name = fields.Char(string="Order Name")

    def update_history(self, vals):
        if vals:
            h_obj = self.env['partner.coupon.pos']
            if vals.get('partner_id', False):
                history = h_obj.search([('coupon_pos', '=', vals['coupon_pos']),
                                        ('partner_id', '=', vals['partner_id'])], limit=1)
            else:
                history = False
            coupon = self.env['gift.coupon.pos'].search([('code', '=', vals['coupon_pos'])], limit=1)
            if history:
                history.number_pos += 1
                coupon.total_avail -= 1
            else:
                coupon.total_avail -= 1
                rec = {'partner_id': vals.get('partner_id', False),
                       'number_pos': 1,
                       'coupon_pos': vals['coupon_pos'],
                       'voucher': coupon.voucher.id,
                       'date_used': fields.datetime.today(),
                       'coupon_amount': vals['coupon_amount'],
                       'order_amount': vals['order_amount'],
                       'order_name': vals['order_name']}
                h_obj.create(rec)
            return True

    def delete_history_from_current_order(self, order_name=None):
        if order_name:
            history_obj = self.env['partner.coupon.pos'].search([('order_name', '=', order_name)])
            history_obj.unlink()
            return True
