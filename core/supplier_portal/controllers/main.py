# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _,SUPERUSER_ID
from odoo.exceptions import AccessError,Warning,ValidationError
from odoo.http import request
import base64
from odoo.addons.website_portal.controllers.main import website_account


class website_account(website_account):
    #Show count of RFQ,PO,DO,Invoice
    # @http.route()
    # def account(self, **kw):
    #     """ Add sales documents to main account page """
    #     response = super(website_account, self).account(**kw)
    #     partner = request.env.user.partner_id
    #
    #     rfq     = request.env['purchase.order']
    #     do      = request.env['stock.picking']
    #     Invoice = request.env['account.invoice']
    #     rfq_count = rfq.search_count([
    #         ('state', 'in', ('draft', 'sent', 'bid', 'cancel', 'confirmed', 'to approve')),
    #         ('partner_id','=',partner.id)
    #     ])
    #     po_count = rfq.search_count([
    #         ('state', 'not in', ('draft', 'sent', 'bid', 'confirmed', 'to approve')),
    #         ('partner_id', '=', partner.id)
    #     ])
    #     do_count = do.search_count([
    #         ('partner_id', '=', partner.id)
    #     ])
    #     invoice_count = Invoice.search_count([
    #         ('type', 'in', ['out_invoice', 'out_refund']),
    #         ('state', 'in', ['open', 'paid', 'cancel']),
    #         ('partner_id', '=', partner.id)
    #     ])
    #
    #     response.qcontext.update({
    #         'rfq_count'     : rfq_count,
    #         'order_count'   : po_count,
    #         'do_count'      :do_count,
    #         'invoice_count' : invoice_count,
    #     })
    #     return response

    #
    # Quotations and Sale Orders
    #
    #show List View of RFQ
    @http.route(['/my/rfq', '/my/rfq/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_rfq(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        rfq = request.env['purchase.order']

        domain = [
            ('state', 'in', ('draft', 'sent', 'bid', 'cancel', 'confirmed', 'to approve')),
            ('partner_id', '=', partner.id)
        ]

        archive_groups = self._get_archive_groups('purchase.order', domain)

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        rfq_count = rfq.search_count(domain)
        # make pager
        pager = request.website.pager(
            url="/my/rfq",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=rfq_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = rfq.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'quotations': quotations,
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/rfq',
        })
        return request.render("supplier_portal.portal_my_quotations", values)

    #show List View of PO
    @http.route(['/my/purchase', '/my/purchase/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PurchaseOrder = request.env['purchase.order']

        domain = [
            ('state', 'not in', ('draft', 'sent', 'bid', 'confirmed', 'to approve')),
            ('partner_id', '=', partner.id)
        ]
        archive_groups = self._get_archive_groups('purchase.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = PurchaseOrder.search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = PurchaseOrder.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/purchase',
        })
        return request.render("supplier_portal.portal_my_purchase", values)

    #show RFQ or PO form
    @http.route(['/my/purchase/<int:order>'], type='http', auth="user", website=True)
    def orders_followup(self, order=None, **kw):
        order = request.env['purchase.order'].browse([order])
        state = 'purchase'
        if order.state in ('draft', 'sent', 'bid', 'cancel', 'confirmed', 'to approve'):
            state = 'rfq'
        try:
            order.check_access_rights('read')
            order.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        order_sudo = order.sudo()

        return request.render("supplier_portal.orders_followup", {
            'order': order_sudo,
            'user_id': request.env.user,
            'state' : state,
        })

    #show List View of DO
    @http.route(['/my/delivery', '/my/delivery/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_do(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Picking = request.env['stock.picking']

        domain = [
            ('partner_id', '=', partner.id)
        ]
        archive_groups = self._get_archive_groups('stock.picking', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = Picking.search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = Picking.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'delivery',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/delivery',
        })
        return request.render("supplier_portal.portal_my_delivery", values)

    #show DO form
    @http.route(['/my/delivery/<int:order>'], type='http', auth="user", website=True)
    def delivery_order_form(self, order=None, **kw):
        order = request.env['stock.picking'].browse([order])
        try:
            order.check_access_rights('read')
            order.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        order_sudo = order.sudo()

        return request.render("supplier_portal.delivery_order_form", {
            'order': order_sudo,
            'user_id': request.env.user
        })

    #
    # Invoices
    #
    #List View of Invoice
    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        AccountInvoice = request.env['account.invoice']

        domain = [
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['open', 'paid', 'cancel'])
        ]
        archive_groups = self._get_archive_groups('account.invoice', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        invoice_count = AccountInvoice.search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        invoices = AccountInvoice.search(domain, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'date': date_begin,
            'invoices': invoices,
            'page_name': 'invoice',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/invoices',
        })
        return request.render("supplier_portal.portal_my_invoices", values)

    #download pdf Invoice
    @http.route(['/my/invoices/pdf/<int:invoice_id>'], type='http', auth="user", website=True)
    def portal_get_invoice(self, invoice_id=None, **kw):
        invoice = request.env['account.invoice'].browse([invoice_id])
        try:
            invoice.check_access_rights('read')
            invoice.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        pdf = request.env['report'].sudo().get_pdf([invoice_id], 'account.report_invoice')
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename=Invoice.pdf;')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    # @http.route(['/my/rfq/<int:order>/edit'], type='http', auth="user", website=True)
    # def edit_price(self, order=None, **kw):
    #     order = request.env['purchase.order'].browse([order])
    #     try:
    #         order.check_access_rights('read')
    #         order.check_access_rule('read')
    #     except AccessError:
    #         return request.render("website.403")
    #
    #     order_sudo = order.sudo()
    #
    #     return request.render("supplier_portal.orders_followup", {
    #         'order': order_sudo,
    #         'user_id': request.env.user
    #     })

    @http.route('/my/rfq/<int:order>/edit', type='http', methods=['POST'], auth="public", website=True, csrf=False)
    def test_path(self,order, **kw):
        order = request.env['purchase.order'].browse([order])
        try:
            order.check_access_rights('read')
            order.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        order_sudo = order.sudo()
        if kw.get('file',False):
            order.write({'attachment':base64.encodestring(kw.get('file',False).read())})
            order.write({'file_name':kw.get('file',False).filename})
        for line in order_sudo.order_line:
            if kw.get(str(line.id)+'price',False):
                line.write({'price_unit':kw.get(str(line.id)+'price',False)})
            if kw.get(str(line.id) + 'qty', False):
                line.write({'product_qty': kw.get(str(line.id)+ 'qty', False)})
        return request.render("supplier_portal.orders_followup", {
            'order': order_sudo,
            'user_id': request.env.user,
            'state' : 'rfq'
        })

    def details_form_validate(self, data):
        error, error_message = super(website_account, self).details_form_validate(data)
        # prevent VAT/name change if invoices exist
        partner = request.env['res.users'].browse(request.uid).partner_id
        invoices = request.env['account.invoice'].sudo().search_count([('partner_id', '=', partner.id), ('state', 'not in', ['draft', 'cancel'])])
        if invoices:
            if 'vat' in data and (data['vat'] or False) != (partner.vat or False):
                error['vat'] = 'error'
                error_message.append(_('Changing VAT number is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'name' in data and (data['name'] or False) != (partner.name or False):
                error['name'] = 'error'
                error_message.append(_('Changing your name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
        return error, error_message

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def account(self, **kw):
        if request._uid == SUPERUSER_ID or (request.env.user and request.env.user.has_group('base.group_portal')):
            values = self._prepare_portal_layout_values()
            # response = super(website_account, self).account(**kw)
            partner = request.env.user.partner_id

            rfq = request.env['purchase.order']
            do = request.env['stock.picking']
            Invoice = request.env['account.invoice']
            rfq_count = rfq.search_count([
                ('state', 'in', ('draft', 'sent', 'bid', 'cancel', 'confirmed', 'to approve')),
                ('partner_id', '=', partner.id)
            ])
            po_count = rfq.search_count([
                ('state', 'not in', ('draft', 'sent', 'bid', 'confirmed', 'to approve')),
                ('partner_id', '=', partner.id)
            ])
            do_count = do.search_count([
                ('partner_id', '=', partner.id)
            ])
            invoice_count = Invoice.search_count([
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'in', ['open', 'paid', 'cancel']),
                ('partner_id', '=', partner.id)
            ])

            values.update({
                'rfq_count': rfq_count,
                'order_count': po_count,
                'do_count': do_count,
                'invoice_count': invoice_count,
            })
            return request.render("website_portal.portal_my_home", values)
        else:
            raise ValidationError(_('The User dont have access for this'))