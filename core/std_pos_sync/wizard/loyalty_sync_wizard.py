from odoo import fields, models,api
from odoo.tools.translate import _
from datetime import datetime
#import xmlrpc.client
import xmlrpclib
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

class LoyaltySyncWizard(models.TransientModel):
    _name = 'loyalty.sync.wizard'
    
    
    @api.multi
    def action_loyalty_sync(self):
        
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
        
        loyalty_pool = self.env['loyalty.program']
        synclog_pool = self.env['loyalty.program.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'loyalty.program')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'loyalty.program')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'loyalty.program','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                loyalty_obj = loyalty_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
                logline_ids = sock.execute(database_name, uid, password, 'auditlog.log.line','search',[('log_id', '=', log_id)])
                vals = {}
                for logline_id in logline_ids:
                    logline_data = sock.execute(database_name, uid, password, 'auditlog.log.line','read',logline_id,['field_name','new_value_text'])
                    field_id = sock.execute(database_name, uid, password, 'ir.model.fields','search',[('model_id', '=', con_model_id[0]),('name', '=', logline_data[0]['field_name'])])
                    field_data = sock.execute(database_name, uid, password, 'ir.model.fields','read',field_id[0],['ttype'])
                    if field_data[0]['ttype'] == 'many2one':
                        if logline_data[0]['new_value_text']:
                            many2one_data = logline_data[0]['new_value_text']
                    elif field_data[0]['ttype'] in ['many2many','one2many']:
                        if logline_data[0]['new_value_text']:
                            many2many_data = logline_data[0]['new_value_text']
                    else:
                        vals.update({logline_data[0]['field_name']: logline_data[0]['new_value_text']})
                
                # For Rules
                rule_ids = sock.execute(database_name, uid, password, 'loyalty.rule','search',[('loyalty_program_id', '=', log_data[0]['res_id'])])
                rule_vals_list = []
                for rule_id in rule_ids:
                    rule_data = sock.execute(database_name, uid, password, 'loyalty.rule','read',rule_id,['name','rule_type','product_id','pp_product','pp_currency','cumulative','category_id'])
                    rule_vals = {
                        'name': rule_data[0]['name'],
                        'rule_type': rule_data[0]['rule_type'],
                        'pp_product': rule_data[0]['pp_product'],
                        'pp_currency': rule_data[0]['pp_currency'],
                        'cumulative': rule_data[0]['cumulative'],
                    }
                    
                    if rule_data[0]['product_id']:
                        product_data = sock.execute(database_name, uid, password, 'product.product','read',rule_data[0]['product_id'][0],['pos_sync_id'])
                        if product_data:
                            product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                            if product_obj:
                                rule_vals.update({'product_id': product_obj and product_obj.id or False})
                    if rule_data[0]['category_id']:
                        prodcategory_data = sock.execute(database_name, uid, password, 'pos.category','read',rule_data[0]['category_id'][0],['pos_sync_id'])
                        if prodcategory_data:
                            prodcategory_obj = self.env['pos.category'].search([('pos_sync_id','=', prodcategory_data[0]['pos_sync_id'])])
                            if prodcategory_obj:
                                rule_vals.update({'category_id': prodcategory_obj and prodcategory_obj.id or False})
                    rule_vals_list.append(rule_vals)
                    
                # For Rewards
                reward_ids = sock.execute(database_name, uid, password, 'loyalty.reward','search',[('loyalty_program_id', '=', log_data[0]['res_id'])])
                reward_vals_list = []
                for reward_id in reward_ids:
                    reward_data = sock.execute(database_name, uid, password, 'loyalty.reward','read',reward_id,['name','reward_type','point_cost','minimum_points','gift_product_id','discount','discount_product_id','point_product_id'])
                    reward_vals = {
                        'name': reward_data[0]['name'],
                        'reward_type': reward_data[0]['reward_type'],
                        'point_cost': reward_data[0]['point_cost'],
                        'minimum_points': reward_data[0]['minimum_points'],
                        'discount': reward_data[0]['discount'],
                    }
                    if reward_data[0]['gift_product_id']:
                        product_data = sock.execute(database_name, uid, password, 'product.product','read',reward_data[0]['gift_product_id'][0],['pos_sync_id'])
                        if product_data:
                            product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                            if product_obj:
                                reward_vals.update({'gift_product_id': product_obj and product_obj.id or False})
                                
                    if reward_data[0]['discount_product_id']:
                        product_data = sock.execute(database_name, uid, password, 'product.product','read',reward_data[0]['discount_product_id'][0],['pos_sync_id'])
                        if product_data:
                            product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                            if product_obj:
                                reward_vals.update({'discount_product_id': product_obj and product_obj.id or False})
                                
                    if reward_data[0]['point_product_id']:
                        product_data = sock.execute(database_name, uid, password, 'product.product','read',reward_data[0]['point_product_id'][0],['pos_sync_id'])
                        if product_data:
                            product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                            if product_obj:
                                reward_vals.update({'point_product_id': product_obj and product_obj.id or False})
                    
                    reward_vals_list.append(reward_vals)
                
                if log_data[0]['method'] == 'write':
                    if loyalty_obj:
                        loyalty_obj.write(vals)
                        # For Rules
                        client_rule_id = self.env['loyalty.rule'].search([('loyalty_program_id','=',loyalty_obj.id)])
                        client_rule_id.unlink()
                        for rule_vals in rule_vals_list:
                            rule_vals.update({'loyalty_program_id': loyalty_obj and loyalty_obj.id or False})
                            self.env['loyalty.rule'].create(rule_vals)
                            
                        # For Rewards
                        client_reward_id = self.env['loyalty.reward'].search([('loyalty_program_id','=',loyalty_obj.id)])
                        client_reward_id.unlink()
                        for reward_vals in reward_vals_list:
                            reward_vals.update({'loyalty_program_id': loyalty_obj and loyalty_obj.id or False})
                            self.env['loyalty.reward'].create(reward_vals)
                if log_data[0]['method'] == 'create':
                    loyalty_id = loyalty_pool.create(vals)
                    # For Rules
                    for rule_vals in rule_vals_list:
                        rule_vals.update({'loyalty_program_id': loyalty_id and loyalty_id.id or False})
                        self.env['loyalty.rule'].create(rule_vals)
                    # For Rewards
                    for reward_vals in reward_vals_list:
                        reward_vals.update({'loyalty_program_id': loyalty_id and loyalty_id.id or False})
                        self.env['loyalty.reward'].create(reward_vals)
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
