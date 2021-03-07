from odoo import fields, api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime,date
from odoo.exceptions import ValidationError

class hr_contract(models.Model):

    _inherit = 'hr.contract'
    
    @api.constrains('date_end','date_start')
    def _check_date(self):
        for contract in self:
            domain = [('date_start', '<=', contract.date_end),
                      ('date_end', '>=', contract.date_start),
                      ('employee_id', '=', contract.employee_id.id),
                      ('id', '!=', contract.id)]
            contract_ids=self.search(domain, count=True)
            if contract_ids:
                raise ValidationError('You can not have 2 contract that overlaps on same date!')
        return True
    
    @api.constrains('hr_contract_income_tax_ids')
    def _check_incomtax_year(self):
        for contract in self:
            if contract.hr_contract_income_tax_ids and contract.hr_contract_income_tax_ids.ids:
                for incmtax in contract.hr_contract_income_tax_ids:
                    domain = [('start_date', '<=', incmtax.end_date),
                              ('end_date','>=', incmtax.start_date),
                              ('contract_id', '=', contract.id),
                              ]
                    contract_ids = self.env['hr.contract.income.tax'].search(domain)
                    if len(contract_ids) > 1:
                        raise ValidationError('You can not configure multiple income tax that overlap on same date!')

class hr_contract_income_tax(models.Model):

    _inherit = 'hr.contract.income.tax'
    
    @api.constrains('director_fee_approval_date')
    def _check_director_fee_approval_date(self):
        for rec in self:
            if rec.director_fee_approval_date and rec.end_date:
                dir_year=datetime.strptime(rec.director_fee_approval_date, DEFAULT_SERVER_DATE_FORMAT).year
                year_id=datetime.strptime(rec.end_date, DEFAULT_SERVER_DATE_FORMAT).year 
                if dir_year >= year_id:
                    raise ValidationError("Wrong IR8A Configuration: (50).Date of approval of directors fees is accepted up to previous income years!")
