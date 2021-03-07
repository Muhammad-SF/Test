# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # @api.depends('signature')
    # def _compute_signature_image(self):
    #     if self.env.user.main_signature == 'upload_file':
    #         self.signature = self.env.user.upload_datas
    #     else:
    #         self.signature = self.env.user.signature

    signature = fields.Binary(
        string='Signature', help='Add signature.')
    confirmed_id = fields.Many2one(
        comodel_name='res.users', string='Confirmed By', help='')
    confirmed_signature = fields.Binary(
        string="Confirmed Signature")
    confirmed_date_time = fields.Datetime(
        string='Confirmed On', help='Confirmed datetime.')
    
    @api.model
    def create(self,vals):
        if self.env.user.main_signature == 'upload_file':
            vals['signature'] = self.env.user.upload_datas
        else:
            vals['signature'] = self.env.user.signature
        return super(PurchaseOrder, self).create(vals)

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if self.env.user.main_signature == 'upload_file':
            confirmed_signature = self.env.user.upload_datas
        else:
            confirmed_signature = self.env.user.signature
        self.write({'confirmed_id': self.env.user.id,
                    'confirmed_signature': confirmed_signature,
                    'confirmed_date_time': fields.Datetime.now(),
                    })
        return res


PurchaseOrder()
