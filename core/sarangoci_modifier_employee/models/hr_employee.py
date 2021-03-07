from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class hr_employee(models.Model):
    _inherit = 'hr.employee'


    # login = fields.Char(related=False, readonly=True)
    # last_login = fields.Datetime(related=False, string='Latest Connection', readonly=True)
    @api.multi
    def defaut_old_employee_id(self):
        today = fields.Date.today()
        employee_ids = self.env['hr.employee'].search([])
        count = 1
        for record in employee_ids:
            record.employee_id = today[0:4]+ today[5:7] + "{0:0>3}".format(count)
            count += 1

    @api.model
    def get_number_employee(self,date):
        employee_ids = self.env['hr.employee'].search([('employee_id','like',date[0:4])])
        if employee_ids:
            sequence = []
            for list in employee_ids.mapped('employee_id'):
                sequence.append(list[-3:])
            max_id = max(sequence)
            return date[0:4] + date[5:7] + "{0:0>3}".format((int(str(max_id)) +1))
        else:
            return date[0:4] + date[5:7] + '001'

    @api.model
    def get_employee_id(self):
        return self.get_number_employee(fields.Date.today())

    @api.onchange('join_date')
    def onchange_join_date_id(self):
        if self.join_date:
            self.employee_id = self.get_number_employee(self.join_date)

    employee_id = fields.Char('Employee ID',required=True,default=get_employee_id)
    user_id     = fields.Many2one('res.users', required=False,string='User')
    address_home_id = fields.Char('Home Address')
    join_date       = fields.Date(default=fields.Date.today())

    _sql_constraints = [
        ('unique_employee_id', 'unique (employee_id)', 'The Employee ID must be unique!')
    ]

    @api.model
    def create(self,vals):
        if not vals.get('user_id',False) and vals.get('work_email',False):
            existed_user = self.env['res.users'].search([('login','=',vals.get('work_email',False))])
            if not existed_user:
                data={
                    'name': vals.get('name',False) or '',
                    'login': vals.get('work_email',False),
                    'groups_id': [(6,0,self.env.ref('base.group_user').ids)]
                }
                user_id = self.env['res.users'].create(data)
                vals.update({'user_id':user_id.id})
            else:
                raise ValidationError(_('Your work email has been registered for other user'))
        res =super(hr_employee, self).create(vals)
        return res

    @api.multi
    def write(self,vals):
        if vals.get('work_email',False):
            existed_user = self.env['res.users'].search([('login', '=', vals.get('work_email', False))])
            if not existed_user:
                if not self.user_id:
                    data = {
                        'name': vals.get('name', False) or self.name,
                        'login': vals.get('work_email', False),
                        'groups_id': [(6, 0, self.env.ref('base.group_user').ids)]
                    }
                    user_id = self.env['res.users'].create(data)
                    self.write({'user_id': user_id.id})
                else:
                    self.user_id.write({'login':vals.get('work_email', False)})
            else:
                raise ValidationError(_('Your work email has been registered for other user'))
        res = super(hr_employee, self).write(vals)
        return res