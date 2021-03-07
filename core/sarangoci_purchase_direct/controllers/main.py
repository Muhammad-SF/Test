# -*- coding: utf-8 -*-

from odoo import http, models, fields, api, _, tools
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.website import slug
from datetime import date
from odoo.addons.purchase_direct_website.controllers.main import WebsitePurchase
import re
import logging
import json
from odoo.exceptions import UserError,ValidationError
_logger = logging.getLogger(__name__)


class WebsitePurchaseBranch(WebsitePurchase):

    @http.route(['/purchase/direct/cart'], type='http', auth="public", website=True)
    def cart(self, **post):
        purchase_direct = request.website.get_purchase_direct()
        branch_ids = request.env.user.branch_ids.ids
        values = {
            'purchase_direct': purchase_direct,
            'vendors': request.env['res.partner'].search([('is_purchase_direct', '=', True)]),
            'journals': request.env['account.journal'].search([('type', 'in', ['cash', 'bank'])]),
            'branches': request.env['stock.warehouse'].search([('branch_id','in',branch_ids)]),
            'errors': request.session.get('errors', [])
        }

        if post.get('type') == 'popover':
            # force no-cache so IE11 doesn't cache this XHR
            return request.render("purchase_direct_website.cart_popover", values, headers={'Cache-Control': 'no-cache'})

        return request.render("purchase_direct_website.cart", values)


    @http.route(['/purchase/direct/branch/update_json'], type='json', auth="public", methods=['POST'], website=True,
                csrf=False)
    def branch_update_json(self, branch_id, display=True):
        request.session['branch_id'] = branch_id
        return branch_id

    @http.route(['/purchase/direct/confirm'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        if request.env.user == request.env.ref('base.public_user'):
            return request.redirect('/web/login?redirect=/purchase/direct/cart')
        errors = []

        purchase_direct = request.website.get_purchase_direct()
        journal = request.session.get('default_payment_journal', False)
        partner = request.session.get('partner_idx', False)
        branch = request.session.get('branch_id', False)
        if str(branch) == 'Please Select Branch':
            raise Exception(_('Please Select Branch...!'))

        warehouse_id = request.env['stock.warehouse'].search([('branch_id','=',int(branch))],limit=1)
        picking_id = request.env['stock.picking.type'].search([('warehouse_id','=',warehouse_id.id),('code','=','incoming')],limit=1)
        request.session['errors'] = []
        if not partner:
            errors.append((_('Sorry, we can\'t complete your order'), _('You Need to Fill Partner first')))
        if not journal:
            errors.append((_('Sorry, we can\'t complete your order'), _('You Need to Fill Journal first')))
        if not branch:
            errors.append((_('Sorry, we can\'t complete your order'), _('You Need to Fill Branch first')))

        request.session['errors'] = errors

        if len(errors) == 0:
            lines_data = purchase_direct.get('line_ids')
            line_obj = request.env['purchase.order.line']
            request_lines = []
            purchase_direct['partner_id'] = partner
            purchase_direct['branch_id'] = branch
            purchase_direct['default_payment_journal'] = journal
            purchase_direct.update(
                request.env['purchase.order'].default_get(['company_id', 'picking_type_id']))
            purchase_direct['picking_type_id'] = picking_id.id
            purchase_direct['is_purchase_direct'] = True
            purchase_direct = request.env['purchase.order'].create(purchase_direct)
            for line_data in lines_data:
                line = line_obj.create({
                    'product_id': line_data.get('product_id'),
                    'product_uom': line_data.get('product_uom_id'),
                    'price_unit': line_data.get('price_unit'),
                    'product_qty': line_data.get('product_qty'),
                    'name': line_data.get('description') or '',
                    'order_id': purchase_direct.id,
                    'date_planned': date.today(),
                })
                request_lines.append(line.id)

            purchase_direct.button_confirm()
            del request.session['purchase_direct']
            if request.session.get('errors', False):
                del request.session['errors']
            if request.session.get('unit_price', False):
                del request.session['unit_price']
        else:
            return request.redirect('/web/login?redirect=/purchase/direct/cart')

        return request.render("purchase_direct_website.pr_created", {'purchase_direct': purchase_direct})