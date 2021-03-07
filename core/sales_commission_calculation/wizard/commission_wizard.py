# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class ReportClassName(models.AbstractModel):
    _name = 'report.sales_commission_calculation_ext.report_sales_commission'

    @api.model
    def render_html(self, docids, data=None):
        if 'active_id' not in self._context:
            return True
        if 'active_model' not in self._context:
            return True
        if self._context['active_model'] != 'commission.wizard':
            return True
        active_id = self._context['active_id']
        commission_wizard = self.env['commission.wizard'].browse(active_id)
        report_data = commission_wizard.get_report_data()
        r_name = 'sales_commission_calculation_ext.report_sales_commission'
        return self.env['report'].render(r_name, report_data)


class CommissionWizard(models.TransientModel):
    _name = "commission.wizard"

    sales_team_id = fields.Many2one('crm.team', "Sales Teams")
    start_period = fields.Datetime("Start Period")
    end_period = fields.Datetime("End Period")

    def print_commission_pdf_report(self):
        commission_lines = self.get_report_data()
        r_name = 'sales_commission_calculation_ext.report_sales_commission'
        return self.env['report'].get_action(
            self, r_name, data=commission_lines)

    def get_report_data(self):
        commissions = []
        domain = [('commission_calculation_type', '=', 'SO')]
        if self.sales_team_id:
            domain.append(('sales_team', '=', self.sales_team_id.name))

        if self.start_period:
            domain.append(('date', '>=', self.start_period))

        if self.end_period:
            domain.append(('date', '<=', self.end_period))

        commissions = self.env['commission.commission'].search(domain, order="date")

        schemes = {}
        for commission in commissions:
            if commission.commission_scheme_id not in schemes:
                schemes[commission.commission_scheme_id] = [commission]
            else:
                schemes[commission.commission_scheme_id].append(commission)

        # Use for Monthly Scheme
        amount_line = []
        qty_line = []

        # Use for Yearly Scheme
        y_amount_line = []
        y_qty_line = []
        for scheme in schemes:
            scheme_obj = self.env['commission.scheme'].search(
                [('name', '=', scheme)], limit=1)

            # Yearly Scheme
            if scheme_obj.interval == 'yearly':
                y_interval_list = []
                for commission in schemes[scheme]:
                    vals = {}
                    date = datetime.strptime(commission.date, "%Y-%m-%d")
                    year = date.year
                    interval = str(year)
                    if interval not in y_interval_list:
                        m_interval_list.append(interval)
                        vals[interval] = [{
                            'salesperson': commission.salesperson,
                            'target': commission.target,
                            'achieved': commission.achieved,
                            'commission_amount': commission.commission_amount
                        }]
                        if commission.target_type == 'Amount':
                            y_amount_line.append(vals)
                        else:
                            y_qty_line.append(vals)
                    else:
                        proccess_lines = []
                        if commission.target_type == 'Amount':
                            proccess_lines = y_amount_line
                        else:
                            proccess_lines = y_qty_line

                        for index in range(0, len(proccess_lines)):
                            flage = True
                            for j in range(0, len(proccess_lines[index][interval])):
                                if interval in proccess_lines[index] and commission.salesperson == proccess_lines[index][interval][j]['salesperson'] and commission.target == proccess_lines[index][interval][j]['target']:
                                    proccess_lines[index][interval][j]['achieved'] += commission.achieved
                                    proccess_lines[index][interval][j]['commission_amount'] += commission.commission_amount
                                    flage = False
                            if flage:
                                proccess_lines[index][interval].append({
                                    'salesperson': commission.salesperson,
                                    'target': commission.target,
                                    'achieved': commission.achieved,
                                    'commission_amount': commission.commission_amount
                                })
                        if commission.target_type == 'Amount':
                            y_amount_line = proccess_lines
                        else:
                            y_qty_line = proccess_lines

            # Other than Yearly Scheme
            else:
                m_interval_list = []
                for commission in schemes[scheme]:
                    vals = {}
                    date = datetime.strptime(commission.date, "%Y-%m-%d")
                    month = date.strftime("%b").upper()
                    year = date.year
                    interval = month + " " + str(year)
                    if interval not in m_interval_list:
                        m_interval_list.append(interval)
                        vals[interval] = [{
                            'salesperson': commission.salesperson,
                            'target': commission.target,
                            'achieved': commission.achieved,
                            'commission_amount': commission.commission_amount
                        }]
                        if commission.target_type == 'Amount':
                            amount_line.append(vals)
                        else:
                            qty_line.append(vals)
                    else:
                        proccess_lines = []
                        if commission.target_type == 'Amount':
                            proccess_lines = amount_line
                        else:
                            proccess_lines = qty_line

                        for index in range(0, len(proccess_lines)):
                            flage = True
                            for j in range(0, len(proccess_lines[index][interval])):
                                if interval in proccess_lines[index] and commission.salesperson == proccess_lines[index][interval][j]['salesperson'] and commission.target == proccess_lines[index][interval][j]['target']:
                                    proccess_lines[index][interval][j]['achieved'] += commission.achieved
                                    proccess_lines[index][interval][j]['commission_amount'] += commission.commission_amount
                                    flage = False
                            if flage:
                                proccess_lines[index][interval].append({
                                    'salesperson': commission.salesperson,
                                    'target': commission.target,
                                    'achieved': commission.achieved,
                                    'commission_amount': commission.commission_amount
                                })
                        if commission.target_type == 'Amount':
                            amount_line = proccess_lines
                        else:
                            qty_line = proccess_lines
        monthly_line_vals = [{"qty": qty_line, "amount": amount_line}]
        yearly_line_vals = [{"qty": y_qty_line, "amount": y_amount_line}]
        commission_lines = [{'monthly': monthly_line_vals, 'yearly': yearly_line_vals}]
        data = {'commission_lines': commission_lines}
        return data

    def print_commission_xls_report(self):
        print "===== xls -------"
