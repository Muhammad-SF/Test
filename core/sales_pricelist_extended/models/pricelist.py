# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    is_approving_matrix = fields.Boolean(string='Approving Matrix Pricelist',default=False)

    @api.multi
    def set_default_is_approving_matrix_fields(self):
        self.env['ir.values'].sudo().set_default('sale.config.settings', 'is_approving_matrix',self.is_approving_matrix)
        return True

    @api.multi
    def get_default_is_approving_matrix_fields(self, fields):
        is_approving_matrix = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_approving_matrix')
        return {
            'is_approving_matrix': is_approving_matrix,
        }


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    branch = fields.Many2one('res.branch',string='Branch')
    # partner_id = fields.Many2one('res.partner', string='Customer',domain=[('customer', '=', True)])
    location = fields.Char(string="Location")
    approving_matrix_pricelist_id = fields.Many2one('approving.matrix.pricelist',string='Approving Matrix')
    is_approving = fields.Boolean(compute='compute_is_approving',string='Is Setting Approver',default=False)
    is_user_approver = fields.Boolean(compute='compute_is_user_approver',string='Is User Approver',default=False)
    state = fields.Selection([('draft','Draft'),('request_for_approval','Request For Approval'),('waiting_for_approval','Waiting For Approval'),('approved','Approved'),('confirmed','Confirmed'),('rejected','Rejected')],string="State", default='draft')
    pricelist_approving_matrix_ids = fields.One2many('pricelist.approving.matrix', 'pricelist_id', string='Price Approving Matrix')
    is_approved = fields.Boolean('Is Approved',default= False)

    @api.model
    def default_get(self, field_list):
        result = super(ProductPricelist, self).default_get(field_list)
        if self.env['ir.values'].get_default('sale.config.settings', 'is_approving_matrix'):
            result['is_approving'] = True
        else:
            result['is_approving'] = False
        return result

    # @api.onchange('company_id')
    # def onchange_company_id(self):
    #     for record in self:
    #         # if record.company_id.branch_id:
    #         #     record.branch_id = record.company_id.branch_id
    #         if record.company_id.partner_id:
    #             record.partner_id = record.company_id.partner_id

    @api.multi
    def compute_is_approving(self):
        if self.env['ir.values'].get_default('sale.config.settings', 'is_approving_matrix'):
            self.is_approving = True
        else:
            self.is_approving = False

    @api.onchange('approving_matrix_pricelist_id','approving_matrix_pricelist_id.approving_matrix_prielist_ids',
                  'approving_matrix_pricelist_id.approving_matrix_prielist_ids.approver_ids','approving_matrix_pricelist_id.approving_matrix_prielist_ids.mim_approver')
    def _onchange_approving_matrix_pricelist_id(self):
        for record in self:
            if record.approving_matrix_pricelist_id and record.approving_matrix_pricelist_id.approving_matrix_prielist_ids:
                linelist = []
                for line in record.approving_matrix_pricelist_id.approving_matrix_prielist_ids:
                    vals = {}
                    vals['approver_ids'] = [(6,0,line.approver_ids.ids)]
                    vals['mim_approver'] = line.mim_approver
                    vals['matrix_line_id'] = line.id
                    linelist.append((0,0,vals))
                record.pricelist_approving_matrix_ids = linelist

    @api.depends('approving_matrix_pricelist_id','approving_matrix_pricelist_id.approving_matrix_prielist_ids','approving_matrix_pricelist_id.approving_matrix_prielist_ids.approver_ids')
    @api.multi
    def compute_is_user_approver(self):
        for record in self:
            if record.approving_matrix_pricelist_id and record.approving_matrix_pricelist_id.approving_matrix_prielist_ids:
                for line in record.pricelist_approving_matrix_ids:
                    if line.approver_ids:
                        for user in line.approver_ids:
                            print"com be self.is_approved ", self.is_approved
                            if self.env.user.id == user.id and self.is_approved == False:
                                print"after self.is_approved ", self.is_approved
                                self.is_user_approver = True

    @api.multi
    def action_request_for_approval(self):
        for record in self:
            if not record.is_approving:
                record.state = 'confirmed'
            elif record.approving_matrix_pricelist_id and record.approving_matrix_pricelist_id.approving_matrix_prielist_ids:
                linelist = []
                for line in record.approving_matrix_pricelist_id.approving_matrix_prielist_ids:
                    exitings_id = self.env['pricelist.approving.matrix'].search([('matrix_line_id', '=', line.id)])
                    if exitings_id:
                        for exit in exitings_id:
                            if line.approver_ids:
                                exit.approver_ids = [(6, 0, line.approver_ids.ids)]
                            exit.mim_approver = line.mim_approver
                record.pricelist_approving_matrix_ids = linelist
                record.state = 'request_for_approval'
            else:
                record.state = 'request_for_approval'

    @api.multi
    def action_approve(self):
        for record in self:
            if record.is_approving == True and record.pricelist_approving_matrix_ids:
                remaining_approver = 0
                total_approver = 0
                for line in record.pricelist_approving_matrix_ids:
                    for user in line.approver_ids:
                        if self.env.user.id == user.id:
                            print"before self.is_approved ",self.is_approved
                            self.is_approved = True
                            print"after self.is_approved ", self.is_approved
                            # line.write({'approved_by_ids': [(4, [user.partner_id.id,])]})
                            line.write({'approved': len(line.approved_by_ids)})
                            remaining_approver += line.approved
                            total_approver += line.mim_approver
                print"remaining_approver ",remaining_approver
                print"total ", total_approver
                if total_approver == 0  or remaining_approver ==  total_approver:
                    record.state = 'approved'
                elif remaining_approver !=  total_approver:
                    record.state = 'waiting_for_approval'
                else:
                    record.state = 'request_for_approval'
            else:
                record.state = 'approved'


    @api.multi
    def action_reject(self):
        for record in self:
            record.state = 'rejected'

    @api.multi
    def action_set_to_draft(self):
        for record in self:
            record.state = 'draft'

ProductPricelist()


class ApprovingMatrixPricelist(models.Model):
    _name = 'approving.matrix.pricelist'

    name = fields.Char('Name')
    approving_matrix_prielist_ids = fields.One2many('approving.matrix.pricelist.line','approving_matrix_pricelist_id',string='Approving Matrix Line')

ApprovingMatrixPricelist()

class ApprovingMatrixPricelistLine(models.Model):
    _name = 'approving.matrix.pricelist.line'

    approver_ids = fields.Many2many('res.users',string='Approver')
    mim_approver = fields.Integer(string='Minimum Approver',default=0)
    approving_matrix_pricelist_id = fields.Many2one('approving.matrix.pricelist', string='Approving Matrix Line')

ApprovingMatrixPricelistLine()

class PricelistApprovingMatrix(models.Model):
    _name = 'pricelist.approving.matrix'

    approver_ids = fields.Many2many('res.users',string='Approver')
    mim_approver = fields.Integer(string='Minimum Approver',default=0)
    approved_by_ids = fields.Many2many('res.partner',string='Approved By')
    approved =  fields.Integer(string='Approved',default=0)
    pricelist_id = fields.Many2one('product.pricelist', string='Approving Matrix Line')
    matrix_line_id = fields.Many2one('approving.matrix.pricelist.line',string='Matrix Line Id')

PricelistApprovingMatrix()


class Partner_ext(models.Model):
    _inherit = 'res.partner'

    property_product_pricelist = fields.Many2one('product.pricelist', 'Sale Pricelist')


class SaleOrder_ext(models.Model):
    _inherit = "sale.order"


    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
