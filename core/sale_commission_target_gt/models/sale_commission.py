# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#    #378401
##############################################################################

from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import tools

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        sale_team = self.env['crm.team'].search([])
        for team in sale_team:
            for member in team.member_ids:
                if member.id == self._context.get('uid'):
                    vals.update({'team_id': team.id})
        vals.update({'user_id': self._context.get('uid')})
        res = super(SaleOrder, self).create(vals)
        return res
    
    target_group_id = fields.Many2one('target.group', string='Commission Group')

    @api.depends('amount_untaxed', 'target_group_id', 'user_id', 'team_id')
    def _compute_commission(self):
        for line in self:
            price_subtotal = 0.00
            target_lines_ids = self.env['target.lines'].search(
                [('target_group_id', '=', line.target_group_id.id), ('min_target', '<=', line.amount_untaxed),
                 ('max_target', '>=', line.amount_untaxed)], limit=1)
            if line.team_id and line.team_id.target_group_id:
                team_target_lines_ids = self.env['target.lines'].search(
                    [('target_group_id', '=', line.team_id.target_group_id.id),
                     ('min_target', '<=', line.amount_untaxed),
                     ('max_target', '>=', line.amount_untaxed)], limit=1)
                if team_target_lines_ids and line.team_id.target_group_id.commission_type == 'amount':
                    price_subtotal = line.amount_untaxed - team_target_lines_ids.amount
                elif team_target_lines_ids and line.team_id.target_group_id.commission_type == 'percentage':
                    price_subtotal = line.amount_untaxed * ((team_target_lines_ids.amount) / 100)
            elif target_lines_ids:
                if line.target_group_id.commission_type == 'amount':
                    price_subtotal = line.amount_untaxed - target_lines_ids.amount
                elif line.target_group_id.commission_type == 'percentage':
                    price_subtotal = line.amount_untaxed * ((target_lines_ids.amount) / 100)
            # elif line.order_id.user_id.name == self.env.user.name:
            #     price_subtotal = line.price_subtotal
            # elif line.order_id.user_id and line.order_id.team_id:
            #     price_subtotal = line.price_subtotal
            line.price_commission = price_subtotal

    price_commission = fields.Monetary(compute='_compute_commission', string='Commission',
                                       readonly=True, store=True)
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('price_subtotal')
    def _compute_amount_commission(self):
        for line in self:
            price_subtotal = line.price_subtotal
            # target_lines_ids = self.env['target.lines'].search([('target_group_id', '=', line.order_id.target_group_id.id), ('min_target', '<=', line.price_subtotal), ('max_target', '>=', line.price_subtotal)], limit=1)
            # if target_lines_ids:
            #     if line.order_id.target_group_id.commission_type == 'amount':
            #         price_subtotal = line.price_subtotal - target_lines_ids.amount
            #     elif line.order_id.target_group_id.commission_type == 'percentage':
            #         price_subtotal = line.price_subtotal - ((line.price_subtotal * target_lines_ids.amount) / 100)
            line.update({
                'price_subtotal_commission': price_subtotal,
            })

    price_subtotal_commission = fields.Monetary(compute='_compute_amount_commission', string='Subtotal With Commission', readonly=True, store=True)

    @api.depends('price_subtotal','order_id.target_group_id','order_id.user_id','order_id.team_id')
    def _compute_commission(self):
        for line in self:
            price_subtotal = 0.00
            target_lines_ids = self.env['target.lines'].search(
                [('target_group_id', '=', line.order_id.target_group_id.id), ('min_target', '<=', line.price_subtotal),
                 ('max_target', '>=', line.price_subtotal)], limit=1)
            if line.order_id.team_id and  line.order_id.team_id.target_group_id:
                team_target_lines_ids = self.env['target.lines'].search(
                    [('target_group_id', '=', line.order_id.team_id.target_group_id.id),
                     ('min_target', '<=', line.price_subtotal),
                     ('max_target', '>=', line.price_subtotal)], limit=1)
                if team_target_lines_ids and line.order_id.team_id.target_group_id.commission_type == 'amount':
                    price_subtotal = line.price_subtotal - team_target_lines_ids.amount
                elif team_target_lines_ids and line.order_id.team_id.target_group_id.commission_type == 'percentage':
                    price_subtotal = line.price_subtotal * ((team_target_lines_ids.amount) / 100)
            elif target_lines_ids:
                if line.order_id.target_group_id.commission_type == 'amount':
                    price_subtotal = line.price_subtotal - target_lines_ids.amount
                elif line.order_id.target_group_id.commission_type == 'percentage':
                    price_subtotal = line.price_subtotal * ((target_lines_ids.amount) / 100)
            # elif line.order_id.user_id.name == self.env.user.name:
            #     price_subtotal = line.price_subtotal
            # elif line.order_id.user_id and line.order_id.team_id:
            #     price_subtotal = line.price_subtotal
            line.update({
                'price_commission': price_subtotal,
            })

    price_commission = fields.Monetary(compute='_compute_commission', string='Commission',
                                                readonly=True, store=True)

class TargetGroup(models.Model):
    _name = 'target.group'

    name = fields.Char('Name')
    commission_type = fields.Selection([('amount','Amount'), ('percentage','Percentage')], 'Commission Type', default='amount')
    target_lines = fields.One2many('target.lines', 'target_group_id')


class TargetLine(models.Model):
    _name = 'target.lines'

    target_group_id = fields.Many2one('target.group')
    min_target = fields.Float('Min Target')
    max_target = fields.Float('Max Target')
    amount = fields.Float('Commission Amount')


class sale_commission_report(models.Model):
    _name = 'sale.commission.report'
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Sales Order', readonly=True)
    date = fields.Datetime('Date Order', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True, oldname='section_id')
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    price_subtotal = fields.Float('Untaxed Total', readonly=True)
    price_commission = fields.Float('Commission', readonly=True)


    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.product_id as product_id,
                    sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                    sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
                    sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
                    sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
                    sum(l.price_total / COALESCE(cr.rate, 1.0)) as price_total,
                    sum(l.price_subtotal_commission) as price_subtotal,
                    sum(l.price_commission) as price_commission,
                    count(*) as nbr,
                    s.name as name,
                    s.date_order as date,
                    s.user_id as user_id,
                    extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                    s.team_id as team_id,
                    sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
                    sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                      join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                    left join currency_rate cr on (cr.currency_id = pp.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    s.name,
                    s.date_order,
                    s.user_id,
                    s.team_id
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self._cr, 'sale_commission_report')
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: