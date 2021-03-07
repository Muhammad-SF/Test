from odoo import fields, models,api
from odoo.tools.translate import _
from datetime import datetime
#import xmlrpc.client
import xmlrpclib
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

class VoucherSyncWizard(models.TransientModel):
    _name = 'voucher.sync.wizard'
    
    
    @api.multi
    def action_voucher_sync(self):
        
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
        
        voucher_pool = self.env['gift.voucher.pos']
        synclog_pool = self.env['gift.voucher.pos.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'gift.voucher.pos')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'gift.voucher.pos')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'gift.voucher.pos','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                voucher_obj = voucher_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
                logline_ids = sock.execute(database_name, uid, password, 'auditlog.log.line','search',[('log_id', '=', log_id)])
                vals = {}
                for logline_id in logline_ids:
                    logline_data = sock.execute(database_name, uid, password, 'auditlog.log.line','read',logline_id,['field_name','new_value_text','new_value'])
                    field_id = sock.execute(database_name, uid, password, 'ir.model.fields','search',[('model_id', '=', con_model_id[0]),('name', '=', logline_data[0]['field_name'])])
                    field_data = sock.execute(database_name, uid, password, 'ir.model.fields','read',field_id[0],['ttype'])
                    if field_data[0]['ttype'] == 'many2one':
                        if logline_data[0]['new_value_text']:
                            many2one_data = logline_data[0]['new_value_text']
                    elif field_data[0]['ttype'] in ['many2many','one2many']:
                        if logline_data[0]['new_value_text']:
                            if logline_data[0]['field_name'] == 'product_categ' and logline_data[0]['new_value']:
                                new_value = logline_data[0]['new_value'][1:-1]
                                if new_value:
                                    many2many_ids = new_value.split(',')
                                    product_categ_ids = []
                                    for many2many_id in many2many_ids:
                                        pos_ctage_name = sock.execute(database_name, uid, password, 'pos.category','read',int(many2many_id),['name'])
                                        product_categ = self.env['pos.category'].search([('name', '=', pos_ctage_name[0]['name'])])
                                        product_categ_ids.append(product_categ.id)
                                    if product_categ_ids:
                                        vals.update({'product_categ': [( 6, 0, product_categ_ids)]})
                            if logline_data[0]['field_name'] == 'product_id' and logline_data[0]['new_value']:
                                new_value = logline_data[0]['new_value'][1:-1]
                                if new_value:
                                    many2many_ids = new_value.split(',')
                                    product_ids = []
                                    for many2many_id in many2many_ids:
                                        product_name = sock.execute(database_name, uid, password, 'product.product','read',int(many2many_id),['name'])
                                        if product_name:
                                            product_id = self.env['product.product'].search([('name', '=', product_name[0]['name'])])
                                            product_ids.append(product_id.id)
                                    if product_ids:
                                        vals.update({'product_id': [( 6, 0, product_ids)]})
                    else:
                        vals.update({logline_data[0]['field_name']: logline_data[0]['new_value_text']})
                if log_data[0]['method'] == 'write':
                    if voucher_obj:
                        voucher_obj.write(vals)
                if log_data[0]['method'] == 'create':
                    voucher_id = voucher_pool.create(vals)
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
