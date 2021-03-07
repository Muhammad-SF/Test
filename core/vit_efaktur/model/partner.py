from odoo import api, fields, models, _
from odoo.exceptions import UserError

class partner(models.Model):
    _inherit = 'res.partner'


    is_efaktur_exported = fields.Boolean("Is eFaktur Exported")
    date_efaktur_exported = fields.Datetime("eFaktur Exported Date", required=False)

    npwp = fields.Char("NPWP", required=False)
    blok = fields.Char("Blok", required=False)
    nomor = fields.Char("Nomor", required=False)
    rt = fields.Char("RT", required=False)
    rw = fields.Char("RW", required=False)
    alamat_lengkap = fields.Char("Alamat", required=False)

