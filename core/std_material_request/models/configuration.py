
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MRApprovalMatrix(models.Model):
    _name = 'mr.approval.matrix'
    _description = 'Material usage approval matrix'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string="Name", required=True, track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse", required=True, track_visibility='onchange')
    location_ids = fields.Many2many('stock.location', string='Locations', track_visibility='onchange')
    std_mat_req_destlocid = fields.Many2one('stock.location',string="Destination location", track_visibility='onchange')
    product = fields.One2many(comodel_name="mr.approval.matrix.line", inverse_name="matrix_id", string="Product")
    level = fields.Integer(string='Level', compute='_get_product_line', store=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id, track_visibility='onchange')
    branch_id = fields.Many2one('res.branch', string='Branch', default=lambda self: self.env.user.branch_id.id, track_visibility='onchange')

    @api.depends('product')
    def _get_product_line(self):
        for record in self:
            if record.product:
                record.level = len(record.product)
            else:
                record.level = 0

    @api.constrains('location_ids')
    def check_location_ids(self):
        for record in self:
            all_location_ids = []
            for location in record.location_ids:
                location_ids = self.search([('location_ids', 'in', location.ids)])
                if len(location_ids) > 1:
                    all_location_ids.append(location.name_get()[0][1])
            if all_location_ids:
                join_location_name = ', '.join(all_location_ids)
                raise ValidationError('Location %s can be used only one time in approval matrix.'%(join_location_name))

    @api.onchange('warehouse_id')
    def onchange_warehouse(self):
        """
        Make warehouse compatible with company
        """
        location_ids = []
        if self.warehouse_id:
            location_obj = self.env['stock.location']
            store_location_id = self.warehouse_id.view_location_id.id
            addtional_ids = location_obj.search([('location_id', 'child_of', store_location_id), ('usage', '=', 'internal')])
            for location in addtional_ids:
                if location.location_id.id not in addtional_ids.ids:
                    location_ids.append(location.id)
            self.location_ids = [(6, 0, location_ids)]
        else:
            self.location_ids = [(6, 0, [])]

class MRApprovalMatrixLine(models.Model):
    _name = 'mr.approval.matrix.line'

    @api.model
    def default_get(self, fields):
        res = super(MRApprovalMatrixLine, self).default_get(fields)
        if self._context:
            context_keys = self._context.keys()
            next_sequence = 1
            if 'product' in context_keys:
                if len(self._context.get('product')) > 0:
                    next_sequence = len(self._context.get('product')) + 1
            res.update({'sequence': next_sequence})
        return res


    sequence = fields.Char(string="Sequence", store=True)
    approver = fields.Many2many('res.users', string="Approver", required=True)
    matrix_id = fields.Many2one('mr.approval.matrix', string="Matrix")
    approved = fields.Boolean()
    minimal_approver = fields.Float('Minimum Approver', default=1)

    @api.constrains('minimal_approver', 'approver')
    def check_minimal_approver(self):
        for record in self:
            if len(record.approver.ids) < record.minimal_approver:
                raise ValidationError('The number of approver must bigger or equal with quantity Minimum Approver.')
