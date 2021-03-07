import logging
import time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)

# from openerp import tools
# from openerp.osv import fields,osv
# import openerp.addons.decimal_precision as dp
# import time
# import logging
# from openerp.tools.translate import _
# from openerp import netsvc

# _logger = logging.getLogger(__name__)

####################################################################################
# periodic read dari ca_pembayaran
# if exists create payment voucher for the invoice
####################################################################################
class account_voucher(models.Model):
    _name = "account.voucher"
    _inherit = "account.voucher"
    
    ####################################################################################
    # create payment
    # invoice_id: yang mau dibayar
    # journal_id: payment method
    ####################################################################################
    @api.model
    def create_payment(self, inv, partner_id, amount, journal, type, name, company_id):
        voucher_lines = []
        
        # cari move_line yang move_id nya = invoice.move_id
        move_lines = inv.move_id.line_ids
        # raise Warning(move_lines)
        if not len(move_lines):
            raise UserError(_('Please confirm the created invoice firstly then set this to clearing.'))
        move_line = move_lines[0]  # yang AR saja
        #payment supplier
        if type == 'payment':
            line_type = 'dr'
            voucher_type = 'purchase'
            journal_account = journal.default_credit_account_id.id
        #receive customer
        else:
            line_type = 'cr'
            voucher_type = 'sale'
            journal_account = journal.default_debit_account_id.id
            
        line_amount = 0 
        voucher_lines.append((0, 0, {
            'move_line_id': move_line.id,
            'amount_original': line_amount,
            'amount_unreconciled': line_amount,
            'reconcile': True,
            'type': line_type,



            'account_id': move_line.account_id.id,
            'price_unit': amount,
            'name': move_line.name,
            'company_id': company_id
        }))

        voucher_id = self.env['account.voucher'].create({
            'partner_id' : partner_id,
            'account_id'	: journal_account,
            'journal_id'	: journal.id,
            'reference' 	: 'Payment giro ' + name,
            'name' 			: 'Payment giro ' + name,
            'company_id' 	: company_id,
            'voucher_type'	: voucher_type,
            'line_ids'		: voucher_lines
        })
        _logger.info("   created payment id:%d" % (voucher_id) )
        return voucher_id

    
    ####################################################################################
    # set done
    ####################################################################################
        
        
    def payment_confirm(self):
        self.proforma_voucher()
        _logger.info("   confirmed payment id:%d" % (self.id) )
        return True
    
    
    ####################################################################################
    # find invoice by number
    ####################################################################################
    def find_invoice_by_number(self, number):
        return self.env['account.invoice'].search([('number' ,'=', number)])
    
    ####################################################################################
    # find journal by code
    ####################################################################################
    def find_journal_by_code(self, cr, uid, code, context=None):
        return self.env['account.journal'].search([('code' ,'=', code)])
