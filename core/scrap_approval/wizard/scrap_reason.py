# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _


class ScrapReason(models.TransientModel):
    _name = 'scrap.reason'

    reason = fields.Text(
        string='Reason for reject',
        help='Reason for reject.', required=True, )

    def get_url(self, obj):
        url = ''
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.model.data'].get_object_reference(
                'stock', 'menu_stock_scrap')[1]
        action_id = self.env['ir.model.data'].get_object_reference(
            'stock', 'action_stock_scrap')[1]
        url = base_url + "/web?db="+str(self._cr.dbname)+"#id=" + str(
            obj.id) + "&view_type=form&model=stock.scrap&menu_id=" + str(
                menu_id)+"&action=" + str(action_id)
        return url

    def get_scrap_matrix(self, obj):
        return self.env['scrap.matrix'].search([])

    def get_approval_list(self, obj):
        """docstring for get_approval_list_first"""
        approval_list =[]
        name = ''
        scrap_matrix_ids = self.get_scrap_matrix(obj)
        approval_list.append(1)
        for matrix in scrap_matrix_ids:
            for line in matrix.scrap_line_ids:
                for employee in line.employee_ids:
                    approval_list.append(employee.user_id.id)
                if name:
                    name += ', '
                name += ', '.join(employee.name for employee in line.employee_ids)
        name += ', ' + 'Administrator'
        return approval_list, name

    @api.multi
    def action_reject(self):
        """docstring for action_reject"""
        stock_scrap_obj = self.env['stock.scrap'].browse(
            self._context.get('active_id'))
        for obj in self:
            if not stock_scrap_obj:
                continue
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference(
                    'scrap_approval', 'email_template_edi_scrap_request_reject')[1]
            except ValueError:
                template_id = False
            ctx = self._context.copy()
            url = self.get_url(obj)
            app_list, name = self.get_approval_list(obj)
            if self.env.user.id not in app_list:
                raise exceptions.UserError(
                    "You can not approve this request.\
                                \n Only %s employee can reject it." % (name))
            if not self.env.user.email:
                raise exceptions.UserError(_("Please add your email address."))
            ctx.update({
                #'email_to': employee.work_email,
                'email_to': stock_scrap_obj.user_id.email,
                'url': url,
                #'approval_name': employee.name,
                'reason': obj.reason,
                'email_from': self.env.user.email,
            })
            self.env['mail.template'].browse(template_id).with_context(
                ctx).send_mail(self.id, force_send=True)
            stock_scrap_obj.write({'state': 'reject',
                                   'reason': obj.reason
                                   })
        return {'type': 'ir.actions.act_window_close'}

ScrapReason()
