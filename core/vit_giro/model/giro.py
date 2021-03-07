# -*- coding: utf-8 -*-
# Part of eComBucket. See LICENSE file for full copyright and licensing details
import logging
import time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)

# from openerp import tools
# from openerp.osv import fields, osv
# import openerp.addons.decimal_precision as dp
# import time
# import logging
# from openerp.tools.translate import _
# from openerp import api

_logger = logging.getLogger(__name__)
STATES = [('draft', 'Draft'), ('open', 'Open'), ('close', 'Close'), ('reject', 'Reject')]


class vit_giro(models.Model):
    _name = 'vit.giro'
    _rec_name = 'name'
    _description = 'Giro'
    
    @api.depends('giro_invoice_ids')
    def _get_invoices(self):
        for giro in self:
            giro.invoice_names = " ".join((self.giro_invoice_ids.mappped('invoice_id.number') or []))
          
    name = fields.Char('Number', help='Nomor Giro', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    due_date = fields.Date('Due Date', help='', readonly=True, states={'draft': [('readonly', False)]})
    receive_date = fields.Datetime('Receive Date', help='', readonly=True,
                                    states={'draft': [('readonly', False)]})
    clearing_date = fields.Datetime('Clearing Date', help='', readonly=True,
                                     states={'draft': [('readonly', False)]})
    amount = fields.Float('Amount', help='', readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Partner', help='', readonly=True,
                                  states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Bank Journal', domain=[('type', '=', 'bank')], help='',
                                  readonly=True, states={'draft': [('readonly', False)]})
    giro_invoice_ids = fields.One2many('vit.giro_invioce', 'giro_id', readonly=True,
                                        states={'draft': [('readonly', False)]})
    invoice_names = fields.Char(computre = _get_invoices, string="Allocated Invoices")
    type = fields.Selection([
        ('payment', 'Payment'),
        ('receipt', 'Receipt')],
        "Type",
        required=True, readonly=True, states={'draft': [('readonly', False)]}, default='payment')
    invoice_type = fields.Char('Invoice Type', readonly=True, states={'draft': [('readonly', False)]}, default='in_invoice')
    state = fields.Selection(string="State", selection=STATES, required=True, readonly=True, default='draft')

    _sql_constraints = [('name_uniq', 'unique(name)', _('Nomor Giro tidak boleh sama'))]
    
    # def _cek_total(self):
    #     inv_total = 0.0
    #     for giro in self.browse(cr, uid, ids, context=context):
    #         for gi in giro.giro_invoice_ids:
    #             inv_total += gi.amount
            
    #         if giro.amount == inv_total:
    #             return True
        
    #     return False
    
    # _constraints = [(_cek_total, _('Total amount allocated for the invoices must be the same as total Giro amount'),
    #                  ['amount', 'giro_invoice_ids'])]
    
    # _defaults = {
    #     'state': STATES[0][0],
    #     'receive_date': time.strftime("%Y-%m-%d %H:%M:%S"),
    #     'type': 'payment',
    #     'inv_type': 'in_invoice',
    # }
    
    @api.multi
    def action_cancel(self):
        data = {'state': STATES[0][0]}
        self.write(data)
    
    @api.multi
    def action_confirm(self):
        data = {'state': STATES[1][0]}
        self.write(data)
    
    @api.multi
    def action_clearing(self):
        
        voucher_obj = self.env['account.voucher']
        u1 = self.env.user
        company_id = u1.company_id.id
        
        for giro in self:
            for gi in giro.giro_invoice_ids:
                invoice_id = gi.invoice_id
                partner_id = giro.partner_id.id
                amount = gi.amount
                journal_id = giro.journal_id
                type = giro.type
                name = giro.name
                vid = voucher_obj.create_payment(invoice_id, partner_id, amount, journal_id, type, name,
                                                 company_id)
                vid.payment_confirm()
        data = {'state': STATES[2][0],
                'clearing_date': time.strftime("%Y-%m-%d %H:%M:%S")}
        self.write(data)
    
    @api.multi
    def action_reject(self):
        data = {'state': STATES[3][0]}
        self.write(data)
    
    @api.onchange('type')
    def on_change_type(self):
        inv_type = 'in_invoice'
        if self.type == 'payment':
            inv_type = 'in_invoice'
        elif self.type == 'receipt':
            inv_type = 'out_invoice'
        self.invoice_type = inv_type


class vit_giro_invoice(models.Model):
    _name = 'vit.giro_invioce'
    _description = 'Giro vs Invoice'
    giro_id =  fields.Many2one('vit.giro', 'Giro', help='')
    invoice_id =  fields.Many2one('account.invoice', 'Invoice',
                                  help='Invoice to be paid',
                                  domain=[('state', '=', 'open')])
    # amount_invoice =  fields.related("invoice_id", "residual",
    #             relation="account.invoice",
    #             type="float", string="Invoice Amount", store=True)
    amount_invoice =  fields.Float('Invoice Amount')
    amount =  fields.Float('Amount Allocated')
    
    
    @api.onchange('invoice_id')
    def on_change_invoice_id(self):
        self.amount_invoice = self.invoice_id.residual


class account_invoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    giro_invoice_ids = fields.One2many('vit.giro_invioce', 'invoice_id', string="Giro")
