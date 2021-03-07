# -*- coding: utf-8 -*-

from odoo import models, exceptions, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

month_dict = {
    '01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June',
    '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December'
}

class sale_commission_report_wizard(models.TransientModel):
    
    _name = 'sale.commission.report.wizard'

    report_type = fields.Selection([('summary', 'Summary'), ('details', 'Details')])
    starting_month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')],
        string="Starting Month")
    ending_month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')],
        string="Ending Month")

    year = fields.Selection([(num, str(num)) for num in range((datetime.now().year) - 10, (datetime.now().year) + 11)],
        string='Year', default=datetime.now().year)
    user_id = fields.Many2many('res.users', string='Salesperson')

    # @api.multi
    # @api.depends('report_type', 'starting_month', 'ending_month', 'year')
    # def _get_date(self):
    #     for rec in self:
    #         start_date = False
    #         end_date = False
    #         if rec.report_type == 'details':
    #             if rec.starting_month and rec.ending_month and rec.year:
    #                 start_date = datetime(int(rec.year), int(rec.starting_month), 1, 00, 00, 00)
    #                 # end_date = datetime(int(rec.year), int(rec.ending_month), 1, 23, 59, 59)
    #                 end_date = datetime(int(rec.year), int(rec.ending_month)+1, 1, 00, 00, 00)
    #         if rec.report_type == 'summary':
    #             if rec.year:
    #                 start_date = datetime(int(rec.year), 1, 1, 00, 00, 00)
    #                 # end_date = datetime(int(rec.year), 12, 31, 23, 59, 59)
    #                 end_date = datetime(int(rec.year)+1, 1, 1, 00, 00, 00)
    #         rec.start_date = start_date
    #         rec.end_date = end_date
    #
    # start_date = fields.Datetime('Start Date', compute='_get_date', store=True)
    # end_date = fields.Datetime('End Date', compute='_get_date', store=True)

    @api.multi
    def print_commission_report(self):
        if self.report_type == 'details':
            if int(self.starting_month) > int(self.ending_month):
                raise UserError(_('Ending month should be greated then Starting month.'))

        # domain = [('confirmation_date', '>=', self.start_date),('confirmation_date', '<', self.end_date)]
        # if self.user_id:
        #     domain.append(('user_id', 'in', self.user_id.ids))
        # sale_orders = self.env['sale.order'].sudo().search(domain)
        # return self.env['report'].get_action(sale_orders, 'sale_commission_target_gt.report_sale_commission')

        sale_commission_data = {
            'selected_year': self.year,
            'report_type': self.report_type,
        }
        all_months = []
        if self.report_type == 'details':
            sale_commission_data.update({
                'starting_month': month_dict[self.starting_month],
                'ending_month': month_dict[self.ending_month],
            })
            starting_month = int(self.starting_month)
            ending_month = int(self.ending_month)
            months = []
            if (starting_month == 12) or (ending_month == 12):
                months = range(int(self.starting_month), int(self.ending_month) + 1)
            else:
                months = range(int(self.starting_month), int(self.ending_month) + 1)
            all_months = months
        else:
            all_months = range(1,13)
        sale_commission_data.update({'all_months': all_months})

        sale_order_obj = self.env['sale.order'].sudo()
        users = self.env['res.users'].sudo().search([('sale_team_id','!=',False)])
        if self.user_id:
            users = self.user_id

        sale_commission_user_data_list = []
        year = int(self.year)
        for one_user in users:
            sale_commission_user_data = {
                'sales_person': one_user.name
            }
            user_commission_data = []
            user_total_sale = 0.00
            user_total_commission = 0.00
            for one_month in all_months:
                start_date = datetime(year, one_month, 1, 00, 00, 00)
                end_date = False
                if int(one_month) == 12:
                    end_date = datetime(year+1, 1, 1, 00, 00, 00)
                else:
                    end_date = datetime(year, one_month + 1, 1, 00, 00, 00)
                start_date = datetime.strftime(datetime.strptime(str(start_date), '%Y-%m-%d %H:%M:%S').date(), '%m/%d/%Y %H:%M:%S')
                end_date = datetime.strftime(datetime.strptime(str(end_date), '%Y-%m-%d %H:%M:%S').date(), '%m/%d/%Y %H:%M:%S')
                sale_orders = sale_order_obj.search([('confirmation_date', '>=', start_date),
                    ('confirmation_date', '<', end_date),('user_id', '=', one_user.id)])
                total_sales = 0.00
                total_commission = 0.00
                sale_order_details = []
                if sale_orders:
                    for one_sale_order in sale_orders:
                        total_sales += one_sale_order.amount_untaxed
                        user_total_sale += one_sale_order.amount_untaxed
                        # total_commission += one_sale_order.price_commission
                        sale_order_details.append({
                            # 'order_date': str(one_sale_order.confirmation_date),
                            'order_date': datetime.strftime(datetime.strptime(str(one_sale_order.confirmation_date), '%Y-%m-%d %H:%M:%S').date(), '%d/%m/%Y'),
                            'order_number': str(one_sale_order.name),
                            'order_customer': str(one_sale_order.partner_id.name),
                            'sales_amount': "{0:.2f}".format(one_sale_order.amount_untaxed)
                        })

                price_subtotal = 0.00
                crm_teams = self.env['crm.team'].sudo().search([])
                for one_team in crm_teams:
                    if one_user.id in one_team.member_ids.ids and one_team.target_group_id:
                        team_target_lines_ids = self.env['target.lines'].search(
                            [('target_group_id', '=', one_team.target_group_id.id),
                             ('min_target', '<=', total_sales),
                             ('max_target', '>=', total_sales)], limit=1)

                        if team_target_lines_ids and one_team.target_group_id.commission_type == 'amount':
                            price_subtotal = total_sales - team_target_lines_ids.amount
                        elif team_target_lines_ids and one_team.target_group_id.commission_type == 'percentage':
                            price_subtotal = total_sales * ((team_target_lines_ids.amount) / 100)
                        total_commission = price_subtotal
                    sale_commission_user_data.update({
                        'target_group': one_team.target_group_id.name
                    })
                user_total_commission += total_commission

                user_commission_data.append({
                    'month': one_month,
                    'month_str': month_dict[str('{:02d}'.format(one_month))],
                    'total_sales': "{0:.2f}".format(total_sales),
                    'total_commission': "{0:.2f}".format(total_commission),
                    'sale_order_details': sale_order_details,
                })
            sale_commission_user_data.update({
                'commission_data': user_commission_data,
                'user_total_sale': "{0:.2f}".format(user_total_sale),
                'user_total_commission': "{0:.2f}".format(user_total_commission),
            })
            sale_commission_user_data_list.append(sale_commission_user_data)
        sale_commission_data.update({
            'sale_commission_user_data': sale_commission_user_data_list
        })
        datas = {
            'sale_commission_data': sale_commission_data,
        }
        if self.report_type == 'summary':
            return self.env['report'].get_action(self, 'sale_commission_target_gt.report_sale_commission', data=datas)
        if self.report_type == 'details':
            return self.env['report'].get_action(self, 'sale_commission_target_gt.report_sale_commission_detail', data=datas)
