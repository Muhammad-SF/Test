# -*- coding: utf-8 -*-
from odoo import http

# class SurveyExtended(http.Controller):
#     @http.route('/survey_extended/survey_extended/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/survey_extended/survey_extended/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('survey_extended.listing', {
#             'root': '/survey_extended/survey_extended',
#             'objects': http.request.env['survey_extended.survey_extended'].search([]),
#         })

#     @http.route('/survey_extended/survey_extended/objects/<model("survey_extended.survey_extended"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('survey_extended.object', {
#             'object': obj
#         })