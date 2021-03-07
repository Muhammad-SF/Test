from odoo import api, models, _
from odoo.exceptions import ValidationError


class ReportReceivingLogActivity(models.AbstractModel):
    _name = 'report.transfer_activity_log.received_log_activity_report'

    def get_data(self, data):
        domain = [('picking_name', '=', data['picking_name']), ('company_id', '=', data['company_id'][0])]
        if data['start_date']:
            domain.append(('create_date', '>', data['start_date']))
        if data['end_date']:
            domain.append(('create_date', '<', data['end_date']))
        if data['customer_ids']:
            domain.append(('partner_id', 'in', data['customer_ids']))
        if data['vendor_ids']:
            domain.append(('partner_id', 'in', data['vendor_ids']))
        if data['location_ids']:
            domain.append(('location_id', 'in', data['location_ids']))
        if data['location_dest_ids']:
            domain.append(('location_dest_id', 'in', data['location_dest_ids']))
        stock_data = self.env['stock.picking'].search(domain)
        if stock_data:
            f_data = {}
            transfer_data = self.env['transfer.activity.log'].search([('reference', 'in', stock_data.ids), ('picking_name', '=', data['picking_name'])])
            for trans in transfer_data.sorted(key=lambda r: r.id):
                if trans.reference.name not in f_data:
                    f_data.update({trans.reference.name: []})
            for key, vals in f_data.items():
                for trans in transfer_data.sorted(key=lambda r: r.id):
                    if key == trans.reference.name:
                        vals.append({
                                'origin': trans.reference.origin,
                                'timestamp': trans.timestamp,
                                'user': trans.user,
                                'status': trans.status,
                                'process_time': trans.process_time
                            })
            return f_data
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

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('transfer_activity_log.received_log_activity_report')
        final_data = self.get_data(data['form'])
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'data': data,
            'final_data': final_data,
            'get_location_name': self.get_location_name,
            'get_dest_location_name': self.get_dest_location_name,
            'get_customer_name': self.get_customer_name
            }
        return report_obj.render('transfer_activity_log.received_log_activity_report', docargs)
