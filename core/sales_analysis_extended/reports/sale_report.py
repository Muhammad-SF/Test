from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    brand_id = fields.Many2one('product.brand', 'Brand')
    invoice_numbers_ext = fields.Char(string='Invoices', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', readonly=True)

    def _select(self):
        select_str = super(SaleReport, self)._select()
        select_str += ", t.product_brand_id as brand_id, s.branch_id as branch_id, " \
                      "s.sale_invoice_numbers as invoice_numbers_ext, s.warehouse_id as warehouse_id"
        return select_str

    def _from(self):
        from_str = super(SaleReport, self)._from()
        from_str += """Left Join product_brand brand on brand.id = t.product_brand_id
                       Left Join res_branch branch on branch.id = s.branch_id"""
        return from_str

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        group_by_str += ", t.product_brand_id, s.sale_invoice_numbers, s.warehouse_id, s.branch_id"
        return group_by_str


