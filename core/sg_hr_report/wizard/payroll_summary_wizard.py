# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
from odoo import tools
from datetime import datetime
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class payroll_summary_wizard(models.TransientModel):

    _name = 'payroll.summary.wizard'

    date_from = fields.Date('Date From', default = lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date To', default = lambda *a: str(datetime.now() + relativedelta.relativedelta(months = +1, day = 1, days = -1))[:10])
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_payroll_rel', 'emp_id3', 'employee_id', 'Employee Name')

    @api.multi
    def print_order(self):
        '''
        The method used to HR Payroll Summary Report of Template called.
        @self: Record set
        @api.multi : The decorator of multi
        @return: Return action of wizard in dictionary
        -------------------------------------------------------------------------
        '''
        cr, uid, context = self.env.args
        payroll_data = self.read([])
        data = {}
        if payroll_data:
            data = payroll_data[0]
        emp_ids = data.get('employee_ids', False) or []
        date_from = data.get('date_from', False) or False
        date_to = data.get('date_to', False) or False
        res_user = self.env["res.users"].browse(uid)
        if data.has_key('date_from') and data.has_key('date_to') and data.get('date_from', False) >= data.get('date_to', False):
            raise ValidationError(_("You must be enter start date less than end date !"))
#        for employee in self.env['hr.employee'].browse(emp_ids):
#            if not employee.bank_account_id:
#                raise ValidationError(_('There is no Bank Account define for %s employee.' % (employee.name)))
#            if not employee.gender:
#                raise ValidationError(_('There is no gender define for %s employee.' % (employee.name)))
#            if not employee.birthday:
#                raise ValidationError(_('There is no birth date define for %s employee.' % (employee.name)))
#            if not employee.identification_id:
#                raise ValidationError(_('There is no identification no define for %s employee.' % (employee.name)))
#            if not employee.work_phone or not employee.work_email:
#                raise ValidationError(_('You must be configure Contact no or email for %s employee.' % (employee.name)))
        for emp in self.env['hr.employee'].browse(emp_ids):
            payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', emp.id),
                                                         ('date_from', '>=', date_from),
                                                         ('date_to', '<=', date_to),
                                                         ('state', 'in', ['draft', 'done', 'verify'])
                                                    ])
            if not payslip_ids.ids:
                raise ValidationError(_('There is no payslip details available between selected date %s and %s for the %s employee.' ) % (date_from, date_to, emp.name))
        data.update({'currency': " " + tools.ustr(res_user.company_id.currency_id.symbol), 'company': res_user.company_id.name})
        datas = {
                'ids': [],
                'form': data,
                'model':'hr.payslip',
            }
        return self.env['report'].get_action(self, 'sg_hr_report.hr_payroll_summary_report_tmp' , data = datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
