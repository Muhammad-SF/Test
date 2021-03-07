# -*- coding: utf-8 -*-
from odoo import http

# class StableHrTimesheetInvoice(http.Controller):
#     @http.route('/stable_hr_timesheet_invoice/stable_hr_timesheet_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stable_hr_timesheet_invoice/stable_hr_timesheet_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stable_hr_timesheet_invoice.listing', {
#             'root': '/stable_hr_timesheet_invoice/stable_hr_timesheet_invoice',
#             'objects': http.request.env['stable_hr_timesheet_invoice.stable_hr_timesheet_invoice'].search([]),
#         })

#     @http.route('/stable_hr_timesheet_invoice/stable_hr_timesheet_invoice/objects/<model("stable_hr_timesheet_invoice.stable_hr_timesheet_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stable_hr_timesheet_invoice.object', {
#             'object': obj
#         })