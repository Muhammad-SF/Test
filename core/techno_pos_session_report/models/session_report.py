# -*- coding: utf-8 -*-
import datetime

from odoo import fields, models, api
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from collections import Counter
import json, ast


class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_session_report = fields.Boolean(string='Session Report ')

class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_return_order = fields.Boolean(string='Return Order')

    @api.multi
    def refund(self):
        res = super(PosOrder, self).refund()
        self.env['pos.order'].search([('id', '=', res['res_id'])]).is_return_order = True
        return res

class PosSession(models.Model):
    _inherit = 'pos.session'

    def get_payment_details(self):
        orders = self.env['pos.order'].search([('session_id', '=', self.id)])
        st_line_ids = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)]).ids
        if st_line_ids:
            self.env.cr.execute("""
                SELECT aj.name, sum(amount) total
                FROM account_bank_statement_line AS absl,
                     account_bank_statement AS abs,
                     account_journal AS aj
                WHERE absl.statement_id = abs.id
                    AND abs.journal_id = aj.id
                    AND absl.id IN %s
                GROUP BY aj.name;
            """, (tuple(st_line_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []
        return payments

    def get_payment_details_qty(self, payment_method):
        qty_payment_method = 0
        if payment_method:
            orders = self.env['pos.order'].search([('session_id', '=', self.id)])
            st_line_obj = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)])
            if len(st_line_obj) > 0:
                res = []
                for line in st_line_obj:
                    res.append(line.journal_id.name)
                res_dict = ast.literal_eval(json.dumps(dict(Counter(res))))
                if payment_method in res_dict:
                    qty_payment_method = res_dict[payment_method]
        return int(qty_payment_method)

    def get_price_list_details(self):
        order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        pricelist = {}
        for order in order_ids:
            if order.pos_pricelist.name:
                if order.pos_pricelist.name in pricelist:
                    pricelist[order.pos_pricelist.name] += order.amount_total
                else:
                    pricelist.update({
                        order.pos_pricelist.name : order.amount_total
                    })
            else:
                if 'undefine' in pricelist:
                    pricelist['undefine'] += order.amount_total
                else:
                    pricelist.update({
                        'undefine': order.amount_total
                    })
        return pricelist

    def get_price_list_qty(self, price_list):
        if price_list:
            qty_pricelist = 0
            price_list_obj = self.env['pos.pricelist'].search([('name','=', str(price_list))])
            if price_list_obj:
                orders = self.env['pos.order'].search([('session_id', '=', self.id),('pos_pricelist.id','=',price_list_obj.id)])
                qty_pricelist = len(orders)
            else:
                if price_list == 'undefine':
                    orders = self.env['pos.order'].search([('session_id', '=', self.id),('pos_pricelist','=',False)])
                    qty_pricelist = len(orders)
            return int(qty_pricelist)

    def get_card_details(self):
        orders = self.env['pos.order'].search([('session_id', '=', self.id)])
        st_line_ids = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)]).ids
        if st_line_ids:
            self.env.cr.execute("""
                SELECT sum(amount) total, absl.card_id
                FROM account_bank_statement_line AS absl,
                     account_bank_statement AS abs,
                     account_journal AS aj
                WHERE absl.statement_id = abs.id
                    AND abs.journal_id = aj.id
                    AND absl.id IN %s
                GROUP BY absl.card_id;
            """, (tuple(st_line_ids),))
            payments = self.env.cr.dictfetchall()
            card_payment_id = self.env['card.payment']
            result = []
            for payment in payments:
                res = {}
                if payment:
                    if payment['card_id']:
                        card_name = card_payment_id.browse(int(payment['card_id'])).name
                        res.update({
                            'total':payment['total'],
                            'card_id':card_name
                        })
                        result.append(res)
        else:
            result = []
        return result

    def get_card_details_qty(self, card_method):
        if card_method:
            qty_card_method = 0
            orders = self.env['pos.order'].search([('session_id', '=', self.id)])
            st_line_obj = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)])
            if len(st_line_obj) > 0:
                res = []
                for line in st_line_obj:
                    res.append(line.card_id.name)
                res_dict = ast.literal_eval(json.dumps(dict(Counter(res))))
                if card_method in res_dict:
                    qty_card_method = res_dict[card_method]

            return int(qty_card_method)

    def get_session_detail(self):
        order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        discount = 0.0
        taxes = 0.0
        total_sale = 0.0
        total_gross = 0.0
        total_return = 0.0
        products_sold = {}
        for order in order_ids:
            total_sale += order.amount_total
            currency = order.session_id.currency_id
            total_gross += order.amount_total
            for line in order.lines:
                if line.product_id.pos_categ_id.name:
                    if line.product_id.pos_categ_id.name in products_sold:
                        products_sold[line.product_id.pos_categ_id.name] += line.qty
                    else:
                        products_sold.update({
                            line.product_id.pos_categ_id.name: line.qty
                        })
                else:
                    if 'undefine' in products_sold:
                        products_sold['undefine'] += line.qty
                    else:
                        products_sold.update({
                                'undefine': line.qty
                                })
                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1 - (line.discount or 0.0) / 100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes += tax.get('amount', 0)
                discount += line.discount
            if order.is_return_order:
                total_return -= order.amount_total
        return {
            'total_sale': total_sale,
            'discount': discount,
            'tax': taxes,
            'products_sold': products_sold,
            'total_gross': total_gross - taxes - discount + total_return,
            'total_return': total_return

        }

    def get_current_datetime(self):
        return fields.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def get_session_open_date(self):
        return datetime.datetime.strptime(self.start_at, DEFAULT_SERVER_DATETIME_FORMAT).date()

    def get_session_open_time(self):
        return datetime.datetime.strptime(self.start_at, DEFAULT_SERVER_DATETIME_FORMAT).strftime("%I:%M %p")
