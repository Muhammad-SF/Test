from odoo import models, fields, api, exceptions, _


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if vals.get('company_type', False) == 'company':
            vals_name = " ".join(vals.get('name').split())
            partner_rec = self.search([('name', 'ilike', vals_name)])
            for partner in partner_rec:
                partner_name = " ".join(partner.name.split())
                if partner_name.lower() == vals_name.lower():
                    raise exceptions.Warning(_('You are not allowed to create duplicate Name!'))
        result = super(Partner, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        if  vals.get('company_type', False) == 'person':
            return super(Partner, self).write(vals)
        if vals.get('name', False):
            vals_name = " ".join(vals.get('name').split())
            partner_rec = self.search([('name', 'ilike', vals_name),
                                       ('company_type', '=', 'company')])
            for partner in partner_rec:
                partner_name = " ".join(partner.name.split())
                if partner_name.lower() == vals_name.lower():
                    raise exceptions.Warning(_('You are not allowed to create duplicate Name!'))
        return super(Partner, self).write(vals)