from odoo import api, fields, models, _

class product(models.Model):
    _inherit = 'product.template'

    is_efaktur_exported = fields.Boolean("Is eFaktur Exported",  )
    date_efaktur_exported = fields.Datetime("eFaktur Exported Date", required=False)
