# coding=utf-8
from odoo import api, fields, models, _

class ResPartnerModifications(models.Model):
    _inherit = "res.partner"

    default_payment_journal = fields.Many2one('account.journal', string='Payment Journal', help="Need to provide Account Journal for Purchase Direct. ")