from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

from lxml import etree
from xml.etree import ElementTree as ET
from odoo.osv import orm
from openerp.osv.orm import setup_modifiers


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    order_line_setting = fields.Selection([
        ('editable', 'Editable'),
        ('popup', 'Popup')
    ],string="Order Line Setting")
    
    show_popup = fields.Boolean(string="Show Popup")

    @api.multi
    def set_show_popup(self):
        return self.env['ir.values'].sudo().set_default('sale.config.settings', 'show_popup', self.show_popup)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        ir_values = self.env['ir.values']
        line_setting = ir_values.get_default('sale.config.settings', 'show_popup')

        group_id = False
        group_id = self.env.ref('Sales_order_line_popup.group_sale_order_line_popup')
        if line_setting:
            if group_id:
                group_id.sudo().write({'users': [(4, self.env.user.id)]})
        else:
            if group_id:
                group_id.sudo().write({'users': [(3, self.env.user.id)]})


        return super(SaleOrder, self).search(args, offset, limit, order, count=count)
