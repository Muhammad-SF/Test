from odoo import models, fields,api

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    attachment  = fields.Binary('Attachment')
    file_name   = fields.Char()