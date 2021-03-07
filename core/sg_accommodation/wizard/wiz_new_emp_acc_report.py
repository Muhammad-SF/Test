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
import time
import xlwt
import base64
from xlwt import Workbook
from StringIO import StringIO
from datetime import date, datetime
from odoo import fields, models, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, misc


class acc_report_new_emp(models.TransientModel):
    _name = 'acc.report.new.emp'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_id = fields.Many2one('res.company', 'Company Id', default = lambda self: self.env['res.company']._company_default_get('acc.report.new.emp'))

    @api.multi
    def print_report(self):
        emps = self.env['hr.employee'].search([('accommodated', '=', True), ('join_date', '>=', self.start_date), ('join_date', '<=', self.end_date)], order = 'join_date')
        month_list = []
        check_months = []
        for emp in emps:
            ctr = 1
            emp_join_date = datetime.strptime(emp.join_date, DEFAULT_SERVER_DATE_FORMAT)
            month = emp_join_date.strftime('%B-%Y')
            bed = self.env['beds.beds'].search([('employee_id', '=', emp.id)])
            if bed:
                emp_dict = {
                    'sr':ctr or '',
                    'emp_id':emp.identification_id or '',
                    'name':emp.name or '',
                    'wp_number':emp.wp_number or '',
                    'company':emp.company_id and emp.company_id.code or '',
                    'dialect':emp.dialect or '',
                    'site':emp.worker_location_id and emp.worker_location_id.name or '',
                    'app_date':emp.app_date or '',
                    'join_date':emp.join_date or '',
                    'accommodation':bed.room_id and bed.room_id.accommodation_id and bed.room_id.accommodation_id.name or '',
                    'print_emp' : True,
                    }
                ctr += 1
                if month_list:
                    check_months = [m for m, dict2 in month_list]
                    month_index_dict = dict([(m2, month_list.index((m2, dict2))) for m2, dict2 in month_list])
                if month.upper() in check_months:
                    month_list[month_index_dict[month.upper()]][1].append(emp_dict)
                else:
                    month_list.append((month.upper(), [emp_dict]))
        fl = StringIO()
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf("font: color black; align: horiz left")
        for_center_bold = xlwt.easyxf("font: bold 1, color black; align: horiz center")
        GREEN_TABLE_HEADER = xlwt.easyxf(
                 'font: bold 1, name Tahoma, height 250;'
                 'align: vertical center, horizontal center, wrap on;'
                  'borders: top double, bottom double, left double, right double;'
                 'pattern: pattern solid, pattern_fore_colour white, pattern_back_colour white'
                 )

        BLACK_MONTH_HEADER = xlwt.easyxf(
                 'font: bold 1, color white, name Tahoma, height 160;'
                 'align: vertical center, horizontal center, wrap on;'
                 'borders: left thin, right thin, top thin, bottom thin;'
                 'pattern: pattern solid, pattern_fore_colour black, pattern_back_colour black'
                 )

        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '0.00'

        worksheet.row(0).height = 320
        worksheet.col(0).width = 4000
        worksheet.col(1).width = 4000
        worksheet.col(2).width = 4000
        worksheet.col(3).width = 4000
        worksheet.col(4).width = 4000
        worksheet.col(5).width = 4000
        worksheet.col(6).width = 6000
        worksheet.col(7).width = 4000
        worksheet.col(8).width = 4000
        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.MEDIUM
        border_style = xlwt.XFStyle()  # Create Style
        border_style.borders = borders

        worksheet.write_merge(0, 0, 0, 8, 'NEW WORKERS', GREEN_TABLE_HEADER)
        worksheet.write(1, 0, 'CODE NO', for_center_bold)
        worksheet.write(1, 1, 'NAME', for_center_bold)
        worksheet.write(1, 2, 'W/P NUMBER', for_center_bold)
        worksheet.write(1, 3, 'COM', for_center_bold)
        worksheet.write(1, 4, 'DIALECT', for_center_bold)
        worksheet.write(1, 5, 'SITE', for_center_bold)
        worksheet.write(1, 6, 'DATE OF APPLICATION', for_center_bold)
        worksheet.write(1, 7, 'ARRIVAL DT', for_center_bold)
        worksheet.write(1, 8, 'ACCOM', for_center_bold)
        if month_list:
            row = 2
            col1 = 0
            col = 8
            for month, month_data in month_list:
                worksheet.write_merge(row, row, col1, col, month, BLACK_MONTH_HEADER)
                if month_data:
                    row = row + 1
                    for month_dict in month_data:
                        worksheet.write(row, 0, month_dict.get('emp_id'), for_left)
                        worksheet.write(row, 1, month_dict.get('name'), for_left)
                        worksheet.write(row, 2, month_dict.get('wp_number'), for_left)
                        worksheet.write(row, 3, month_dict.get('company'), for_left)
                        worksheet.write(row, 4, month_dict.get('dialect'), for_left)
                        worksheet.write(row, 5, month_dict.get('site'), for_left)
                        worksheet.write(row, 6, month_dict.get('app_date'), for_left)
                        worksheet.write(row, 7, month_dict.get('join_date'), for_left)
                        worksheet.write(row, 8, month_dict.get('accommodation'), for_left)
                        row = row + 1
        workbook.save(fl)
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'file': buf})
        self.env.args = cr, uid, misc.frozendict(context)
        module_rec = self.env['acc.report.new.emp.standard.export'].create({'file' : buf, 'name' : 'New Employee.xls'})
        return {
                'type': 'ir.actions.act_window',
                'res_id' : module_rec.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'acc.report.new.emp.standard.export',
                'target': 'new',
                'context': ctx}

class acc_report_new_emp_standard_export(models.TransientModel):
    _name = 'acc.report.new.emp.standard.export'

    file = fields.Binary('File')
    name = fields.Char(string = 'File Name', size = 32)

    @api.multi
    def action_back(self):
        if self._context is None:
            self._context = {}
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'acc.report.new.emp',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: