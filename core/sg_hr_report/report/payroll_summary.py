# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, models
import time


class payroll_summary_report(models.AbstractModel):
    _name = 'report.sg_hr_report.hr_payroll_summary_report_tmp'

#    @api.model
#    def get_groupname(self, data):
#        start_date = datetime.datetime.strptime(data.get('date_from'), "%Y-%m-%d")
#        month = start_date.strftime('%m')
#        year = start_date.strftime('%Y')
#        list = []
#        res = {
#               'period': month,
#               'year': year,
#            }
#        list.append(res)
#        return list

    @api.model
    def get_name(self, data):
        date_from = data.get('date_from' or False)
        date_to = data.get('date_to' or False)
        result = {}
        total = {}
        employee_ids = self.env['hr.employee'].search([('id', 'in', data.get('employee_ids'))])
        for employee in employee_ids:
            payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', employee.id),
                                                         ('date_from', '>=', date_from),
                                                         ('date_from', '<=', date_to),
                                                         ('state', 'in', ['draft', 'done', 'verify'])])
            commission = incentive = net = twage = lvd = exa = exd = gross = cpf = pf = overtime = backpay = bonus = donation = cpftotal = sdl = fwl = 0.0
            for payslip in payslip_ids:
                for rule in payslip.details_by_salary_rule_category:
                    if rule.code == 'SC102':
                        overtime += rule.total
                    if rule.code == 'SC104':
                        commission += rule.total
                    if rule.code == 'SC105':
                        incentive += rule.total
                    if rule.code == 'NET':
                        net += rule.total
                    if rule.code == 'SC206':
                        lvd += rule.total
                    if rule.code == 'SC122':
                        exa += rule.total
                    if rule.code == 'SC299':
                        exd += rule.total
                    if rule.code == 'GROSS':
                        gross += rule.total
                    if rule.category_id.code == 'CAT_CPF_EMPLOYEE':
                        cpf += rule.total
                    if rule.category_id.code == 'CAT_CPF_EMPLOYER':
                        pf += rule.total
                    if rule.category_id.code == 'CAT_CPF_TOTAL':
                        cpftotal += rule.total
                    if rule.code == 'SC48':
                        backpay += rule.total
                    if rule.code == 'SC121':
                        bonus += rule.total
                    if rule.register_id.name in ['CPF - ECF', 'CPF - MBMF', 'CPF - SINDA', 'CPF - CDAC']:
                        donation += rule.total
                    if rule.code == 'CPFSDL':
                        sdl += rule.total
                    if rule.code == 'FWL':
                        fwl += rule.total
            payslip_result = {'ename': payslip.employee_id.name or '',
                              'eid': payslip.employee_id and payslip.employee_id.user_id and payslip.employee_id.user_id.login or '',
                              'bank_acc_id': payslip.employee_id and payslip.employee_id.bank_account_id and payslip.employee_id.bank_account_id.acc_number or '',
                              'twage': payslip.contract_id.wage or 0.0,
                              'net': net or 0.0,
                              'lvd': lvd or 0.0,
                              'exa': exa or 0.0,
                              'exd': exd or 0.0,
                              'gross': gross or 0.0,
                              'cpf': cpf or 0.0,
                              'pf': pf or 0.0,
                              'bonus': bonus or 0.0,
                              'overtime': overtime or 0.0,
#                              'backpay': backpay or 0.0,
                              'donation': donation or 0.0,
                              'cpftotal': cpftotal or 0.0,
                              'sdl': sdl or 0.0,
                              'fwl': fwl or 0.0,
                              'incentive': incentive or 0.0,
                              'commission': commission or 0.0}
            if payslip.employee_id.department_id:
                if payslip.employee_id.department_id.id in result:
                    result.get(payslip.employee_id.department_id.id).append(payslip_result)
                else:
                    result.update({payslip.employee_id.department_id.id: [payslip_result]})
            else:
                if 'Undefined' in result:
                    result.get('Undefined').append(payslip_result)
                else:
                    result.update({'Undefined': [payslip_result]})
        finalcommission = finalincentive = finaltwage = finalnet = finallvd = finalexa = finalexd = finalgross = finalcpf = finalpf = finalovertime = finalbackpay = finalbonus = finaldonation = finalcpftotal = finalsdl = finalfwl = 0
        final_result = {}
        for key, val in result.items():
            if key == 'Undefined':
                category_name = 'Undefined'
            else:
                category_name = self.env['hr.department'].browse(key).name
            total = {'name': category_name, 'commission': 0.0, 'incentive':0.0, 'twage': 0.0, 'net': 0.0, 'lvd': 0.0, 'exa': 0.0, 'exd': 0.0, 'gross':0.0, 'cpf': 0.0, 'pf': 0.0, 'overtime': 0.0, 'backpay': 0.0, 'bonus': 0.0, 'donation':0.0, 'cpftotal': 0.0, 'sdl': 0.0, 'fwl':0.0}
            for line in val:
                for field in line:
                    if field in total:
                        total.update({field:  total.get(field) + line.get(field)})
            final_result[key] = {'lines': val, 'total': total}
            finaltwage += total['twage']
            finalnet += total['net']
            finallvd += total['lvd']
            finalexa += total['exa']
            finalexd += total['exd']
            finalgross += total['gross']
            finalcpf += total['cpf']
            finalpf += total['pf']
            finalovertime += total['overtime']
            finalbackpay += total['backpay']
            finalbonus += total['bonus']
            finaldonation += total['donation']
            finalcpftotal += total['cpftotal']
            finalsdl += total['sdl']
            finalfwl += total['fwl']
            finalcommission += total['commission']
            finalincentive += total['incentive']
            
        final_total = {'twage' : finaltwage or 0.0,
                       'net' : finalnet or 0.0,
                       'lvd' : finallvd or 0.0,
                       'exa' : finalexa or 0.0,
                       'exd' : finalexd or 0.0,
                       'gross' : finalgross or 0.0,
                       'cpf' : finalcpf or 0.0,
                       'pf' : finalpf or 0.0,
                       'overtime': finalovertime or 0.0,
                       'backpay': finalbackpay or 0.0,
                       'bonus': finalbonus or 0.0,
                       'donation': finaldonation or 0.0,
                       'cpftotal': finalcpftotal or 0.0,
                       'sdl': finalsdl or 0.0,
                       'fwl': finalfwl or 0.0,
                       'commission': finalcommission or 0.0,
                       'incentive': finalincentive or 0.0}
        self.final_group_total.append(final_total)
        return final_result.values()
    
    @api.model
    def finalgrouptotal(self):
        return self.final_group_total
    
    @api.multi
    def render_html(self, docids, data):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        data = docs.read([])[0]
        self.final_group_total = []
        get_name = self.get_name(data)
        finalgrouptotal = self.finalgrouptotal()
        docargs = {'doc_ids' : self.ids,
                   'doc_model' : self.model,
                   'data' : data,
                   'docs' : docs,
                   'time' : time,
                   'get_name' : get_name,
                   'finalgrouptotal' : finalgrouptotal}
        return self.env['report'].render('sg_hr_report.hr_payroll_summary_report_tmp', docargs)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
