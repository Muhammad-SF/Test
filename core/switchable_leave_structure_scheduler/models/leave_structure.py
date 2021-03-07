from odoo import api, fields, models, _
from datetime import datetime, timedelta
import time
from datetime import date

class LeaveStructureSwitchable(models.Model):
    _inherit = 'holiday.group.config'

    switchable = fields.Boolean('Switchable') 
    interval_number = fields.Integer('Interval Number') 
    interval_unit = fields.Selection([
        ('years','Years of Position Period'),
        ('months','Months of Position Period'),
        ('days','Days of Position Period'),
        ('years1','Years of Services in Company'),
        ('months1','Months of Services in Company'),
        ('days1','Days of Services in Company')],'Interval Unit')
    change_to = fields.Many2one('holiday.group.config',string='Change To')

    def leave_structure_switchable_function(self):
        employees = self.env['hr.employee'].search([])
        fmt = '%Y-%m-%d'
        for employee in employees:
            if employee.leave_config_id.switchable == True:
                if employee.leave_config_id.interval_unit == 'years':
                    if employee.years_of_service >= employee.leave_config_id.interval_number:
                        employee.leave_config_id = employee.leave_config_id.change_to.id
                        employee.leave_all_bool = False
                        holidays = self.env['hr.holidays'].search([('employee_id','=',employee.id)])
                        for holiday in holidays:
                            holiday.state = 'cancel'
                            holiday.unlink()

                elif employee.leave_config_id.interval_unit == 'months':
                    months = employee.months + employee.years_of_service * 12
                    if months >= employee.leave_config_id.interval_number:
                        employee.leave_config_id = employee.leave_config_id.change_to.id
                        employee.leave_all_bool = False
                        holidays = self.env['hr.holidays'].search([('employee_id','=',employee.id)])
                        for holiday in holidays:
                            holiday.state = 'cancel'
                            holiday.unlink()
                elif employee.leave_config_id.interval_unit == 'days':
                    d1 = datetime.strptime(employee.join_date, fmt)
                    d2 = datetime.strptime(str(date.today()), fmt)
                    days = (d2-d1).days
                    if days >= employee.leave_config_id.interval_number:
                        employee.leave_config_id = employee.leave_config_id.change_to.id
                        employee.leave_all_bool = False
                        holidays = self.env['hr.holidays'].search([('employee_id','=',employee.id)])
                        for holiday in holidays:
                            holiday.state = 'cancel'
                            holiday.unlink()

                elif employee.leave_config_id.interval_unit == 'years1':
                    if employee.years_of_service1 >= employee.leave_config_id.interval_number:
                        employee.leave_config_id = employee.leave_config_id.change_to.id
                        employee.leave_all_bool = False
                        holidays = self.env['hr.holidays'].search([('employee_id','=',employee.id)])
                        for holiday in holidays:
                            holiday.state = 'cancel'
                            holiday.unlink()

                elif employee.leave_config_id.interval_unit == 'months1':
                    months = employee.months1 + employee.years_of_service1 * 12
                    if months >= employee.leave_config_id.interval_number:
                        employee.leave_config_id = employee.leave_config_id.change_to.id
                        employee.leave_all_bool = False
                        holidays = self.env['hr.holidays'].search([('employee_id','=',employee.id)])
                        for holiday in holidays:
                            holiday.state = 'cancel'
                            holiday.unlink()

                elif employee.leave_config_id.interval_unit == 'days1':
                    d1 = datetime.strptime(employee.first_contract_date, fmt)
                    d2 = datetime.strptime(str(date.today()), fmt)
                    days = (d2-d1).days
                    if days >= employee.leave_config_id.interval_number:
                        employee.leave_config_id = employee.leave_config_id.change_to.id
                        employee.leave_all_bool = False
                        holidays = self.env['hr.holidays'].search([('employee_id','=',employee.id)])
                        for holiday in holidays:
                            holiday.state = 'cancel'
                            holiday.unlink()                       