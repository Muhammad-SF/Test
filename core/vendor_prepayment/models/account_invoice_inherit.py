from odoo import models,fields,api,_
from datetime import datetime
from dateutil.relativedelta import relativedelta

class AccountInvoiceInherit(models.Model):
    _inherit='account.invoice'
    
    #vendor_invoice_boolean=fields.Boolean('Customer Invoice Boolean')
    vendor_invoice_boolean=fields.Boolean('Vendor Invoice Boolean')
    period = fields.Integer("Period")
    period_type = fields.Selection([('day','Days'),('month','Month'),('year','Year')],string="Period Type")
    no_of_period = fields.Integer("Number Of Period")
    start_date = fields.Date("Start Date")
    vendor_renewal_boolean = fields.Boolean("Renewal Boolean")
    
    
    def scheduled_invoice_vendor(self):
        for subscription in self.env['account.subscription'].search([('state','=','running')]):
            today = datetime.today()
            today_date = today.strftime('%Y-%m-%d')
            
            start_datetime = today.strftime('%Y-%m-%d %H:%M:%S')
            sch_inv_ids =  subscription.lines_id.search([('move_id','=',None),
                                                        ('subscription_id','=',subscription.id),
                                                        ('date','=',today_date),
                                                    ])
            print("===sch_po_ids===",sch_inv_ids)
            print("=-===order.recurring_schedule_ids===",subscription.lines_id)
            
            
            if sch_inv_ids:
                for sch_line in sch_inv_ids:
                    print("===sch_po_ids==in=",sch_inv_ids)
                    po = self._prepare_move_line_vals(start_datetime,subscription)
                    sch_line.write({'move_id':po.id})
                    subscription.freq_count = subscription.freq_count + 1
            
            print("======subscription.period_total===",subscription.period_total)
            print("======subscription.freq_count===",subscription.freq_count)
            if subscription.freq_count == subscription.period_total:
                subscription.state = "done"


            
    def _prepare_move_line_vals(self, start_datetime, subscription):
        line_list = []
        for sub_line in subscription.model_id.lines_id:
    
            #Create movelines
            vals1 = {'credit':sub_line.credit,
                    'account_id':sub_line.account_id.id,
                     'debit':sub_line.debit,
                    'name':sub_line.name,
                    'partner_id':sub_line.partner_id.id }
   
            line_list.extend(((0,0,vals1),))
        #create move
        move_id = self.env['account.move'].create({'journal_id':subscription.model_id.journal_id.id,
                                         'date':start_datetime,
                                         'ref':subscription.ref,
                                         'line_ids':line_list})
        move_id.post()
        
        return move_id
    @api.model
    def create(self,vals):
        journal=self.env['account.journal'].sudo().search([('name','=','Vendor PrePayment')])
        #update journal of pre payment
        if self._context.get('default_vendor_invoice_boolean')==True:
            vals.update({'journal_id':journal.id,'vendor_invoice_boolean':True})
        return super(AccountInvoiceInherit,self).create(vals)
    
class AccountInvoiceLineInherit(models.Model):
    _inherit='account.invoice.line'
    
    expense_account = fields.Many2one('account.account',string="Expense Account")
    
    
class payment(models.Model):
    _inherit = 'account.payment'
    
    expense_account = fields.Many2one('account.account',string="Expense Account")
    
    
    @api.multi
    def post(self):
        res = super(payment,self).post()
        #Create entry for recurring model
        inv = self.env['account.invoice'].browse(self._context.get('active_id'))
        # if self.payment_difference==self.amount:
        if inv.invoice_line_ids:
                for line in inv.invoice_line_ids[0]:
                    if self.no_of_period and line.account_id and self.expense_account and self.period_type:
                        line_list = []
                        vals1 = {'credit':0.0,
                                 'sequence':0,
                                 'partner_id':inv.partner_id.id,
                                'account_id':self.expense_account.id,
                                 'debit':(self.amount/self.no_of_period),
                                'name':'Payment '+line.name }
                        
                        vals2 = {'credit':(self.amount/self.no_of_period),
                                 'sequence':0,
                                 'partner_id':inv.partner_id.id,
                                'account_id':line.account_id.id,
                                 'debit':0.0,
                                'name':'Payment '+line.name
                          }
                        line_list.extend(((0,0,vals1),(0,0,vals2)))
                        # create account model entry
                        account_model = self.env['account.model'].create({
                                                          'name':'Payment '+line.name,
                                                          'journal_id':inv.journal_id.id,
                                                          'lines_id':line_list})
                        # create account subscription entry
                        subscription_id = self.env['account.subscription'].create({'state':'draft',
                                                                 'name':account_model.name,
                                                                 'model_id':account_model.id,
                                                                 'ref':inv.number,
                                                                 'date_start':self.start_date,
                                                                 'period_total':self.no_of_period,
                                                                 'period_nbr':self.period,
                                                                 'period_type':self.period_type})
                        subscription_id.compute()
