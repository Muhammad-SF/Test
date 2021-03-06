# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning, RedirectWarning



class ReferralConfiguration(models.TransientModel):
	_name = 'referral.config.setting'
	_inherit = 'res.config.settings'

	verify_commission = fields.Selection([
		("autoApprove","Auto Approve (When Refferal customer Signup with Refferal code)"),
		("afterOrder","On successful completion of first order (When Refferal customer Signup with Refferal code and after complete first order )"),
		], string="Commission Type",required=True,help="Referred Customer Commission based on")
	# home_page_content = fields.Html(string="Landing Page Content")
	is_refferal_points_used = fields.Boolean(required=True,Default=False,help="set Refferal points")
	referral_points = fields.Integer(string="Referral Commmission Amount",required="1", help="Reward points Earn by referral (customer who signup with friend's referral code)")
	refered_points = fields.Integer(string="Referred Commmission Amount",required="1",help="Reward points a referrer will earn (referrer: customer whose referral code is used by his friend)")
	equivalent_amount = fields.Float(string="1Point equivalent amount",default=1.0,help="equivalent amount (1 reward points is equal to how much amount)")
	currency_id = fields.Many2one('res.currency', string='Currency', required=True,
	 readonly=True,default=lambda self: self.env.user.company_id.currency_id.id)


	@api.multi
	def set_default_referrals_values(self):
		IrValues = self.env['ir.values']
		if self.env['res.users'].has_group('base.group_erp_manager'):
			IrValues = IrValues.sudo()
		IrValues.set_default('referral.config.setting', 'verify_commission', self.verify_commission)
		IrValues.set_default('referral.config.setting', 'is_refferal_points_used', self.is_refferal_points_used)
		IrValues.set_default('referral.config.setting', 'referral_points', self.referral_points)
		IrValues.set_default('referral.config.setting', 'refered_points', self.refered_points)
		IrValues.set_default('referral.config.setting', 'equivalent_amount', self.equivalent_amount)



	@api.model
	def referrals_homepage_default(self, fields=None):
		home_page_content = self.env['ir.values'].get_default('referral.config.setting', 'home_page_content')
		how_it_works_content = self.env['ir.values'].get_default('referral.config.setting', 'how_it_works_content')

		return {
		'home_page_content':home_page_content,
		'how_it_works_content':how_it_works_content,
		}

	@api.model
	def get_default_referrals_values(self, fields=None):
		referral_points = self.env['ir.values'].get_default('referral.config.setting', 'referral_points') or 0
		refered_points = self.env['ir.values'].get_default('referral.config.setting', 'refered_points') or 0
		equivalent_amount = self.env['ir.values'].get_default('referral.config.setting', 'equivalent_amount') or 1
		return {
		'referral_points':referral_points,
		'refered_points':refered_points,
		'equivalent_amount':equivalent_amount,
		}

	def default_mail_template_values(self):
		mail_subject = self.env['ir.values'].get_default('referral.config.setting', 'mail_subject') or "subject"
		mail_body = self.env['ir.values'].get_default('referral.config.setting', 'mail_body') or "body"
		return {
		'mail_subject':mail_subject,
		'mail_body':mail_body,
		}

	@api.model
	def get_default_commissionOn(self, fields=None):
		verify_commission = self.env['ir.values'].get_default('referral.config.setting', 'verify_commission') or 'autoApprove'
		return {
		'verify_commission':verify_commission,
		}


	@api.multi
	def execute(self):
		if self.referral_points < 0 :
			raise Warning(_("Referral Point should not be negative."))
		if not self.refered_points > 0:
			raise Warning(_("Referred Point should not be zero, nor negative."))
		if not self.equivalent_amount > 0:
			raise Warning(_("Equivalent Amount should not be zero, nor negative. "))
		return super(ReferralConfiguration, self).execute()


	def calculate_referral_amt(self):
		reward_amt_detail = self.get_default_referrals_values()
		return reward_amt_detail['referral_points'] * reward_amt_detail['equivalent_amount']

	def calculate_refered_amt(self):
		reward_amt_detail = self.get_default_referrals_values()
		return reward_amt_detail['refered_points'] * reward_amt_detail['equivalent_amount']

	@api.onchange('is_refferal_points_used')
	def _onchange_is_refferal_points_used(self):
		if self.is_refferal_points_used == False:
			self.referral_points = 0

	@api.model
	def demodata_set(self):
		IrValues = self.env['ir.values'].sudo()
		IrValues.set_default('referral.config.setting', 'how_it_works_content', """<ol><li><p>Refer a friend to us by sharing your Unique Referral Code with them.</p></li><li><p>Once they Sign-up using your Referral Code 'you will be rewarded by ....$ and your friend too will be rewarded by ...$'' in case of 'Auto Approve'.</p></li><li><p>In case of 'On successful completion of first order', your friend(your referral) will be rewarded by ..$ once he sign up using your referral code and you too will get rewarded as soon as your friend (Referral) completes his first Sale Order after signing up using your referral codes.</p></li></ol>""")
		IrValues.set_default('referral.config.setting', 'home_page_content', """Refer us! To your connections (friend and family) and earn Rewards. Through our Refer and Earn program, you just need to share your auto-generated Unique Referral Code (Referral code will be generated automatically once you sign-up with us) with your connections. Once your referred connections join us using your referral code. You???ll be rewarded by us. You can even track your referrals and the reward earned in the real-time via our personalized dashboard.You spread the word, we will share the wealth.""")
		IrValues.set_default('referral.config.setting', 'mail_subject', """Referral Link to Earn Rewards ({{reward_amt}}) - {{website_name}} """)
		IrValues.set_default('referral.config.setting', 'mail_body', """<p>Hi,</p><p>I???d like to introduce you to ???{{website_name}}'.</p><p>Join it with my Referral Code ???{{referral_code}}??? (or) Referral link to earn Rewards '{{reward_amt}}'.</p><p>Referral Link : {{signup_link}}</p><p>Thanks,</p><p>Your Regards,<br></p><p>{{user_name}}</p>""")

	@api.multi
	def open_landing_page_content(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Configure Landing Page Content',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'wizard.landing.content',
			'target': 'new',
		}


	@api.multi
	def open_how_it_work_content(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Configure How it work ?',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'wizard.how.it.work',
			'target': 'new',
		}

	@api.multi
	def open_wizard_mail_template(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Configure Mail Template',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'wizard.mail.template',
			'target': 'new',
		}



