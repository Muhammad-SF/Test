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
from odoo import fields, models, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import base64
import tempfile
import csv
import xlrd
from xlrd import open_workbook
from odoo.exceptions import Warning


class add_pub(models.TransientModel):

    _name = 'add.pub'

    date = fields.Date(string = 'Date', default = datetime.strftime(datetime.now(), DEFAULT_SERVER_DATE_FORMAT))
    pub_file = fields.Binary(string = 'Import PUB')
    datas_fname = fields.Char('Filename')

    @api.multi
    def add_pub(self):
        '''
        The method used to import data from pub history of csv file 
        in pub history object
        @param self : The Record Set
        @api.multi : The api of multi decorator
        @return: wizard of action in dictionary
        '''
        pub_history_obj = self.env['pub.history']
        cr, uid, context = self.env.args
        context = dict(context)
        for data in self:
            filename_str = str(data.datas_fname)
            split_file = filename_str.split('.')
            if not data.pub_file:
                raise Warning(_('Please select PUB file to proceed.'))
            if not filename_str[-4:] == ".xls":
                raise Warning(_('Select .xls file only'))
            csv_data = base64.decodestring(data.pub_file)
            temp_path = tempfile.gettempdir()
            fp = open(temp_path + '/xsl_file.xls', 'wb+')
            fp.write(csv_data)
            fp.close()
            wb = open_workbook(temp_path + '/xsl_file.xls')
            header_list = []
            for sheet in wb.sheets():
                for rownum in range(sheet.nrows):
                    header_list.append({rownum : sheet.row_values(rownum)})
            pub_vals = {}
            for dict_new in header_list[1:]:
                for key , val in dict_new.iteritems():
                    acc_brw = self.env['accommodation.accommodation'].browse(int(val[0]))
                    if acc_brw.state == 'open' or acc_brw.state == 'renewed':
                        pub_ids = pub_history_obj.search([('accommodation_id', '=', int(val[0])),
                                                          ('date', '=', data.date),
                                                          ('month', '=', str(int(val[1]))),
                                                          ('year', '=', int(val[2])),
                                                          ('pub_amount', '=', float(val[3]))])
                        if not pub_ids:
                            pub_vals = {
                                        'accommodation_id':int(val[0]),
                                        'date':data.date,
                                        'month':str(int(val[1])),
                                        'year':int(val[2]),
                                        'pub_amount':float(val[3])
                                        }
                            his_rec = pub_history_obj.create(pub_vals)
                    else:
                        continue
        return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pub.import.notification',
                'target': 'new',
                'context': context,
                }

class pub_import_notification(models.TransientModel):
    _name = 'pub.import.notification'

    @api.multi
    def get_back_wiz_action(self):
        context = self.env.context
        return {
                'name': 'add_pub',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'add.pub',
                'target': 'new',
                'context': context,
                }
