# -*- coding: utf-8 -*-
from odoo import http

# class StableAccountAnalyticAnalysis(http.Controller):
#     @http.route('/stable_account_analytic_analysis/stable_account_analytic_analysis/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stable_account_analytic_analysis/stable_account_analytic_analysis/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stable_account_analytic_analysis.listing', {
#             'root': '/stable_account_analytic_analysis/stable_account_analytic_analysis',
#             'objects': http.request.env['stable_account_analytic_analysis.stable_account_analytic_analysis'].search([]),
#         })

#     @http.route('/stable_account_analytic_analysis/stable_account_analytic_analysis/objects/<model("stable_account_analytic_analysis.stable_account_analytic_analysis"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stable_account_analytic_analysis.object', {
#             'object': obj
#         })