# -*- encoding: utf-8 -*-

import odoo
import odoo.modules.registry
import ast

from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home

import datetime
import json
import pytz
import os
from odoo.addons.website_payment.controllers.main import WebsitePayment
from odoo.addons.online_school_enrollment.controllers.main import AdminRegister
import logging

_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# OpenERP Web web Controllers
#----------------------------------------------------------

class WebsitePayment(WebsitePayment):

    @http.route(['/website_payment/transaction'], type='json', auth="public", website=True)
    def transaction(self, reference, amount, currency_id, acquirer_id):
        res = super(WebsitePayment, self).transaction(reference=reference, amount=amount, currency_id=currency_id, acquirer_id=acquirer_id)
        ref = reference[reference.rfind('-')+1:]
        is_student_id =  any(char.isdigit() for char in ref)
        if is_student_id and not reference.startswith('INV/'):        
            pay_tra_id = request.env['payment.transaction'].sudo().browse(res)
            pay_tra_id.student_id = ref
        return res

    @http.route(['/website_payment/confirm'], type='http', auth='public', website=True)
    def confirm(self, **kw):
        tx_id = request.session.pop('website_payment_tx_id', False)
        values = {'tx_id':tx_id, 'without_paypal':False}
        if tx_id:
            tx = request.env['payment.transaction'].sudo().browse(tx_id)
            status = (tx.state == 'done' and 'success') or 'danger'
            message = (tx.state == 'done' and _('Your payment was successful! It may take some time to be validated on our end.')) or _('Oops! There was a problem with your payment.')
            return request.render('online_school_enrollment.thanks', values)
        else:
            return request.render('online_school_enrollment.thanks', values)

class AdminRegister(AdminRegister):

    @http.route(['/admission/register/create'], type='http', auth="public", website=True, csrf=False)
    def admission_register_create(self, **post):
        vals = {}
        values = {}
        parent_vals = {}
        previous_school_vals = {}
        family_detail_vals = {}
        if post:
            student_parent_id = False
            dob = False
            if post.get('dob',False):
                dob = datetime.datetime.strptime(str(post.get('dob',False)), "%m/%d/%Y").strftime('%m/%d/%Y')
            admission_date = datetime.datetime.strptime(str(datetime.datetime.today().date()), "%Y-%m-%d").strftime('%m/%d/%Y')
            pid = request.env['ir.sequence'].sudo().next_by_code('student.student')
            # if post.get('first_name',False):
            #     first_name = post.get('first_name').split(' ')
            #     middle = ''
            #     first = ''
            #     last = ''
            #     first = first_name and first_name[0] or ''
            #     middle = first_name and len(first_name) == 2 and first_name[1] or ''
            #     last = first_name and len(first_name) == 3 and first_name[2] or ''
            vals.update({
                'pid':pid,
                'name': post.get('first_name',False) or '',
                # 'middle': str(middle) or '',
                # 'last': str(last) or '',
                'gender': post.get('gender',False),
                'school_id':post.get('school_ids',False) and int(post.get('school_ids',False)),
                'standard_id':post.get('standard_ids',False) and int(post.get('standard_ids',False)),
                'year':post.get('year_ids',False) and int(post.get('year_ids',False)),
                'street':post.get('address1',False),
                'street2':post.get('address2',False),
                'city':post.get('city',False),
                'state_id':post.get('state_ids',False) and int(post.get('state_ids',False)),
                'zip':post.get('zip',False),
                'country_id':post.get('country_ids',False) and int(post.get('country_ids',False)),
                'phone':post.get('phone',False),
                'mobile':post.get('mobile',False),
                'email':post.get('email',False),
                'website':post.get('website',False),
                'date_of_birth':dob,
                'admission_date':admission_date,
                'contact_phone1':post.get('phone_no',False),
                'contact_mobile1':post.get('mobile_no',False),
                'maritual_status': post.get('marital_status',False),
                'remark': post.get('qualification_remark',False),
                'mother_tongue': post.get('mother_tongue_ids',False) and int(post.get('mother_tongue_ids',False)),
                'active':True,
                })
            already_student_id = request.env['student.student'].sudo().search([
                ('email','=',post.get('email',False)),
                ('mobile','=',post.get('mobile',False)),
                ('phone','=',post.get('phone',False)),
                ('date_of_birth','=',dob),
                ('contact_phone1','=',post.get('phone_no',False)),
                ('contact_mobile1','=',post.get('mobile_no',False)),
                ('active','=',True),
                ],limit=1)
            student_register_id = False
            if not already_student_id:
                student_register_id = request.env['student.student'].sudo().create(vals)
                student_register_id.active = True            
            # Student Payment Detail
            if post.has_key('payment_option') and post.get('payment_option',False) != 'manually':
                if post.get('school_ids',False) and int(post.get('school_ids',False)) and (already_student_id or student_register_id):
                    self.send_student_mail(already_student_id or student_register_id)
                    school_ids = post.get('school_ids',False) and int(post.get('school_ids',False))
                    school_browse_ids = request.env['school.school'].sudo().browse(school_ids)
                    amount = 0
                    if school_browse_ids.application_fee_id:
                        env = request.env
                        user = env.user.sudo()
                        currency_id = user.company_id.currency_id.id
                        country_id = user.company_id.country_id.id
                        for line in school_browse_ids.application_fee_id.line_ids:
                            if line.type == 'application_fee':
                                values.update({'amount':line.amount,'name': line.name})
                        reference = (already_student_id and already_student_id.name +'-'+ school_browse_ids.name + '-' + str(already_student_id.id)) or (student_register_id.name +'-'+ school_browse_ids.name + '-' + str(student_register_id.id))
                        amount = values.get('amount', False)
                        partner_id = False
                        acquirer_id = False
                        partner_id = already_student_id and already_student_id.user_id.partner_id.id or student_register_id.user_id.partner_id.id
                        currency = env['res.currency'].browse(currency_id)
                        # Try default one then fallback on first
                        acquirer_id = acquirer_id and int(acquirer_id) or \
                            env['ir.values'].get_default('payment.transaction', 'acquirer_id', company_id=user.company_id.id) or \
                            env['payment.acquirer'].search([('website_published', '=', True), ('company_id', '=', user.company_id.id)])[0].id
                        acquirer = env['payment.acquirer'].with_context(submit_class='btn btn-primary pull-right',
                                                                        submit_txt=_('Pay Now')).browse(acquirer_id)
                        # auto-increment reference with a number suffix if the reference already exists
                        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        payment_form = acquirer.sudo().render(reference, float(amount), currency.id, values={'return_url': '/website_payment/confirm', 'partner_id': partner_id})
                        
                        values = {
                            'reference': reference,
                            'acquirer': acquirer,
                            'currency': currency,
                            'amount': float(amount),
                            'payment_form': payment_form,
                            'partner_id':partner_id or False,
                            'student_register_id': student_register_id,
                            'student_id':already_student_id and already_student_id.id or student_register_id.id,
                        }
                        return request.render('school_enrolment_paypal.admission_payment', values)
                    else:
                        return request.render('website.404')
            else:
                self.send_student_mail(already_student_id or student_register_id)
                values.update({'tx_id':student_register_id.id, 'without_paypal':True})
                return request.render("online_school_enrollment.thanks", values)         
        return request.render('website.404')
