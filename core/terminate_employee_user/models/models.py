# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime

class terminate_employee_user(models.Model):
    _inherit = 'hr.employee'


    @api.multi
    def cessation_date_checker(self):
        emp=self.search([])
        for e in emp:
            d1= fields.Date.today()
            d2= e.cessation_date
            if d1 and d2:
                d1 = datetime.strptime(d1, "%Y-%m-%d")
                d2 = datetime.strptime(d2, "%Y-%m-%d")
                days=abs((d2 - d1).days)
                if days == 0:
                    v={'emp_status':'terminated'}
                    e.write(v)
                    u=self.env['res.users'].search([('id','=',e.user_id.id)])
                    u.write({'active':False})