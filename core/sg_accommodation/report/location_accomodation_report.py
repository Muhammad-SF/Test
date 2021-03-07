# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt.Ltd. (<http://www.serpentcs.com>).
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
from odoo import api, models
import time


class location_accommodation(models.AbstractModel):
    _name = 'report.sg_accommodation.view_location_report'

    @api.model
    def get_companies(self):
        company_list=[]
        self.td_list = []
        comp_ids=self.env['res.company'].search([('tenant', '=', True)])
        for comp in comp_ids:
            company_list.append(comp.company_code)
            if company_list:
                company_list.sort()
            no_of_td=company_list
            for td in range(0,len(no_of_td)):
                self.td_list.append(td)
        return company_list

    @api.multi
    def render_html(self, docids, data=None):
        report = self.env['report']._get_report_from_name('sg_accommodation.view_location_report')
        records = self.env['accommodation.accommodation'].browse(self.ids)
        docargs = {'doc_ids' : self.ids,
                   'doc_model' : report.model,
                   'data' : data,
                   'docs' : records,
                   'time' : time,
                   'get_companies' : self.get_companies}
        return self.env['report'].render('sg_accommodation.view_location_report', docargs)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: