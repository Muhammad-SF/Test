# -*- coding: utf-8 -*-
from odoo import http

# class SixcapRemoveUnsubscribeLink(http.Controller):
#     @http.route('/sixcap_remove_unsubscribe_link/sixcap_remove_unsubscribe_link/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sixcap_remove_unsubscribe_link/sixcap_remove_unsubscribe_link/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sixcap_remove_unsubscribe_link.listing', {
#             'root': '/sixcap_remove_unsubscribe_link/sixcap_remove_unsubscribe_link',
#             'objects': http.request.env['sixcap_remove_unsubscribe_link.sixcap_remove_unsubscribe_link'].search([]),
#         })

#     @http.route('/sixcap_remove_unsubscribe_link/sixcap_remove_unsubscribe_link/objects/<model("sixcap_remove_unsubscribe_link.sixcap_remove_unsubscribe_link"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sixcap_remove_unsubscribe_link.object', {
#             'object': obj
#         })