# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import xlwt
import base64
from StringIO import StringIO


class salesperson_analysis_wizard(models.TransientModel):
    _name = 'salesperson.analysis.wizard'
    _description = 'Salesperson Analysis'

    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')

    @api.multi
    def get_salesperson_analysis_data(self):
        data_list = []
        lead_ids = self.env['crm.lead'].search([('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date), ('type','=','opportunity')])
        sales_person = list(set([x.user_id for x in lead_ids]))
        for user_id in sales_person:
            vals = {}
            vals['user_id'] = user_id.name if user_id else 'No Salesperson'
            vals['lead_count'] = len(lead_ids.filtered(lambda x: x.user_id == user_id))
            vals['meeting_count>0'] = len(lead_ids.filtered(lambda x: x.user_id == user_id and x.meeting_count > 0))
            vals['meeting_count>1'] = len(lead_ids.filtered(lambda x: x.user_id == user_id and x.meeting_count > 1))
            data_list.append(vals)
        return data_list

    @api.multi
    def action_generate_salesperson_analysis_xls(self):
        file_name = 'Salespersonanalysis.xls'
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet('Salesperson Analysis')
        salesperson_analysis = self.get_salesperson_analysis_data()

        header = xlwt.easyxf('font:bold True, name Arial;align: horiz centre;')
        substyle = xlwt.easyxf('font:bold False, name Arial;align: horiz left;')
        numberstyle = xlwt.easyxf('font:bold False, name Arial;align: horiz right;')

        worksheet.col(0).width = 9000
        worksheet.col(1).width = 8000
        worksheet.col(2).width = 8000
        worksheet.col(3).width = 8000

        worksheet.write(0, 0, 'Period $start - $end', header)
        worksheet.write(0, 1, '# Leads', header)
        worksheet.write(0, 2, '# Meetings', header)
        worksheet.write(0, 3, '# > 1 Meetings', header)

        row = 1
        for sheet in salesperson_analysis:
            worksheet.write(row, 0, sheet['user_id'], substyle)
            worksheet.write(row, 1, sheet['lead_count'], numberstyle)
            worksheet.write(row, 2, sheet['meeting_count>0'], numberstyle)
            worksheet.write(row, 3, sheet['meeting_count>1'], numberstyle)

            row += 1
        fp = StringIO()
        workbook.save(fp)

        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_id = self.env['ir.attachment'].create({'name': file_name, 'datas_fname': file_name, 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        fp.close()

        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "self",
        }

salesperson_analysis_wizard()