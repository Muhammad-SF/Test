from odoo import models, fields, api

class account_asset(models.Model):
    _inherit ='account.asset.asset'

    branch_id   = fields.Many2one('res.branch','Branch',required=True)

class payment_term_line(models.Model):
        _inherit ='account.payment.term.line'

        option = fields.Selection([
            ('day_after_invoice_date', 'Day(s) after the invoice date'),
            ('fix_day_following_month', 'Day(s) after the end of the invoice month (Net EOM)'),
            ('fix_day_following_week', 'Day(s) after the end of the invoice Week (Net EOM)'),
            ('last_day_following_month', 'Last day of following month'),
            ('last_day_current_month', 'Last day of current month')])

class purchase_request(models.Model):
    _inherit= 'purchase.request'

    branch_id = fields.Many2one('res.branch',required=True)

class pos_config(models.Model):
    _inherit='pos.config'

    branch_id = fields.Many2one('res.branch', required=True)