# -*- coding: utf-8 -*-
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
	_inherit = 'payment.transaction'

	student_id = fields.Many2one('student.student')

	@api.multi
	def write(self, vals):
		if vals.get('state',False) and (self.student_id or vals.get('student_id',False)):
			if vals.get('state') == 'done':
				student_payslip_id = self.env['student.payslip'].sudo().search([('state','=','draft'), ('student_id','=',self.student_id.id)], limit=1)
				if student_payslip_id and not student_payslip_id.journal_id:
					journal = self.env['account.journal'].sudo().search([('type', '=',
																'sale')],
															  limit=1)
					student_payslip_id.journal_id = journal and journal.id
				if self.student_id and self.student_id.school_id and self.student_id.school_id.application_fee_id:
					if student_payslip_id and not student_payslip_id.fees_structure_id:
						student_payslip_id.fees_structure_id = self.student_id.school_id.application_fee_id.id
				template_id = self.env.ref('school_enrolment_paypal.student_payment_confirmation_template_id')
				template_id.email_to = self.student_id.email
				template_id.send_mail(self.student_id.id, force_send=True)
				student_payslip_id.payslip_confirm()
				payment = False
				invoice_id = False
				invoice_id = self.env['account.invoice'].search([('state','in',['draft','open']), ('student_payslip_id','=', student_payslip_id and student_payslip_id.id or False)], limit=1)
				
				if invoice_id:
					payment_type = invoice_id.type in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
					communication = self.type in ('in_invoice', 'in_refund') and invoice_id.reference or invoice_id.number
					pay_journal = self.env['account.journal'].sudo().search([('type', '=', 'cash')], limit=1)
					payment_method = self.env.ref('account.account_payment_method_manual_in')
					payment = self.env['account.payment'].create({
			            'invoice_ids': [(6, 0, invoice_id and invoice_id.ids or [])],
			            'amount': invoice_id.residual or 0.0,
			            'payment_date': fields.Date.context_today(self),
			            'communication': communication,
			            'partner_id': invoice_id.partner_id.id,
			            'partner_type': invoice_id.type in ('out_invoice', 'out_refund') and 'customer' or 'supplier',
			            'journal_id': pay_journal and pay_journal.id or False,
			            'payment_type': payment_type,
			            'payment_method_id': payment_method.id,
		        	})
		        	if payment:
		        		payment.post()
		res = super(PaymentTransaction, self).write(vals)
		return res