from odoo import fields, models,api
from odoo.tools.translate import _
from datetime import datetime
#import xmlrpc.client
import xmlrpclib
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

#Product Attributes
class ProductAttrsSyncWizard(models.TransientModel):
    _name = 'product.attrs.sync.wizard'
    
    @api.multi
    def action_product_attrs_sync(self):
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
        
        product_attrs_pool = self.env['product.attribute']
        synclog_pool = self.env['product.attribute.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'product.attribute')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'product.attribute')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'product.attribute','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                product_attrs_obj = product_attrs_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
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
                if log_data[0]['method'] == 'write':
                    if product_attrs_obj:
                        product_attrs_obj.write(vals)
                if log_data[0]['method'] == 'create':
                    product_attrs_id = product_attrs_pool.create(vals)
                    
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
        
#Product Attribute Values
class ProductAttrsSyncWizard(models.TransientModel):
    _name = 'product.attrs.values.sync.wizard'
    
    @api.multi
    def action_product_attrs_values_sync(self):
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
        
        product_attrs_values_pool = self.env['product.attribute.value']
        synclog_pool = self.env['product.attrs.value.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'product.attribute.value')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'product.attribute.value')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'product.attribute.value','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                product_attrs_values_obj = product_attrs_values_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
                logline_ids = sock.execute(database_name, uid, password, 'auditlog.log.line','search',[('log_id', '=', log_id)])
                vals = {}
                for logline_id in logline_ids:
                    logline_data = sock.execute(database_name, uid, password, 'auditlog.log.line','read',logline_id,['field_name','new_value_text'])
                    field_id = sock.execute(database_name, uid, password, 'ir.model.fields','search',[('model_id', '=', con_model_id[0]),('name', '=', logline_data[0]['field_name'])])
                    field_data = sock.execute(database_name, uid, password, 'ir.model.fields','read',field_id[0],['ttype'])
                    if field_data[0]['ttype'] == 'many2one':
                        if logline_data[0]['new_value_text']:
                            if logline_data[0]['field_name'] == 'attribute_id':
                                many2one_id = int((logline_data[0]['new_value_text'].split(',')[0]).rsplit('(')[1])
                                product_attrs_name = sock.execute(database_name, uid, password, 'product.attribute','read',many2one_id,['pos_sync_id'])
                                attribute_id = self.env['product.attribute'].search([('pos_sync_id', '=', product_attrs_name[0]['pos_sync_id'])])
                                if attribute_id:
                                    vals.update({'attribute_id':attribute_id and attribute_id.id or False})
                    elif field_data[0]['ttype'] in ['many2many','one2many']:
                        if logline_data[0]['new_value_text']:
                            many2many_data = logline_data[0]['new_value_text']
                    else:
                        vals.update({logline_data[0]['field_name']: logline_data[0]['new_value_text']})
                if log_data[0]['method'] == 'write':
                    if product_attrs_values_obj:
                        product_attrs_values_obj.write(vals)
                if log_data[0]['method'] == 'create':
                    product_attrs_values_id = product_attrs_values_pool.create(vals)
                    
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True

#Product and Product Variants
class ProductSyncWizard(models.TransientModel):
    _name = 'product.sync.wizard'
    
    
    @api.multi
    def action_product_sync(self):
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
        
        # For Product Templates
        product_pool = self.env['product.template']
        synclog_pool = self.env['product.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'product.template')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'product.template')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pt_pos_sync_id = sock.execute(database_name, uid, password, 'product.template','read',log_data[0]['res_id'],['pt_pos_sync_id'])
            if pt_pos_sync_id:
                product_obj = product_pool.search([('pt_pos_sync_id','=', pt_pos_sync_id[0]['pt_pos_sync_id'])])
                logline_ids = sock.execute(database_name, uid, password, 'auditlog.log.line','search',[('log_id', '=', log_id)])
                vals = {}
                attribute_line_vals_list = []
                for logline_id in logline_ids:
                    logline_data = sock.execute(database_name, uid, password, 'auditlog.log.line','read',logline_id,['field_name','new_value_text','new_value'])
                    field_id = sock.execute(database_name, uid, password, 'ir.model.fields','search',[('model_id', '=', con_model_id[0]),('name', '=', logline_data[0]['field_name'])])
                    field_data = sock.execute(database_name, uid, password, 'ir.model.fields','read',field_id[0],['ttype'])
                    if field_data[0]['ttype'] == 'many2one':
                        if logline_data[0]['new_value_text']:
                            many2one_data = logline_data[0]['new_value_text']
                    elif field_data[0]['ttype'] in ['many2many','one2many']:
                        if logline_data[0]['new_value_text']:
                            #Sync Multiple POS Category
                            print "\n\n======logline_data111111",logline_data
                            if logline_data[0]['field_name'] == 'pos_categ_ids' and logline_data[0]['new_value']:
                                new_value = logline_data[0]['new_value'][1:-1]
                                if new_value:
                                    many2many_ids = new_value.split(',')
                                    categ_ids = []
                                    for many2many_id in many2many_ids:
                                        pos_ctage_name = sock.execute(database_name, uid, password, 'pos.category','read',int(many2many_id),['pos_sync_id'])
                                        product_categ = self.env['pos.category'].search([('pos_sync_id', '=', pos_ctage_name[0]['pos_sync_id'])])
                                        categ_ids.append(product_categ.id)
                                    if categ_ids:
                                        vals.update({'pos_categ_ids': [( 6, 0, categ_ids)]})
                            #Sync Product Variants
                            if field_data[0]['ttype'] == 'one2many':
                                if logline_data[0]['field_name'] == 'attribute_line_ids':
                                    #print "\n\n$$$$$$$$$$$4logline_data[0]['new_value']",logline_data[0]['new_value']
                                    if logline_data[0]['new_value'] != '[]':
                                        if logline_data[0]['new_value'].startswith('[') and logline_data[0]['new_value'].endswith(']'): 
                                            one2many_logdata = logline_data[0]['new_value'][1:-1]
                                            one2many_logdata1 = one2many_logdata.split(",")
                                            for attribute_line in one2many_logdata1:
                                                attribute_line_data = sock.execute(database_name, uid, password, 'product.attribute.line','read',int(attribute_line),['attribute_id','value_ids'])
                                                #print "\n\n==attribute_line_data======",attribute_line_data
                                                attribute_line_vals = {}
                                                value_list = []
                                                if attribute_line_data:
                                                    if attribute_line_data[0]['attribute_id']:
                                                        attribute_name = sock.execute(database_name, uid, password, 'product.attribute','read',int(attribute_line_data[0]['attribute_id'][0]),['pos_sync_id'])
                                                        attribute_id = self.env['product.attribute'].search([('pos_sync_id', '=', attribute_name[0]['pos_sync_id'])])
                                                        if attribute_id:
                                                            attribute_line_vals.update({'attribute_id': attribute_id and attribute_id.id or False})
                                                    if attribute_line_data[0]['value_ids']:
                                                        for value_id in attribute_line_data[0]['value_ids']:
                                                            value_name = sock.execute(database_name, uid, password, 'product.attribute.value','read',int(value_id),['pos_sync_id'])
                                                            value_id = self.env['product.attribute.value'].search([('pos_sync_id', '=', value_name[0]['pos_sync_id'])])
                                                            if value_id:
                                                                value_list.append(value_id.id)
                                                attribute_line_vals.update({'value_ids': [(6, 0, value_list)]})
                                                attribute_line_vals_list.append((0,0,attribute_line_vals))
                    else:
                        vals.update({logline_data[0]['field_name']: logline_data[0]['new_value_text']})
                vals.update({'attribute_line_ids':  attribute_line_vals_list})
                if log_data[0]['method'] == 'write':
                    if product_obj:
                        product_obj.write(vals)
                if log_data[0]['method'] == 'create':
                    product_id = product_pool.create(vals)
                    for product_variant_id in product_id.product_variant_ids:
                        mst_productv_ids = sock.execute(database_name, uid, password, 'product.product','search',[('pt_pos_sync_id', '=', product_id.pt_pos_sync_id)])
                        for mst_productv_id in mst_productv_ids:
                            mst_pv_data = sock.execute(database_name, uid, password, 'product.product','read',mst_productv_id,['display_name','pos_sync_id'])
                            if mst_pv_data[0]['display_name'] == product_variant_id.display_name:
                                product_variant_id.write({'pos_sync_id': mst_pv_data[0]['pos_sync_id']})
                    
        # For Product Variants
        product_product_pool = self.env['product.product']
        pp_model_id = self.env['ir.model'].search([('model', '=', 'product.product')])
        
        pp_con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'product.product')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', pp_con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', pp_con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'product.product','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                product_product_obj = product_product_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
                logline_ids = sock.execute(database_name, uid, password, 'auditlog.log.line','search',[('log_id', '=', log_id)])
                vals = {}
                for logline_id in logline_ids:
                    logline_data = sock.execute(database_name, uid, password, 'auditlog.log.line','read',logline_id,['field_name','new_value_text','new_value'])
                    field_id = sock.execute(database_name, uid, password, 'ir.model.fields','search',[('model_id', '=', pp_con_model_id[0]),('name', '=', logline_data[0]['field_name'])])
                    field_data = sock.execute(database_name, uid, password, 'ir.model.fields','read',field_id[0],['ttype'])
                    
                    if field_data[0]['ttype'] == 'many2one':
                        if logline_data[0]['new_value_text']:
                            many2one_data = logline_data[0]['new_value_text']
                    elif field_data[0]['ttype'] in ['many2many','one2many']:
                        if logline_data[0]['new_value_text']:
                            if logline_data[0]['field_name'] == 'pos_categ_ids' and logline_data[0]['new_value']:
                                new_value = logline_data[0]['new_value'][1:-1]
                                if new_value:
                                    many2many_ids = new_value.split(',')
                                    categ_ids = []
                                    for many2many_id in many2many_ids:
                                        pos_ctage_name = sock.execute(database_name, uid, password, 'pos.category','read',int(many2many_id),['pos_sync_id'])
                                        product_categ = self.env['pos.category'].search([('pos_sync_id', '=', pos_ctage_name[0]['pos_sync_id'])])
                                        categ_ids.append(product_categ.id)
                                    if categ_ids:
                                        vals.update({'pos_categ_ids': [( 6, 0, categ_ids)]})
                    else:
                        if logline_data[0]['field_name'] != 'barcode':
                            vals.update({logline_data[0]['field_name']: logline_data[0]['new_value_text']})
                        else:
                            mst_pv_ids = sock.execute(database_name, uid, password, 'product.product','search', [('pos_sync_id', '=', product_product_obj.pos_sync_id)])
                            mst_pv_data = sock.execute(database_name, uid, password, 'product.product','read',mst_pv_ids[0],['barcode'])
                            vals.update({'barcode': mst_pv_data[0]['barcode']})
                if log_data[0]['method'] == 'write':
                    if product_product_obj:
                        product_product_obj.write(vals)
                #if log_data[0]['method'] == 'create':
                #    product_product_id = product_product_pool.create(vals)
                    
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
