# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _


class StockScrap(models.Model):
    _name = 'stock.scrap'
    _inherit = ['stock.scrap', 'mail.thread', 'ir.needaction_mixin']
    #_inherit = 'stock.scrap'

    def _get_default_scrap_location_id(self):
        return self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id

    def _get_default_location_id(self):
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

    product_id = fields.Many2one(
        'product.product', 'Product',
        required=True, states={
            'done': [('readonly', True)],
            'return': [('readonly', True)],
            'waiting_approval': [('readonly', True)],
            'approve': [('readonly', True)],
            'reject': [('readonly', True)],
        },
        track_visibility='onchange' )
    scrap_qty = fields.Float(
        'Quantity', default=1.0,
        required=True, states={
            'done': [('readonly', True)],
            'return': [('readonly', True)],
            'waiting_approval': [('readonly', True)],
            'approve': [('readonly', True)],
            'reject': [('readonly', True)],
        })
    location_id = fields.Many2one(
        'stock.location', 'Location', domain="[('usage', '=', 'internal')]",
        required=True,
        states={
            'done': [('readonly', True)],
            'return': [('readonly', True)],
            'waiting_approval': [('readonly', True)],
            'approve': [('readonly', True)],
            'reject': [('readonly', True)],
        }, default=_get_default_location_id)
    scrap_location_id = fields.Many2one(
        'stock.location', 'Scrap Location', default=_get_default_scrap_location_id,
        domain="[('scrap_location', '=', True)]",
        states={
            'done': [('readonly', True)],
            'return': [('readonly', True)],
            'waiting_approval': [('readonly', True)],
            'approve': [('readonly', True)],
            'reject': [('readonly', True)],
                })
    product_uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure',
        required=True, states={
            'done': [('readonly', True)],
            'return': [('readonly', True)],
            'waiting_approval': [('readonly', True)],
            'approve': [('readonly', True)],
            'reject': [('readonly', True)],
        })
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('done', 'Done'),
        ('reject', 'Reject'),
        ('return', 'Return'),
    ], string='Status', default="draft", track_visibility='onchange')
    user_id = fields.Many2one(
        'res.users', string='Requester',
        index=True,
        default=lambda self: self.env.user, track_visibility='onchange')
    first_approve = fields.Boolean(
        string='First Approved', help='first time approved technical field',
     copy=False)
    reason = fields.Text(string='Reject Reason', help='Reason for reject', copy=False)
    return_stock_move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Return Move', help='Return move', copy=False )
    move_id = fields.Many2one('stock.move', 'Scrap Move', readonly=True, copy=False)

    @api.multi
    def do_scrap(self):
        if self._context.get('skip_stock_move'):
            pass
        else:
            return super(StockScrap, self).do_scrap()

    def get_url(self, obj):
        url = ''
        base_url = self.env[
            'ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.model.data'].get_object_reference(
                'stock', 'menu_stock_scrap')[1]
        action_id =  self.env['ir.model.data'].get_object_reference(
            'stock', 'action_stock_scrap')[1]
        url = base_url + "/web?db="+str(self._cr.dbname)+"#id="+ str(
            obj.id) +"&view_type=form&model=stock.scrap&menu_id="+str(
                menu_id)+"&action=" + str(action_id)
        return url

    def get_scrap_matrix(self, obj):
        return self.env['scrap.matrix'].search([])

    @api.multi
    def to_approval(self):
        for obj in self:
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference(
                    'scrap_approval', 'email_template_edi_scrap_request')[1]
            except ValueError:
                template_id = False
            ctx = self._context.copy()
            url = self.get_url(obj)
            scrap_matrix_ids = self.get_scrap_matrix(obj)
            if not scrap_matrix_ids:
                raise exceptions.UserError(_("No Scrap Approval Matrix found.\
                                             Please create it."))
            for scrap_matrix in scrap_matrix_ids:
                if not scrap_matrix.scrap_line_ids:
                    raise exceptions.UserError(_("No Employee found in Scrap \
                    Matrix. Please add employee in it."))
                for line in scrap_matrix.scrap_line_ids[0]:
                    for employee in line.employee_ids:
                        if not employee.work_email:
                            raise exceptions.UserError(
                                _("Add an email to employee %s." % (employee.name)))
                        if not employee.user_id:
                            raise exceptions.UserError(
                                _("Assign user to employee %s." % (employee.name)))
                        if not self.env.user.email:
                            raise exceptions.UserError(_("Please add your email address."))
                        ctx.update({'email_to': employee.work_email,
                                    'url': url,
                                    'approval_name': employee.name,
                                    'email_from': self.env.user.email,
                                    })
                        self.env['mail.template'].browse(template_id).with_context(
                            ctx).send_mail(self.id, force_send=True)
            obj.write({'state': 'waiting_approval'})
        return True

    def get_approval_list_first(self, obj):
        """docstring for get_approval_list_first"""
        first_approval_list =[]
        name = ''
        scrap_matrix_ids = self.get_scrap_matrix(obj)
        first_approval_list.append(1)
        for matrix in scrap_matrix_ids:
            for line in matrix.scrap_line_ids[0]:
                for employee in line.employee_ids:
                    first_approval_list.append(employee.user_id.id)
                name += ', '.join(employee.name for employee in line.employee_ids)
        name += ', ' + 'Administrator'
        return first_approval_list, name

    def get_approval_list_second(self, obj):
        """docstring for get_approval_list_first"""
        second_approval_list = []
        name = ''
        second_approval_list.append(1)
        scrap_matrix_ids = self.get_scrap_matrix(obj)
        for matrix in scrap_matrix_ids:
            for line in matrix.scrap_line_ids[1]:
                for employee in line.employee_ids:
                    second_approval_list.append(employee.user_id.id)
                name += ', '.join(employee.name for employee in line.employee_ids)
        name += ', ' + 'Administrator'
        return second_approval_list, name

    @api.multi
    def action_approval(self):
        for obj in self:
            if not obj.first_approve:
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference(
                        'scrap_approval', 'email_template_edi_scrap_approve_first')[1]
                except ValueError:
                    template_id = False
                ctx = self._context.copy()
                url = self.get_url(obj)
                scrap_matrix_ids = self.get_scrap_matrix(obj)
                if not scrap_matrix_ids:
                    raise exceptions.UserError(_("No Scrap Approval Matrix found.\
                                                 Please create it."))
                for scrap_matrix in scrap_matrix_ids:
                    if not scrap_matrix.scrap_line_ids:
                        raise exceptions.UserError(_("No Employee found in Scrap \
                        Matrix. Please add employee in it."))
                    if not len(scrap_matrix.scrap_line_ids) >=2:
                        raise exceptions.UserError(_("Add second level approval"))
                    for line in scrap_matrix.scrap_line_ids[0]:
                        first_app_list, name = self.get_approval_list_first(obj)
                        if self.env.user.id not in first_app_list:
                            raise exceptions.UserError(
                                "You can not approve this request.\
                                \n Only %s employee can approve it." % (name))
                        for employee in line.employee_ids:
                            if not employee.work_email:
                                raise exceptions.UserError(
                                    _("Add an email to employee %s." % (employee.name)))
                            if not employee.user_id:
                                raise exceptions.UserError(
                                    _("Assign user to employee %s." % (employee.name)))
                        if not self.env.user.email:
                            raise exceptions.UserError(_("Please add your email address."))
                        ctx.update({'email_to': employee.work_email,
                                        'url': url,
                                        'approval_name': employee.name,
                                        'email_from': self.env.user.email,
                                        })
                        self.env['mail.template'].browse(template_id).with_context(
                                ctx).send_mail(self.id, force_send=True)
                obj.write({'state': 'waiting_approval',
                           'first_approve': True,
                           })
            else:
                ## final approval
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference(
                        'scrap_approval', 'email_template_edi_scrap_approve_final')[1]
                except ValueError:
                    template_id = False
                ctx = self._context.copy()
                url = self.get_url(obj)
                second_app_list, name = self.get_approval_list_second(obj)
                if self.env.user.id not in second_app_list:
                    raise exceptions.UserError(
                        "You can not approve this request.\
                                \n Only %s employee can approve it." % (name))
                if not self.env.user.email:
                    raise exceptions.UserError(_("Please add your email address."))
                ctx.update({
                    #'email_to': employee.work_email,
                    'email_to': obj.user_id.email,
                    'url': url,
                    #'approval_name': employee.name,
                    'email_from': self.env.user.email,
                })
                self.env['mail.template'].browse(template_id).with_context(
                    ctx).send_mail(self.id, force_send=True)
                obj.with_context(skip_stock_move=False).do_scrap()
                #obj.write({'state': 'done'})
        return True


StockScrap()
