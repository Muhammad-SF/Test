# -*- coding: utf-8 -*-
#############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
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
#############################################################################

from odoo import models, fields, api, _


class HrSalaryRuleExt(models.Model):
    _inherit = 'hr.salary.rule'
    _description = 'Inherited to categorized Ordinary and Additional Wages at salary rule level.'

    is_cpf = fields.Selection([('no_cpf', 'No CPF'), ('ow', 'OW'), ('aw', 'AW')], 'Is CPF')


class HrPayslipExt(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Inherited for Ordinary and Additional Wages Integration with Pay slip Computation.'

    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict):
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(amount) as sum
                    FROM hr_payslip as hp, hr_payslip_input as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                    SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                    FROM hr_payslip as hp, hr_payslip_worked_days as pi
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                            FROM hr_payslip as hp, hr_payslip_line as pl
                            WHERE hp.employee_id = %s AND hp.state = 'done'
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                            (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.env['hr.payslip']
        obj_rule = self.env['hr.salary.rule']
        payslip = payslip_obj.browse(payslip_id)
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

        categories_obj = BrowsableObject(payslip.employee_id.id, categories_dict)
        input_obj = InputLine(payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(payslip.employee_id.id, rules)
        #get ordinary wages and additional wages rules
        ow_brw = obj_rule.search([('is_cpf', '=', 'ow')])
        aw_brw = obj_rule.search([('is_cpf', '=', 'aw')])
        ow_ids = ow_brw.ids
        aw_ids = aw_brw.ids
        ow_total = aw_total = 0.0
        baselocaldict = {'payslip_brw':payslip,'categories': categories_obj, 'rules': rules_obj, 'payslip': payslip_obj, 'worked_days': worked_days_obj, 'inputs': input_obj}
       #get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        structure_ids = contracts.get_all_structures()
        #get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in self.env['hr.salary.rule'].browse(sorted_rule_ids):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                localdict['ow_total'] = ow_total
                localdict['aw_total'] = aw_total
                #check if the rule can be applied
                if rule.satisfy_condition(localdict) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate = rule.compute_rule(localdict)
                    if rule.id in ow_ids:
                        ow_total += float(qty) * amount * rate / 100
                        ow_ids.remove(rule.id)
                    elif rule.id in aw_ids:
                        aw_total += float(qty) * amount * rate / 100
                        aw_ids.remove(rule.id)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        result = [value for code, value in result_dict.items()]
        return result

