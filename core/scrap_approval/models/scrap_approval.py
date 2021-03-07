# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _
from odoo.exceptions import UserError
from urlparse import urljoin


class ScrapApproval(models.Model):
    _name = 'scrap.approval'
    _description = 'Scrap Approval'
    _order = 'id desc'

    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id

    def _get_default_location_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

    name = fields.Char(
        string='Name', size=64, help='Scrap sequence name.',
        default=lambda self: _('New'),
        copy=False, readonly=True, required=True, )
    origin = fields.Char(string='Source Document')
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True, states={'done': [('readonly', True)]},
        string='Product', help='Product select for scrap.')
    tracking = fields.Selection('Product Tracking', readonly=True, related="product_id.tracking")
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot',
        states={'done': [('readonly', True)]}, domain="[('product_id', '=', product_id)]")
    package_id = fields.Many2one(
        'stock.quant.package', 'Package',
        states={'done': [('readonly', True)]})
    scrap_qty = fields.Float('Quantity', default=1.0, required=True, states={'done': [('readonly', True)]})
    product_uom_id = fields.Many2one(
                'product.uom', 'Unit of Measure',
                required=True, states={'done': [('readonly', True)]})
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('waiting_approval', 'Waiting Approval'),
                   ('approve', 'Approve'),
                   ('reject', 'Reject'),
                   ], default='draft',
        string='State', help='Various state of the Scrap Approval')
    user_id = fields.Many2one('res.users', string='Requester',
                              index=True,
                              default=lambda self: self.env.user)
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True)
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True, states={'done': [('readonly', True)]}, default=_get_default_location_id)
    scrap_location_id = fields.Many2one(
                'stock.location', 'Scrap Location', default=_get_default_scrap_location_id,
                domain="[('scrap_location', '=', True)]", states={'done': [('readonly', True)]})
    date_expected = fields.Datetime('Expected Date', default=fields.Datetime.now)
    employee_ids = fields.Many2many(
        comodel_name='hr.employee', string='Approver',
        help='Add multiple Approver', )

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('scrap.approval') or _('New')
        scrap = super(ScrapApproval, self).create(vals)
        return scrap

    @api.multi
    def action_get_stock_move(self):
        action = self.env.ref('stock.stock_move_action').read([])[0]
        action['domain'] = [('id', '=', self.move_id.id)]
        return action

    def get_url(self, obj):
        url = ''
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.model.data'].get_object_reference(
                'scrap_approval', 'menu_scrap_approval')[1]
        action_id =  self.env['ir.model.data'].get_object_reference(
            'scrap_approval','act_open_scrap_approval_view')[1]
        url = base_url + "/web?#id="+ str(
            obj.id) +"&view_type=form&model=scrap.approval&menu_id="+str(
                menu_id)+"&action=" + str(action_id)
        return url

    @api.multi
    def to_approval(self):
        for obj in self:
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference(
                    'scrap_approval', 'email_template_edi_scrap_request')[1]
            except ValueError:
                template_id = False
            ctx = self._context.copy()
           #base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
           #menu_id = self.env['ir.model.data'].get_object_reference(
           #    'scrap_approval', 'menu_scrap_approval')[1]
           #action_id =  self.env['ir.model.data'].get_object_reference(
           #    'scrap_approval','act_open_scrap_approval_view')[1]
           #url = base_url + "/web?#id="+ str(
           #    obj.id) +"&view_type=form&model=scrap.approval&menu_id="+str(
           #    menu_id)+"&action=" + str(action_id)
            url = self.get_url(obj)
            for employee in obj.employee_ids:
                if not employee.work_email:
                    raise UserError(_("Add an email to employee %s." % (employee.name)))
                if not employee.user_id:
                    raise UserError(_("Assign user to employee %s." % (employee.name)))
                ctx.update({'email_to': employee.work_email,
                            'url': url,
                            'approval_name': employee.name,
                            })
                self.env['mail.template'].browse(template_id).with_context(
                    ctx).send_mail(self.id, force_send=True)
            obj.write({'state': 'waiting_approval'})
        return True

    @api.multi
    def action_approval(self):
        for obj in self:
            print "action approval", obj
            obj.write({'state': 'approval'})
        return True

    @api.multi
    def action_reject(self):
        for obj in self:
            print "action reject", obj




ScrapApproval()
