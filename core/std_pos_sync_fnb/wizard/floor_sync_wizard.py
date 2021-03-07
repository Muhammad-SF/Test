from odoo import fields, models,api
from odoo.tools.translate import _
from datetime import datetime
#import xmlrpc.client
import xmlrpclib
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

class FloorSyncWizard(models.TransientModel):
    _name = 'floor.sync.wizard'
    
    
    @api.multi
    def action_floor_sync(self):
        
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
        
        floor_pool = self.env['restaurant.floor']
        synclog_pool = self.env['floor.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'restaurant.floor')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'restaurant.floor')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'restaurant.floor','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                floor_obj = floor_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
                logline_ids = sock.execute(database_name, uid, password, 'auditlog.log.line','search',[('log_id', '=', log_id)])
                vals = {}
                for logline_id in logline_ids:
                    logline_data = sock.execute(database_name, uid, password, 'auditlog.log.line','read',logline_id,['field_name','new_value_text'])
                    field_id = sock.execute(database_name, uid, password, 'ir.model.fields','search',[('model_id', '=', con_model_id[0]),('name', '=', logline_data[0]['field_name'])])
                    field_data = sock.execute(database_name, uid, password, 'ir.model.fields','read',field_id[0],['ttype'])
                    if field_data[0]['ttype'] == 'many2one':
                        if logline_data[0]['new_value_text']:
                            if logline_data[0]['field_name'] == 'pos_config_id':
                                many2one_id = int((logline_data[0]['new_value_text'].split(',')[0]).rsplit('(')[1])
                                pos_config_name = sock.execute(database_name, uid, password, 'pos.config','read',many2one_id,['name'])
                                pos_config_id = self.env['pos.config'].search([('name', '=', pos_config_name[0]['name'])])
                                if pos_config_id:
                                    vals.update({'pos_config_id':pos_config_id and pos_config_id.id or False})
                    elif field_data[0]['ttype'] in ['many2many','one2many']:
                        if logline_data[0]['new_value_text']:
                            many2many_data = logline_data[0]['new_value_text']
                    else:
                        vals.update({logline_data[0]['field_name']: logline_data[0]['new_value_text']})
                if log_data[0]['method'] == 'write':
                    if floor_obj:
                        floor_obj.write(vals)
                if log_data[0]['method'] == 'create':
                    if not floor_obj:
                        floor_id = floor_pool.create(vals)
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
        
        
        
