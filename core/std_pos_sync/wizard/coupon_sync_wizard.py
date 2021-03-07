from odoo import fields, models,api
from odoo.tools.translate import _
from datetime import datetime
#import xmlrpc.client
import xmlrpclib
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

class CouponSyncWizard(models.TransientModel):
    _name = 'coupon.sync.wizard'
    
    # Sync from Master to Client
    @api.multi
    def action_coupon_sync(self):
        master_url = self.env.ref('std_pos_sync.master_url').value
        database_name = self.env.ref('std_pos_sync.database_name').value
        company_name = self.env.ref('std_pos_sync.company_name').value
        username = self.env.ref('std_pos_sync.username').value
        password = self.env.ref('std_pos_sync.password').value        
        
        sock_common_url = master_url + 'xmlrpc/common'
        sock_url = master_url + 'xmlrpc/object'
        sock_common = xmlrpclib.ServerProxy(sock_common_url)
        uid = sock_common.login(database_name, username, password)
        status = 'Success'
        if uid:
            status = 'Success'
        else:
            status = 'Failed'
            raise UserError("Can't connection to server.")
        sock = xmlrpclib.ServerProxy(sock_url)
        
        coupon_pool = self.env['gift.coupon.pos']
        synclog_pool = self.env['gift.coupon.pos.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'gift.coupon.pos')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'gift.coupon.pos')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'gift.coupon.pos','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                coupon_obj = coupon_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
                logline_ids = sock.execute(database_name, uid, password, 'auditlog.log.line','search',[('log_id', '=', log_id)])
                vals = {}
                for logline_id in logline_ids:
                    logline_data = sock.execute(database_name, uid, password, 'auditlog.log.line','read',logline_id,['field_name','new_value_text','new_value'])
                    field_id = sock.execute(database_name, uid, password, 'ir.model.fields','search',[('model_id', '=', con_model_id[0]),('name', '=', logline_data[0]['field_name'])])
                    field_data = sock.execute(database_name, uid, password, 'ir.model.fields','read',field_id[0],['ttype'])
                    if field_data[0]['ttype'] == 'many2one':
                        if logline_data[0]['new_value_text']:
                            if logline_data[0]['field_name'] == 'voucher':
                                many2one_id = int((logline_data[0]['new_value_text'].split(',')[0]).rsplit('(')[1])
                                voucher_sync_name = sock.execute(database_name, uid, password, 'gift.voucher.pos','read',many2one_id,['pos_sync_id'])
                                voucher_id = self.env['gift.voucher.pos'].search([('pos_sync_id', '=', voucher_sync_name[0]['pos_sync_id'])])
                                if voucher_id:
                                    vals.update({'voucher':voucher_id and voucher_id.id or False})
                    elif field_data[0]['ttype'] in ['many2many','one2many']:
                        if logline_data[0]['new_value_text']:
                            if logline_data[0]['field_name'] == 'partner_id' and logline_data[0]['new_value']:
                                new_value = logline_data[0]['new_value'][1:-1]
                                if new_value:
                                    many2many_ids = new_value.split(',')
                                    partner_ids = []
                                    for many2many_id in many2many_ids:
                                        partner_sync_name = sock.execute(database_name, uid, password, 'res.partner','read',int(many2many_id),['pos_sync_id'])
                                        partner_id = self.env['res.partner'].search([('pos_sync_id', '=', partner_sync_name[0]['pos_sync_id'])])
                                        partner_ids.append(partner_id.id)
                                    if partner_ids:
                                        vals.update({'partner_id': [( 6, 0, partner_ids)]})
                    else:
                        vals.update({logline_data[0]['field_name']: logline_data[0]['new_value_text']})
                if log_data[0]['method'] == 'write':
                    if coupon_obj:
                        coupon_obj.write(vals)
                if log_data[0]['method'] == 'create':
                    if not coupon_obj:
                        coupon_id = coupon_pool.create(vals)
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
        
        
    # Sync from Client To Master    
    @api.multi
    def action_coupon_sync_to_master(self):
        master_url = self.env.ref('std_pos_sync.master_url').value
        database_name = self.env.ref('std_pos_sync.database_name').value
        company_name = self.env.ref('std_pos_sync.company_name').value
        username = self.env.ref('std_pos_sync.username').value
        password = self.env.ref('std_pos_sync.password').value        
        
        sock_common_url = master_url + 'xmlrpc/common'
        sock_url = master_url + 'xmlrpc/object'
        sock_common = xmlrpclib.ServerProxy(sock_common_url)
        uid = sock_common.login(database_name, username, password)
        status = 'Success'
        if uid:
            status = 'Success'
        else:
            status = 'Failed'
            raise UserError("Can't connection to server.")
        sock = xmlrpclib.ServerProxy(sock_url)
        
        synclog_pool = self.env['master.gift.coupon.pos.sync.log']
        auditlog_pool = self.env['auditlog.log']
        coupon_pool = self.env['gift.coupon.pos']
        con_model_id = self.env['ir.model'].search([('model', '=', 'gift.coupon.pos')],limit=1)
        
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = auditlog_pool.search([('create_date', '>', last_sync_date),('model_id', '=', con_model_id.id)])
        else:
            latest_auditlogs = auditlog_pool.search([('model_id', '=', con_model_id.id)])
        
        
        for log_id in latest_auditlogs:
            coupon_obj = coupon_pool.browse(log_id.res_id)
            if coupon_obj:
                master_coupon_id = sock.execute(database_name, uid, password, 'gift.coupon.pos','search',[('pos_sync_id', '=', coupon_obj.pos_sync_id)])
                vals = {}
                for logline_id in log_id.line_ids:
                    if logline_id.new_value_text:
                        if logline_id.field_id.ttype == 'many2one':
                            if logline_id.field_name == 'voucher':
                                master_voucher_id = sock.execute(database_name, uid, password, 'gift.voucher.pos','search',[('pos_sync_id', '=', coupon_obj.voucher.pos_sync_id)])
                                if master_voucher_id:
                                    vals.update({'voucher': master_voucher_id[0]})
                        elif logline_id.field_id.ttype in ['many2many','one2many']:
                            if logline_id.field_name == 'partner_id' and logline_id.new_value:
                                new_value = logline_id.new_value[1:-1]
                                if new_value:
                                    many2many_ids = new_value.split(',')
                                    partner_ids = []
                                    for many2many_id in many2many_ids:
                                        partner_obj = self.env['res.partner'].browse(int(many2many_id))
                                        master_partner_id = sock.execute(database_name, uid, password, 'res.partner','search',[('pos_sync_id', '=', partner_obj.pos_sync_id)])
                                        if master_partner_id:
                                            partner_ids.append(master_partner_id[0])
                                    if partner_ids:
                                        vals.update({'partner_id': [( 6, 0, partner_ids)]})
                                
                        else:
                            vals.update({logline_id.field_name: logline_id.new_value_text})
                if log_id.method == 'write':
                    if master_coupon_id:
                        sock.execute(database_name, uid, password, 'gift.coupon.pos','write',master_coupon_id[0],vals)
                if log_id.method == 'create':
                    if not master_coupon_id:
                        sock.execute(database_name, uid, password, 'gift.coupon.pos','create',vals)
                        
                                
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
