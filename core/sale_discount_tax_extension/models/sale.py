# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class SaleOrder(models.Model):
	_inherit = "sale.order"

	@api.depends('order_line.price_total', 'global_order_discount', 'global_discount_type')
	def _amount_all(self):
		for order in self:
			total_discount = 0.0
			amount_untaxed = 0.0
			amount_tax = 0.0
			inc_tax = 0.0
			exl_tax = 0.0
			total_discount = 0.0
			round_curr = order.currency_id.round
			for line in order.order_line:
				amount_untaxed += line.line_sub_total
				if line.discount_type == 'fixed':
					total_discount += line.line_discount
				else:
					total_discount += line.line_sub_total * ((line.line_discount or 0.0) / 100.0)
				for tax in line.tax_id:
					if tax.price_include_total:
						in_tax_amount = tax.with_context(
							base_values=(line.price_subtotal, line.price_subtotal, line.price_subtotal)).compute_all(
							line.line_sub_total, line.order_id.currency_id, 1, product=line.product_id,
							partner=line.order_id.partner_id)
						tax_amt = sum(t.get('amount', 0.0) for t in in_tax_amount.get('taxes', []))
						inc_tax += round_curr(tax_amt)
						amount_tax += round_curr(tax_amt)
					else:
						price = line.price_unit
						if tax.price_include:
							ex_tax_amount = tax.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
															product=line.product_id, partner=line.order_id.partner_id)
							tax_amt = sum(t.get('amount', 0.0) for t in ex_tax_amount.get('taxes', []))
							exl_tax += round_curr(tax_amt)
							amount_tax += round_curr(tax_amt)
						else:

							ex_tax_amount = tax.compute_all(line.price_subtotal, line.order_id.currency_id, 1,
															product=line.product_id, partner=line.order_id.partner_id)
							tax_amt = sum(t.get('amount', 0.0) for t in ex_tax_amount.get('taxes', []))
							exl_tax += round_curr(tax_amt)
							amount_tax += round_curr(tax_amt)
		total_amount = amount_untaxed + amount_tax - total_discount
		if self.global_discount_type and self.global_order_discount:
			discTax = self.env['ir.config_parameter'].get_param('discount_purchase_order.global_discount_tax', 0)
			if discTax == 0:
				total_amount = amount_untaxed
			else:
				total_amount = amount_untaxed + amount_tax
			if order.global_discount_type == 'percent':
				beforeGlobal = total_amount
				total_amount = total_amount * (1 - (order.global_order_discount or 0.0) / 100)
				total_discount = beforeGlobal - total_amount
			else:
				total_amount = total_amount - (order.global_order_discount or 0.0)
				total_discount = order.global_order_discount
			if discTax == 0:
				total_amount = total_amount + amount_tax

		vals = {
			'amount_untaxed': order.currency_id.round(amount_untaxed),
			'amount_tax': order.currency_id.round(amount_tax),
			'amount_total': total_amount,
			'total_discount': total_discount,
			'ppn': ("""%s""") % (exl_tax),
			'pph': ("""%s""") % (inc_tax)
		}
		order.update(vals)


class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"


	@api.depends('product_uom_qty', 'price_unit', 'tax_id', 'discount', 'discount_type')
	def _compute_amount(self):
		for line in self:
			tax_included = line.tax_id.filtered(lambda tax: tax.price_include)
			tax_not_included = line.tax_id.filtered(lambda tax: not tax.price_include)
			taxes = tax_included.compute_all(line.price_unit, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
			sub_total = taxes['total_excluded']
			tax_included_amount = taxes['total_included'] - taxes['total_excluded']
			if line.discount_type == 'fixed':
				price_subtotal = sub_total - (line.line_discount or 0.0)
				price_reduce = sub_total - (line.line_discount or 0.0)
			else:
				price_reduce = sub_total * (1 - (line.line_discount or 0.0) / 100.0)
				price_subtotal = price_reduce
			quantity = 1

			taxes = tax_not_included.compute_all(price_subtotal, line.order_id.currency_id, quantity, product=line.product_id, partner=line.order_id.partner_id)
			tax_not_included_amount = taxes['total_included'] - taxes['total_excluded']
			vals = {
				'price_tax': tax_included_amount + tax_not_included_amount,
				'price_total': taxes['total_included'],
				'price_subtotal': price_subtotal,
				'price_reduce': price_reduce,
				'line_sub_total': sub_total,
			}
			line.update(vals)