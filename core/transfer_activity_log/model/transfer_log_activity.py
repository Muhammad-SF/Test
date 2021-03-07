from odoo import fields, models, api


class TransferLogActivity(models.Model):
    _name = 'transfer.log.activity'
    _description = 'Transfer Log Activity'
    _rec_name = 'reference'


    timestamp = fields.Datetime('Timestamp', readonly=True)
    status = fields.Char('Status', readonly=True)
    user = fields.Many2one('res.users','User', readonly=True)
    reference = fields.Many2one('stock.picking','Reference',readonly=True)
    process_time = fields.Char(string="Process Time")

class TransferLogActivity(models.Model):
    _name = 'transfer.activity.log'
    _description = 'Transfer Log Activity'
    _rec_name = 'reference'

    reference = fields.Many2one('stock.picking', string='Reference', readonly=True)
    origin = fields.Char('Source Document', readonly=True)
    timestamp = fields.Datetime('Timestamp', readonly=True)
    status = fields.Char('Status', readonly=True)
    user = fields.Char('User', readonly=True)
    company_id = fields.Many2one(related='reference.company_id', string="Company", readonly=True)
    location = fields.Char('Source Location', readonly=True)
    location_dest = fields.Char('Destination Location', readonly=True)
    customer = fields.Many2one(related="reference.partner_id", string='Customer', readonly=True)
    vendor = fields.Many2one(related="reference.partner_id", string='Vendor', readonly=True)
    process_time = fields.Char(string='Processed Time', readonly=True)
    days = fields.Float(string='Processed Days', readonly=True)
    hours_minutes = fields.Char()
    mail_track_id = fields.Many2one('mail.tracking.value')
    mail_id = fields.Many2one('mail.message')
    picking_name = fields.Char('Picking Name')

    @api.model
    def create_transfer_log_existing_picking(self):
        transfer_obj = self.env['transfer.activity.log']
        stock_picking_obj = self.env['stock.picking']
        query = """
                select 
                    tv.id as tracking_id,
                    sp.id as picking_id,
                    mm.id as message_id,
                    sp.origin as picking_origin,
                    mm.create_date::timestamp(0) as mail_create_date,
                    part.name as author_name,
                    tv.new_value_char,
                    tv.old_value_char,
                    pick_part.name as picking_partner_name,
                    comp.name as company_name
                from 
                    mail_tracking_value tv
                    left join mail_message mm on (mm.id = tv.mail_message_id)
                    left join stock_picking sp on (sp.id = mm.res_id)
                    left join res_partner part on (part.id = mm.author_id)
                    left join res_partner pick_part on (pick_part.id = sp.partner_id)
                    left join res_company comp on (comp.id = sp.company_id)
                where 
                    tv.field='state' and 
                    mm.model='stock.picking' and
                    tv.id not in (select mail_track_id from transfer_activity_log group by mail_track_id)
                order by 
                    sp.id,tv.id
                """
        self._cr.execute(query)
        query_fetch_data = self._cr.dictfetchall()
        log_mail_id_list = {}
        for tracking_value in query_fetch_data:
            picking_id = tracking_value.get('picking_id')
            message_id = tracking_value.get('message_id')
            tracking_new_value = tracking_value.get('new_value_char') or ''
            mail_create_date = tracking_value.get('mail_create_date')
            picking = stock_picking_obj.browse(tracking_value.get('picking_id'))

            old_data = transfer_obj.search([('reference', '=', picking_id)], order='id desc', limit=1)

            days = 0
            hours = 0
            minutes = 0
            seconds = 0
            if tracking_new_value != 'Draft' and old_data:
                old_timestamp = datetime.strptime(old_data.mail_id.create_date, DTF)
                new_timestamp = datetime.strptime(mail_create_date, DTF)
                process_time = new_timestamp - old_timestamp
                days, seconds = process_time.days, process_time.seconds
                minutes, seconds = divmod(seconds, 60)
                hours, minutes = divmod(minutes, 60)

            process_time = str(days) + ' Days ' + str(hours) + ' Hours ' + str(minutes) + ' Minutes'
            hours1 = hours + (days * 24)
            minutes1 = (hours1 * 60) + minutes
            seconds1 = (minutes1 * 60) + seconds
            hours1 = hours1 < 10 and '0' + str(hours1) or hours1
            minutes = minutes < 10 and '0' + str(minutes) or minutes
            seconds = seconds < 10 and '0' + str(seconds) or seconds
            if not transfer_obj.search([('mail_id', '=', message_id)]):
                transfer_obj.create({
                    'origin': tracking_value.get('picking_origin') or '',
                    'timestamp': mail_create_date,
                    'user': tracking_value.get('author_name'),
                    'status': tracking_new_value,
                    'location': picking and picking.location_id.display_name,
                    'location_dest': picking and picking.location_dest_id.display_name,
                    'customer': tracking_value.get('picking_partner_name') or ' ',
                    'vendor': tracking_value.get('picking_partner_name') or ' ',
                    'days': round(seconds1 / 86400.00, 2),
                    'hours_minutes': str(hours1 or 00) + ':' + str(minutes or 00) + ':' + str(seconds or 00),
                    'process_time': process_time,
                    'company_id': tracking_value.get('company_id'),
                    'mail_track_id': tracking_value.get('tracking_id'),
                    'mail_id': message_id,
                    'picking_name': picking.picking_name,
                    'reference': picking_id or False
                    })
        return True