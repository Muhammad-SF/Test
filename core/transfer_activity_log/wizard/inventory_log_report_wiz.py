# -*- coding: utf-8 -*-
##############################################################################
#
#    Laxicon Solution(Odoo Expert)
#    Copyright (C) 2015 Laxicon Soluation (<http://laxicon.in/>)
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import ValidationError
from io import BytesIO
import base64

try:
    import xlwt
except ImportError:
    xlwt = None


class DeliveryOrderLogActivityWizard(models.TransientModel):

    _name = 'transfer.activity.log.wiz'
    _description = 'Activity Log Wizard'

    def default_location_dest(self):
        customerloc = False
        if 'default_picking_name' in self._context and self._context.get('default_picking_name') == 'Delivery Orders':
            customerloc = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
        return customerloc

    def default_location(self):
        customerloc = False
        if 'default_picking_name' in self._context and self._context.get('default_picking_name') == 'Receipts':
            customerloc = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
        return customerloc

    def get_comapny_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, required=True, domain=get_comapny_domain)
    customer_ids = fields.Many2many('res.partner', string='Customer', domain=[('customer', '=', True)])
    vendor_ids = fields.Many2many('res.partner', string='Vendor', domain=[('supplier', '=', True)])
    location_ids = fields.Many2many('stock.location', 'transfer_location_rel', 'transfer_id', 'location_id', string='Source Location', default=default_location)
    location_dest_ids = fields.Many2many('stock.location', 'transfer_location_dest_rel', 'transfer_id', 'location_dest_id', string='Destination Location', default=default_location_dest)
    partner_location = fields.Boolean(compute="is_partner_location")
    start_date = fields.Date(string="Start Date", default=(datetime.now()+relativedelta(day=1, months=0)).strftime('%Y-%m-%d'), help="Based on Scheduled Date")
    end_date = fields.Date(string="End Date", default=(datetime.now()+relativedelta(day=1, months=1, days=-1)).strftime('%Y-%m-%d'), help="Based on Scheduled Date")
    datas = fields.Binary('File')
    picking_name = fields.Char("Picking Name")

    @api.multi
    @api.depends('location_dest_ids')
    def is_partner_location(self):
        for res in self:
            loc = res.default_location_dest()
            if loc and loc.id in res.location_dest_ids.ids:
                res.partner_location = True
            else:
                res.partner_location = False

    def get_data(self):
        domain = [('picking_name', '=', self.picking_name), ('company_id', '=', self.company_id.id)]
        if self.start_date:
            domain.append(('create_date', '>', self.start_date))
        if self.end_date:
            domain.append(('create_date', '<', self.end_date))
        if self.customer_ids:
            domain.append(('partner_id', 'in', self.customer_ids.ids))
        if self.vendor_ids:
            domain.append(('partner_id', 'in', self.vendor_ids.ids))
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))
        if self.location_dest_ids:
            domain.append(('location_dest_id', 'in', self.location_dest_ids.ids))
        stock_data = self.env['stock.picking'].search(domain)
        if stock_data:
            data = {}
            transfer_data = self.env['transfer.activity.log'].search([('reference', 'in', stock_data.ids), ('picking_name', '=', self.picking_name)])
            for trans in transfer_data.sorted(key=lambda r: r.id):
                if trans.reference.name not in data:
                    data.update({trans.reference.name: []})
            for key, vals in data.items():
                for trans in transfer_data.sorted(key=lambda r: r.id):
                    if key == trans.reference.name:
                        vals.append({
                                'origin': trans.reference.origin,
                                'timestamp': trans.timestamp,
                                'user': trans.user,
                                'status': trans.status,
                                'location': trans.location,
                                'location_dest': trans.location_dest,
                                'customer': trans.customer,
                                'vendor': trans.vendor,
                                'process_time': trans.process_time
                            })
            return data
        else:
            raise ValidationError(_("There is no data available"))

    def get_location_name(self, location_ids):
        """
        Return warehouse names
            - WH A, WH B...
        """
        location_obj = self.env['stock.location']
        locations = 'ALL'
        if location_ids:
            location_rec = location_obj.search([('id', 'in', location_ids)])
            if location_rec:
                locations = ",".join([x.display_name for x in location_rec])
            else:
                locations = '-'
        return locations

    def get_dest_location_name(self, location_dest_ids):
        """
        Return warehouse names
            - WH A, WH B...
        """
        location_obj = self.env['stock.location']
        locations = 'ALL'
        if location_dest_ids:
            location_rec = location_obj.search([('id', 'in', location_dest_ids)])
            if location_rec:
                locations = ",".join([x.display_name for x in location_rec])
            else:
                locations = '-'
        return locations

    def get_customer_name(self, customer_ids):
        """
        Return warehouse names
            - WH A, WH B...
        """
        partner_obj = self.env['res.partner']
        partners = 'ALL'
        if customer_ids:
            customer_rec = partner_obj.search([('id', 'in', customer_ids)])
            if customer_rec:
                partners = ",".join([x.name for x in customer_rec])
            else:
                partners = '-'
        return partners

    @api.multi
    def print_report(self):
        data = {}
        data['ids'] = self._context.get('active_ids', [])
        data['model'] = self._context.get('active_model', 'ir.ui.menu')
        for record in self:
            data['form'] = self.read(['company_id', 'customer_ids', 'location_ids', 'location_dest_ids', 'start_date', 'end_date', 'picking_name', 'vendor_ids'])[0]
        report_name = 'transfer_activity_log.delivery_log_activity_report'
        if self.picking_name == 'Receipts':
            report_name = 'transfer_activity_log.received_log_activity_report'
        if self.picking_name == 'Internal Transfer IN':
            report_name = 'transfer_activity_log.transfer_in_log_activity_report'
        if self.picking_name == 'Internal Transfer Out':
            report_name = 'transfer_activity_log.transfer_in_log_activity_report'
        return self.env['report'].with_context(landscape=True).get_action(self, report_name, data=data)

    @api.multi
    def print_xls_report(self):
        final_data = self.get_data()
        location = self.get_location_name(self.location_ids.ids)
        location_dest = self.get_dest_location_name(self.location_dest_ids.ids)
        customer = self.vendor_ids.ids
        if self.customer_ids:
            customer = self.customer_ids.ids
        customer = self.get_customer_name(customer)
        picking_name = 'Delivery Order Activity Log'
        if self.picking_name == 'Receipts':
            picking_name = "Receiving Notes Activity Log"
        if self.picking_name == 'Internal Transfer Out':
            picking_name = "Transfer Out Activity Log"
        if self.picking_name == 'Internal Transfer IN':
            picking_name = "Transfer In Activity Log"
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(picking_name, cell_overwrite_ok=True)
        header_bold = xlwt.easyxf("font: bold on")
        header_center = xlwt.easyxf("align: horiz center;font: bold on")
        row = 0
        col = 0
        worksheet.write_merge(row, col, row, col + 5, _(picking_name), header_center)
        row += 2
        col = 0
        worksheet.write(row, col, _("Company"), header_center)
        col += 1
        worksheet.write(row, col, _('Source Location'), header_center)
        col += 1
        worksheet.write(row, col, _("Destination Location"), header_center)
        col += 1
        worksheet.write(row, col, _("Periods"), header_center)
        if self.picking_name == 'Delivery Orders':
            col += 1
            worksheet.write(row, col, _("Customer"), header_center)
        if self.picking_name == 'Receipts':
            col += 1
            worksheet.write(row, col, _("Vendor"), header_center)
        row += 1
        col = 0
        worksheet.write(row, col, self.company_id.name)
        col += 1
        worksheet.write(row, col, location)
        col += 1
        worksheet.write(row, col, location_dest)
        col += 1
        worksheet.write(row, col, str(self.start_date) + ' to ' + str(self.end_date))
        col += 1
        if self.picking_name in ['Delivery Orders', 'Receipts']:
            worksheet.write(row, col, customer)
        row += 2
        col = 0
        worksheet.write(row, col, _("No."), header_bold)
        col += 1
        worksheet.write(row, col, _('Reference'), header_bold)
        col += 1
        worksheet.write(row, col, _("Source Document"), header_bold)
        col += 1
        worksheet.write(row, col, _("Timestamp"), header_bold)
        col += 1
        worksheet.write(row, col, _("User"), header_bold)
        col += 1
        worksheet.write(row, col, _("Status"), header_bold)
        col += 1
        worksheet.write(row, col, _("Processed Time"), header_bold)
        count = 1
        flag = False
        for key, vals in final_data.items():
            row += 1
            col = 0
            worksheet.write(row, col, count)
            col += 1
            if not flag:
                worksheet.write(row, col, key)
                col += 1
                worksheet.write(row, col, vals[0].get('origin') or '')
            else:
                worksheet.write(row, col, _())
                col += 1
                worksheet.write(row, col, _())
            for f in vals:
                col = 3
                worksheet.write(row, col, f.get('timestamp'))
                col += 1
                worksheet.write(row, col, f.get('user'))
                col += 1
                worksheet.write(row, col, f.get('status'))
                col += 1
                worksheet.write(row, col, f.get('process_time'))
                row += 1
            count += 1
            row += 1
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        report_data_file = base64.encodestring(fp.read())
        fp.close()
        self.write({'datas': report_data_file})
        picking_name = picking_name + '.xls'
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=transfer.activity.log.wiz&field=datas&download=true&id=%s&filename=%s' % (self.id, picking_name),
            'target': 'new',
            }
