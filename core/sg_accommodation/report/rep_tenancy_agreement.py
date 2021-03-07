# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt.Ltd. (<http://www.serpentcs.com>).
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

from odoo import api, models
import time
from datetime import datetime


class report_rep_tenancy_agreement(models.AbstractModel):
    _name = 'report.accommodation.tenancy_agreement_report'

    @api.model
    def get_partner(self, address_id):
        if address_id.parent_id:
            return address_id.parent_id.name
        else:
            return address_id.name

    @api.model
    def get_rooms(self, maximum , stay):
        diff = maximum - stay
        return diff

    @api.model
    def get_rate(self, rent, maximum , stay):
        diff = maximum - stay
        cal_rate = rent * diff
        return cal_rate

    @api.model
    def get_date(self):
        return time.strftime('%d %B %Y')

    @api.model
    def get_date_format(self, date_start):
        if date_start:
            time_val = datetime.strptime(date_start, '%Y-%m-%d') 
            time_for = datetime.strftime(time_val, '%d %B %Y') 
            return time_for
        return ''

    @api.multi
    def render_html(self, docids, data=None):
        report = self.env['report']._get_report_from_name('sg_accommodation.rep_acco_tenancy_agreement')
        records = self.env['accommodation.accommodation'].browse(self.ids)
        docargs = {'doc_ids' : self.ids,
                   'doc_model' : report.model,
                   'data' : data,
                   'docs' : records,
                   'time' : time,
                   'get_corr_add' : self.get_corr_add,
                   'get_partner' : self.get_partner,
                   'get_total' : self.get_total,
                   'get_rate' : self.get_rate,
                   'get_rooms_ids' : self.get_rooms_ids}
        return self.env['report'].render('sg_accommodation.rep_acco_tenancy_agreement', docargs)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
