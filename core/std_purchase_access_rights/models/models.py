# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    @api.model
    def create(self, vals):
        if vals.get('user_id') and self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and (self.env.user.id != vals.get('user_id')):
            raise UserError('Purchase Admin can not create/edit for other users records!')
        if vals.get('user_id') and self.user_has_groups('purchase.group_purchase_user') and not self.user_has_groups('std_purchase_access_rights.group_purchase_manager') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and not self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and (self.env.user.id != vals.get('user_id')):
            raise UserError('Purchase User can not create/edit for other users records!')
        return super(PurchaseRequisition, self).create(vals)

    @api.multi
    def write(self, vals):
        for record in self:
            user_id = vals.get('user_id', record.user_id.id)
            if user_id and self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and (self.env.user.id != user_id):
                raise UserError('Purchase Admin can not create/edit for other users records')
            if vals.get('user_id') and self.user_has_groups('purchase.group_purchase_user') and not self.user_has_groups('std_purchase_access_rights.group_purchase_manager') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and not self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and (self.env.user.id != user_id):
                raise UserError('Purchase User can not create/edit for other users records!')
        return super(PurchaseRequisition, self).write(vals)

PurchaseRequisition()

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if vals.get('create_uid') and self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and (self.env.user.id != vals.get('create_uid')):
            raise UserError('Purchase Admin can not create/edit for other users records!')
        if vals.get('user_id') and self.user_has_groups('purchase.group_purchase_user') and not self.user_has_groups('std_purchase_access_rights.group_purchase_manager') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and not self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and (self.env.user.id != vals.get('create_uid')):
            raise UserError('Purchase User can not create/edit for other users records!')
        return super(PurchaseOrder, self).create(vals)

    @api.multi
    def write(self, vals):
        for record in self:
            user_id = vals.get('create_uid', record.create_uid.id)
            if user_id and self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and (self.env.user.id != user_id):
                raise UserError('Purchase Admin can not create/edit for other users records!')
            if vals.get('user_id') and self.user_has_groups('purchase.group_purchase_user') and not self.user_has_groups('std_purchase_access_rights.group_purchase_manager') and not self.user_has_groups('std_purchase_access_rights.group_purchase_executive') and not self.user_has_groups('std_purchase_access_rights.group_purchase_admin') and (self.env.user.id != user_id):
                raise UserError('Purchase User can not create/edit for other users records!')
        return super(PurchaseOrder, self).write(vals)

PurchaseOrder()