# -*- coding: utf-8 -*-
from odoo import http

# class WorkingScheduleCalendar(http.Controller):
#     @http.route('/working_schedule_calendar/working_schedule_calendar/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/working_schedule_calendar/working_schedule_calendar/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('working_schedule_calendar.listing', {
#             'root': '/working_schedule_calendar/working_schedule_calendar',
#             'objects': http.request.env['working_schedule_calendar.working_schedule_calendar'].search([]),
#         })

#     @http.route('/working_schedule_calendar/working_schedule_calendar/objects/<model("working_schedule_calendar.working_schedule_calendar"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('working_schedule_calendar.object', {
#             'object': obj
#         })