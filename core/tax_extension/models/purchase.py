from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            inc_tax = 0.0
            exl_tax = 0.0
            round_curr = order.currency_id.round
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                if line.taxes_id:
                    for tax in line.taxes_id:
                        if tax.price_include_total:
                            in_tax_amount = tax.with_context(base_values=(line.price_subtotal, line.price_subtotal, line.price_subtotal)).compute_all(line.price_subtotal, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
                            tax_amt = sum(t.get('amount', 0.0) for t in in_tax_amount.get('taxes', []))
                            inc_tax += round_curr(tax_amt)
                            amount_tax += round_curr(tax_amt)
                        else:
                            price = line.price_unit
                            if tax.price_include:
                                ex_tax_amount = tax.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
                                tax_amt = sum(t.get('amount', 0.0) for t in ex_tax_amount.get('taxes', []))
                                exl_tax +=round_curr(tax_amt)
                                amount_tax += round_curr(tax_amt)
                            else:
                                ex_tax_amount = tax.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
                                tax_amt = sum(t.get('amount', 0.0) for t in ex_tax_amount.get('taxes', []))
                                exl_tax +=round_curr(tax_amt)
                                amount_tax += round_curr(tax_amt)
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + exl_tax - abs(inc_tax),
                'ppn':("""%s""") % (exl_tax),
                'pph':("""%s""") % (inc_tax)
            })

    ppn = fields.Html(string='PPN',readonly=True, compute='_amount_all')
    pph = fields.Html(string='PPH',readonly=True, compute='_amount_all')
