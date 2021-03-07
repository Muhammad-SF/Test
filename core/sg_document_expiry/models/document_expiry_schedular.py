# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
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
import base64
import time
import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models, _
from odoo.report import render_report

class employee_immigration(models.Model):
    _inherit = 'employee.immigration'
    
    @api.model
    def get_expiry_documents(self):
        """
        It will be called from scheduler and finds the documents that 
        will be expired after 30 days.
        """
        context = dict(self._context)
        if context is None:
            context = {}
        next_date = (datetime.datetime.strptime(time.strftime('%Y-%m-%d'),
                                                '%Y-%m-%d') + \
                     relativedelta(days=30)).strftime('%Y-%m-%d')
        self._cr.execute("SELECT employee_id as employee, doc_type_id as \
            type FROM employee_immigration GROUP BY employee_id, doc_type_id")
        res = {}
        for data in self._cr.dictfetchall():
            employee_id = data['employee']
            type = data['type']
            imig_ids = self.search([('employee_id', '=', employee_id),
                                    ('doc_type_id', '=', type),
                                    ('exp_date', '=', next_date)],
                                   order='exp_date desc')
            if imig_ids and imig_ids.ids:
                if employee_id in res:
                    res[employee_id].append({'type': type,
                                             'exp_date': next_date})
                else:
                    res.update({employee_id: [{'type': type,
                                               'exp_date': next_date}]})
                res.update({'img_id':imig_ids.ids})
                self.generate_send_mail(res)
        return True

    @api.model
    def generate_send_mail(self, res):
        """
        It calls Document Expiry Report and will attache it to mail, 
        generate mail body and send it to hr manager and system admin.
        """
        data = {
             'ids': [],
             'model': 'employee.immigration',
             'form': res
        }
        datas = {
            'type': 'ir.actions.report.xml',
            'report_name': 'sg_document_expiry.document_expirey_report',
            'datas': data,
        }
        if res.has_key('img_id'):
            self._ids = res['img_id']
        mail_server_ids = self.env['ir.mail_server'].search([])
        if mail_server_ids and mail_server_ids.ids:
            mail_server_ids = mail_server_ids.ids
            attachment_ids = []
            groups = [self.env['ir.model.data'
                               ].get_object('hr', 'group_hr_manager')]
            groups += [self.env['ir.model.data'
                                ].get_object('base', 'group_system')]
            email_ids = ''
            for group in groups:
                for user in group.users:
                    email = user.email
                    if email:
                        email_ids += email + ','
            values = {
                'email_to': email_ids,
                'body_html': "Kindly find attached Document Expiry Report.",
                'subject': 'Document Expiry Report',
                'mail_server_id': mail_server_ids[0],
                'auto_delete': True,
            }
            ir_attachment = self.env['ir.attachment']
            msg_id = self.env['mail.mail'].create(values)
            domain = [('report_name', '=',
                       'sg_document_expiry.document_expirey_report')]
            matching_reports = self.env['ir.actions.report.xml'
                                        ].search(domain)
            if matching_reports and matching_reports.ids:
                report = matching_reports[0]
                result, format = render_report(self.env.cr, self.env.uid,
                                               self._ids, report.report_name,
                                               datas, {})
                result = base64.b64encode(result)
                file_name = "Document Expiry Report.pdf"
                if result:
                    attach_data = {
                        'name': file_name,
                        'datas_fname': file_name,
                        'datas': result,
                        'res_model': 'mail.mail',
                        'type': 'binary',
                        'res_id': msg_id.id,
                        }
                    attach_id = ir_attachment.create(attach_data)
                    attachment_ids.append(attach_id.id)
                if attachment_ids:
                    msg_id.write({'attachment_ids': [(6, 0, attachment_ids)]})
            msg_id.send()
#            if attachment_ids:
#                for attach in ir_attachment.browse(attachment_ids):
#                    attach.unlink()
        return True
