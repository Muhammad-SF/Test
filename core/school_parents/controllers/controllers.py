# -*- coding: utf-8 -*-
from odoo import http

# class SchoolParents(http.Controller):
#     @http.route('/school_parents/school_parents/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/school_parents/school_parents/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('school_parents.listing', {
#             'root': '/school_parents/school_parents',
#             'objects': http.request.env['school_parents.school_parents'].search([]),
#         })

#     @http.route('/school_parents/school_parents/objects/<model("school_parents.school_parents"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('school_parents.object', {
#             'object': obj
#         })