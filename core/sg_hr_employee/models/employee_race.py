# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _


class EmployeeRace(models.Model):
    _name = 'employee.race'
    _description = 'Employee Race'

    name = fields.Char(
        string='Employee Race', size=64, help='Employee Race Name.',
        required=True, )

EmployeeRace()
