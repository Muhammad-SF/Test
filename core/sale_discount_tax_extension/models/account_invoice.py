# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare


class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	@api.one
	@api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice',
				 'global_discount_type', 'global_order_discount')
	def _compute_amount(self):
		super(AccountInvoice, self)._compute_amount()
		amountss = 0.0
		amountadd = 0.0
		amountadd1 = 0.0
		pay_separate_tax = 0.0
		round_curr = self.currency_id.round

		amountUntaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
		amountTax = sum(line.amount for line in self.tax_line_ids)
		totalDiscount = sum(((line.price_subtotal) * (
					(line.discount or 0.0) / 100.0))
					if line.discount_type == 'percent' else line.discount for line in self.invoice_line_ids)
		if self.tax_line_ids:
			for line in self.tax_line_ids:
				if line.tax_id.price_include_total:
					amountss += round_curr(line.amount)
				elif line.tax_id.price_include_total:
					amountadd += round_curr(line.amount)
					self.amount_untaxed = self.amount_untaxed - amountadd
				else:
					amountadd1 += round_curr(line.amount)
					amountadd += round_curr(line.amount)
				self.amount_total = self.amount_untaxed + amountadd - abs(amountss)
				if line.tax_id.pay_seprately:
					pay_separate_tax += round_curr(line.amount)
					self.payment_fields_boolean = True

		totalAmount = amountUntaxed + amountTax - totalDiscount
		discTax =  0
		if self.type and self.type in ('out_invoice', 'out_refund'):
			discTax = self.env['ir.config_parameter'].get_param('discount_sale_order.global_sale_discount_tax', 0)
		if self.global_order_discount and self.global_discount_type:
			if discTax == 0:
				totalAmount = amountUntaxed
			else:
				totalAmount = amountUntaxed + amountTax
			if self.global_discount_type == 'percent':
				beforeGlobal = totalAmount
				totalAmount = totalAmount * (1 - (self.global_order_discount or 0.0) / 100)
				totalGlobalDiscount = beforeGlobal - totalAmount
				totalDiscount = totalGlobalDiscount
			else:
				totalGlobalDiscount = self.global_order_discount or 0.0
				totalAmount = totalAmount - totalGlobalDiscount
				totalDiscount = totalGlobalDiscount
			if discTax == 0:
				totalAmount = totalAmount + amountTax
		self.total_discount = totalDiscount
		self.amount_untaxed = amountUntaxed
		self.amount_tax = amountTax
		self.amount_total = totalAmount
		self.ppn = ("""%s %s""") % (amountadd1, self.company_currency_id.symbol)
		self.pph = ("""%s %s""") % (amountss, self.company_currency_id.symbol)
		self.separate_tax_amount = pay_separate_tax
		amount_total_company_signed = self.amount_total
		amount_untaxed_signed = self.amount_untaxed
		if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
			currency_id = self.currency_id.with_context(date=self.date_invoice)
			amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
			amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
		sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
		self.amount_total_company_signed = amount_total_company_signed * sign
		self.amount_total_signed = self.amount_total * sign
		self.amount_untaxed_signed = amount_untaxed_signed * sign

	@api.multi
	def get_taxes_values(self):
		tax_grouped = {}
		for line in self.invoice_line_ids:
			tax_included = line.invoice_line_tax_ids.filtered(lambda tax: tax.price_include)
			tax_not_included = line.invoice_line_tax_ids.filtered(lambda tax: not tax.price_include)
			taxes_included_values = tax_included.compute_all(line.price_unit, line.invoice_id.currency_id,
															 line.quantity, product=line.product_id,
															 partner=line.invoice_id.partner_id)
			taxes_included_amount = taxes_included_values['taxes']
			sub_total = taxes_included_values['total_excluded']
			for tax in taxes_included_amount:
				val = self._prepare_tax_line_vals(line, tax)
				key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)
				if key not in tax_grouped:
					tax_grouped[key] = val
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += val['base']

			if line.discount_type == 'fixed':
				price_subtotal = sub_total - (line.discount or 0.0)
			else:
				price_subtotal = sub_total * (1 - (line.discount or 0.0) / 100.0)
			quantity = 1
			taxes_not_included_amount = tax_not_included.compute_all(price_subtotal, line.invoice_id.currency_id, quantity, product=line.product_id,
										 partner=line.invoice_id.partner_id)['taxes']
			for tax in taxes_not_included_amount:
				val = self._prepare_tax_line_vals(line, tax)
				key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)
				if key not in tax_grouped:
					tax_grouped[key] = val
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += val['base']
		res = tax_grouped
		return res


class invoiceLine(models.Model):
	_inherit = 'account.invoice.line'

	@api.one
	@api.depends('price_unit', 'discount', 'discount_type', 'invoice_line_tax_ids', 'quantity',
				 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
				 'invoice_id.date_invoice', 'invoice_id.date')
	def _compute_price(self):
		if self.invoice_id.type and self.invoice_id.type in ('out_invoice', 'out_refund'):
			currency = self.invoice_id and self.invoice_id.currency_id or None
			tax_included = self.invoice_line_tax_ids.filtered(lambda tax: tax.price_include)
			tax_not_included = self.invoice_line_tax_ids.filtered(lambda tax: not tax.price_include)
			taxes = tax_included.compute_all(self.price_unit, self.invoice_id.currency_id, self.quantity,
											 product=self.product_id, partner=self.invoice_id.partner_id)
			sub_total = taxes['total_excluded']
			if self.discount_type == 'fixed':
				line_subtotal = sub_total - self.discount or 0.0
			else:
				line_subtotal = sub_total * (1 - (self.discount or 0.0) / 100.0)
			quantity = 1
			taxes = tax_not_included.compute_all(line_subtotal, currency, quantity, product=self.product_id,
														  partner=self.invoice_id.partner_id)
			price = taxes['total_excluded'] if taxes else line_subtotal * self.quantity

			self.price_reduce = price - (line_subtotal / self.quantity)
			self.price_subtotal = price_subtotal_signed = sub_total
			self.line_sub_total = line_subtotal

			if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
				price_subtotal_signed = self.invoice_id.currency_id.with_context(
					date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed,
																			self.invoice_id.company_id.currency_id)
			sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
			self.price_subtotal_signed = price_subtotal_signed * sign

		else:
			super(invoiceLine, self)._compute_price()