class WizardLanding(models.TransientModel):
	_name = 'wizard.landing.content'

	landing_content = fields.Html(string="Landing Page Content",
		default=lambda self: self.env['ir.values'].get_default('referral.config.setting', 'home_page_content'))

	def modify(self):
		ir_values_obj = self.env['ir.values']
		ir_values_obj.set_default('referral.config.setting', 'home_page_content', self.landing_content)



class WizardHowItWork(models.TransientModel):
	_name = 'wizard.how.it.work'

	how_it_works_content = fields.Html(string="How it Works?",
		default=lambda self: self.env['ir.values'].get_default('referral.config.setting', 'how_it_works_content') )

	def modify(self):
		ir_values_obj = self.env['ir.values']
		ir_values_obj.set_default('referral.config.setting', 'how_it_works_content', self.how_it_works_content)


class WizardMailTemplate(models.TransientModel):
	_name = 'wizard.mail.template'

	def _getDefaultSubject(self):
		return self.env['ir.values'].get_default('referral.config.setting', 'mail_subject') or "subject"


	def _getDefaultBody(self):
		return self.env['ir.values'].get_default('referral.config.setting', 'mail_body') or "body"

	mail_subject = fields.Text(string="Mail Subject",default=_getDefaultSubject,required="1" )
	mail_body = fields.Html(string="Mail Body",default=_getDefaultBody,required="1")

	def modify(self):
		IrValues = self.env['ir.values'].sudo()
		IrValues.set_default('referral.config.setting', 'mail_subject', self.mail_subject)
		IrValues.set_default('referral.config.setting', 'mail_body', self.mail_body)
