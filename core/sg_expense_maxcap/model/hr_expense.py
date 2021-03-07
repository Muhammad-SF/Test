# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from datetime import datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError,UserError


class hr_contract(models.Model):

    _inherit = "hr.expense"

    contract_id = fields.Many2one('hr.contract','Contract')

    @api.onchange('employee_id','date')
    def _check_expense_contract(self):
        for exp in self:
            if exp.employee_id and exp.employee_id.id and exp.date:
                contract_ids = self.env['hr.contract'].search([('employee_id','=',exp.employee_id.id),
                                                               ('date_start','<=',exp.date),'|',
                                                               ('date_end','>=',exp.date),
                                                               ('date_end','=',False),
                                                               ])
                if contract_ids and contract_ids.ids:
                    contract_ids = contract_ids.ids
                    exp.contract_id = contract_ids[0]
#                else:
#                    if not contract_ids.ids:
#                        raise UserError(_('No contract found for the Employee "%s" based on current expense date.' %(exp.employee_id.name)))
#                    if contract_ids and len(contract_ids.ids) > 1:
#                        raise UserError(_('Multiple contracts found for the Employee "%s" based on current expense date.' %(exp.employee_id.name)))


    @api.multi
    @api.constrains('state','product_id','unit_amount','total_amount','employee_id','date','contract_id')
    def _check_expense_line_prod(self):
        for expense in self:
            if expense.contract_id and expense.contract_id.id:
                contract = expense.contract_id
                if expense.date >= contract.date_start and expense.date <= contract.date_end:
                    if contract.hr_cont_prod_ids and contract.hr_cont_prod_ids.ids:
                        for con_line in contract.hr_cont_prod_ids:
                            if con_line.product_id and con_line.product_id.id and con_line.product_id.id == expense.product_id.id and \
                                    (con_line.start_date <= expense.date and con_line.end_date >= expense.date):
                                if con_line.pro_rate == True:
                                    cont_st_date = datetime.strptime(con_line.start_date, DEFAULT_SERVER_DATE_FORMAT)
                                    cont_ed_date = datetime.strptime(con_line.end_date, DEFAULT_SERVER_DATE_FORMAT)
                                    expense_date = datetime.strptime(expense.date, DEFAULT_SERVER_DATE_FORMAT)

                                    remain_mnt = 1
                                    remain_month = relativedelta(expense_date, cont_st_date)
                                    if remain_month:
                                        if remain_month.years:
                                            remain_mnt += (remain_month.years) * 12
                                        if remain_month.months:
                                            remain_mnt += remain_month.months

                                    cont_months = relativedelta(cont_ed_date, cont_st_date)
                                    contract_mnt = 1
                                    if cont_months:
                                        if cont_months.years:
                                            contract_mnt += (cont_months.years) * 12
                                        if cont_months.months:
                                            contract_mnt += cont_months.months

                                    max_prod_cap = round((con_line.max_prod_cap / contract_mnt) * remain_mnt)
                                    total_amt = con_line.max_exp_cap_draft + con_line.max_exp_cap
                                    if max_prod_cap < total_amt and con_line.override == False:
                                        raise ValidationError(_('You can not apply expense more than pro ration amount of %s ' % (max_prod_cap)))
                                else:
                                    total_amnt = con_line.max_exp_cap_draft + con_line.max_exp_cap
                                    if con_line.max_prod_cap < total_amnt and con_line.override == False:
                                        raise ValidationError(_('You can not create expense over your expense limit.\
                                                                \nYour expense limit for product "%s" is : %s .\
                                                                \nAnd you have already approved expenses for same product is : %s .\
                                                                \n'%(con_line.product_id.name,
                                                                     con_line.max_prod_cap,
                                                                     con_line.max_exp_cap)))

