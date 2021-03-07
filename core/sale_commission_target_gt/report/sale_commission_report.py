# -*- coding: utf-8 -*-

from odoo import models,fields,api,_

class sale_commission_target_gt_report(models.AbstractModel):
    _name = 'report.sale_commission_target_gt.report_sale_commission'

    @api.model
    def render_html(self, docids, data=None):
        advice = self.env['sale.commission.report.wizard'].browse(self.env.context.get('active_id'))
        docargs = {
            'doc_ids': docids,
            'doc_model': 'sale.commission.report.wizard',
            'data': data,
            'docs': advice,
        }
        return self.env['report'].render('sale_commission_target_gt.report_sale_commission', docargs)

class sale_commission_target_detail_gt_report(models.AbstractModel):
    _name = 'report.sale_commission_target_gt.report_sale_commission_detail'

    @api.model
    def render_html(self, docids, data=None):
        advice = self.env['sale.commission.report.wizard'].browse(self.env.context.get('active_id'))
        docargs = {
            'doc_ids': docids,
            'doc_model': 'sale.commission.report.wizard',
            'data': data,
            'docs': advice,
        }
        return self.env['report'].render('sale_commission_target_gt.report_sale_commission_detail', docargs)
