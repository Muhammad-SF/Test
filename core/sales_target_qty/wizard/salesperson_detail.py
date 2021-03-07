from odoo import models,fields, api, _
from datetime import datetime


class SalespersonDetailWizard(models.Model):
	_name = 'salesperson.detail'


	sale_target_qty_year = fields.Selection([(num, str(num)) for num in range((datetime.now().year) - 5, (datetime.now().year) + 20)],
							'Year')
	product_id = fields.Many2one('product.product', "Product")
	currency_id = fields.Many2one('res.currency', "Currency", default=lambda self: self.env.user.company_id.currency_id)
	crm_team_id = fields.Many2one('crm.team',string="Crm Team")
	member_id = fields.Many2one('res.users', string='Sales Person')

	sales_per_target_qty_line_ids = fields.One2many('sales.target.qty.line','line_product_id',string='Sale Quantity Target')
	actual_sales_per_target_qty_line_ids = fields.One2many('sales.target.qty.line','line_product_id',string='Sale Quantity Target')

	@api.model
	def save_details(self):
		print('\n save ---')

	@api.model
	def default_get(self,fields):
		crm_team_id = self._context.get('crm_team_id')
		product_id = self._context.get('default_product_id')
		year = self._context.get('default_sale_target_qty_year')
		pro_line_active_id = self._context.get('active_id')
		default_first = self._context.get('default_first')
		print('\n pro_line_active_id default_get ---- ',pro_line_active_id)

		res = super(SalespersonDetailWizard,self).default_get(fields)
		crm_team = self.env['crm.team'].browse(crm_team_id)

		member_list = []
		sales_target_line_ids = []

		for member in crm_team.member_ids:

			sales_target_line = self.env['sales.target.qty.line'].search([('member_id', '=',member.id), 
					('year', '=', year),('product_id','=',product_id)])
			
			print('\n sales_target_line =-==== ',sales_target_line)
			line = (0,0,{'member_id':member.id,
						 'product_id':self._context.get('default_product_id',False),
						 'show_year':self._context.get('default_sale_target_qty_year'),
						 'year':self._context.get('default_sale_target_qty_year'),
						 't_january':0.0,
						 't_february':0.0,
						 't_march':0.0,
						 't_may':0.0,
						 't_june':0.0,
						 't_july':0.0,
						 't_august':0.0,
						 't_september':0.0,
						 't_october':0.0,
						 't_november':0.0,
						 't_december':0.0
					})
			# if not sales_target_line:
			member_list.append(line)

		sales_detail = self.search([('id','=',pro_line_active_id),('product_id','=',product_id)],limit=1)
		
		print('\n sales_detail -- ',sales_detail)
		if not sales_detail:
			res['sales_per_target_qty_line_ids'] = member_list
			res['crm_team_id'] = crm_team_id

		return res
	

	@api.model
	def create(self,vals):
		pro_line_active_id = self._context.get('active_id')

		pro_line = self.env['sales.target.product.line'].browse(pro_line_active_id)
		res = super(SalespersonDetailWizard,self).create(vals)

		if pro_line:
			pro_line.salesperson_detail_id = res.id

		for line in res.sales_per_target_qty_line_ids:
			line.product_id = res.product_id
			line.year = res.sale_target_qty_year

		return res
