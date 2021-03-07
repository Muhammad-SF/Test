# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReorderMailList(models.Model):
    _name = 'reorder.mail.list'
    _description = 'Reorder Mail Receiver'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    user_id = fields.Many2one('res.users', string="Receiver")
    location_id = fields.Many2one('stock.location', string="Location")
    product_id = fields.Many2one('product.product', string="Product")
    action_name = fields.Char(string="Action")
    minimum_qty = fields.Float(string="Qty")
    maximum_qty = fields.Float(string="Max Qty")
    current_qty = fields.Float(string="Qty")
    product_qty = fields.Float(string="Product qty")
    supplier_id = fields.Many2one('res.partner', string="Supplier", domain="[('supplier', '=', True)]")
    source_loc_id = fields.Many2one('stock.location', 'Source Location', domain=[('usage', '=', 'internal')])
    stock_loc_id = fields.Many2one('stock.location')
    warehouse_id = fields.Many2one('stock.warehouse')
    reordering_rule = fields.Char('Reordering Rule')
    company_id = fields.Many2one('res.company', 'Company')
    lead_days = fields.Integer('Lead Time')
    lead_type = fields.Selection([
        ('net', 'Day(s) to get the products'),
        ('supplier', 'Day(s) to purchase')
    ], 'Lead Type')

    @api.model
    def create(self, vals):
        res = super(ReorderMailList, self).create(vals)
        if res:
            user_obj = self.env['user.mail.data']
            user = user_obj.search([('user_id', '=', res.user_id.id)])
            if not user:
                user = user_obj.sudo().create({'user_id': res.user_id.id})

            # for location
            u_location_obj = self.env['user.location']
            location = u_location_obj.search([('user_mail_id', '=', user.id), ('location_id', '=', res.location_id.id)])
            if not location:
                location = u_location_obj.sudo().create({'user_mail_id': user.id, 'location_id': res.location_id.id})

            # create detail list
            data = {
                'user_mail_id': user.id,
                'user_loc_id': location.id,
                'product_id': res.product_id.id,
                'action_name': res.action_name,
                'minimum_qty': res.minimum_qty,
                'maximum_qty': res.maximum_qty,
                'current_qty': res.current_qty,
                'product_qty': res.product_qty,
                'supplier_id': res.supplier_id.id,
                'source_loc_id': res.source_loc_id.id,
                'warehouse_id': res.warehouse_id.id,
                'stock_loc_id': res.stock_loc_id.id,
                'company_id': res.company_id.id,
                'lead_days': res.lead_days,
                'lead_type': res.lead_type,
                'reordering_rule': res.reordering_rule,
            }
            self.env['user.details'].sudo().create(data)
        return res


class UserMail(models.Model):
    _name = 'user.mail.data'

    user_id = fields.Many2one('res.users', string="Mail To")
    name = fields.Char(related="user_id.name", string="Name", store=True)
    location_ids = fields.One2many('user.location', 'user_mail_id')
    detail_ids = fields.One2many('user.details', 'user_mail_id', string="Detail")
    partner_id = fields.Many2one(related="user_id.partner_id", string="Partner", store=True)
    email = fields.Char(related='partner_id.email', string="email", store=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get())

    @api.multi
    def send_reorder_mail(self):
        template = self.env.ref('reordering_rule_extended.send_mail_to_user')
        assert template._name == 'mail.template'
        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.sudo().write(template_values)
        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.") % user.user_id.name)
            with self.env.cr.savepoint():
                template.with_context(lang=self.user_id.partner_id.lang).sudo().send_mail(self.id, force_send=True,
                                                                                          raise_exception=True)

    @api.multi
    def get_name_list(self):
        """
        Get Name List
        """
        name_list = []
        for location in self.location_ids:
            for details in location.detail_ids:
                name_list.append(details.action_name)
        name = set(name_list)
        return name

    @api.multi
    def get_warehouse_location(self, action_name, warehouse=False, location=False, company=False, lead=False,
                               supplier=False, source_location=False):
        """
        Get warehouse and Location
        """
        name = False
        details_ids = self.env['user.details'].search([('action_name', '=', action_name)], limit=1)
        if details_ids:
            if warehouse:
                name = details_ids.warehouse_id.name
            if location:
                name = details_ids.stock_loc_id.display_name
            if company:
                name = details_ids.company_id.name
            if lead:
                if details_ids.lead_type == 'net':
                    name = str(details_ids.lead_days) + ' ' + 'Day(s) to get the products'
                if details_ids.lead_type == 'supplier':
                    name = str(details_ids.lead_days) + ' ' + 'Day(s) to purchase'
            if supplier:
                name = details_ids.supplier_id.name
            if source_location:
                name = details_ids.source_loc_id.display_name
        return name

    @api.multi
    def get_data_value_details(self, action_name):
        """
        Get Data Value Details
        """
        details_ids = []
        for location in self.location_ids:
            for details in location.detail_ids:
                if details.action_name == action_name:
                    details_ids.append(details.id)
        object_ids = self.env['user.details'].browse(details_ids)
        return object_ids


class UserLocation(models.Model):
    _name = 'user.location'

    name = fields.Char(related="location_id.name", store=True)
    user_mail_id = fields.Many2one('user.mail.data', string="User")
    location_id = fields.Many2one('stock.location', string="Location")
    detail_ids = fields.One2many('user.details', 'user_loc_id', string="Details")


class UserDetail(models.Model):
    _name = 'user.details'

    @api.depends('product_id', 'action_name', 'product_qty')
    def get_name_detail(self):
        for rec in self:
            name = ""
            if rec.product_id.default_code:
                name += "[" + rec.product_id.default_code + "]"
            name += rec.product_id.name + " - " + str(rec.product_qty) + " QTY - " + rec.action_name + " Created"
            rec.name = name

    name = fields.Char(string="Name", compute="get_name_detail")
    user_mail_id = fields.Many2one('user.mail.data', string="User")
    user_loc_id = fields.Many2one('user.location', string="Location")
    product_id = fields.Many2one('product.product', string="Product")
    action_name = fields.Char(string="Action")
    minimum_qty = fields.Float(string="Min Qty")
    maximum_qty = fields.Float(string="Max Qty")
    current_qty = fields.Float(string="Current Qty")
    product_qty = fields.Float(string="Product Qty")
    supplier_id = fields.Many2one('res.partner', string="Supplier", domain="[('supplier', '=', True)]")
    source_loc_id = fields.Many2one('stock.location', 'Source Location', domain=[('usage', '=', 'internal')])
    stock_loc_id = fields.Many2one('stock.location')
    warehouse_id = fields.Many2one('stock.warehouse')
    reordering_rule = fields.Char('Reordering Rule')
    company_id = fields.Many2one('res.company', 'Company')
    lead_days = fields.Integer('Lead Time')
    lead_type = fields.Selection([
        ('net', 'Day(s) to get the products'),
        ('supplier', 'Day(s) to purchase')
    ], 'Lead Type')
