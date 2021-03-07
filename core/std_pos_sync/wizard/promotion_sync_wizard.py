from odoo import fields, models,api
from odoo.tools.translate import _
from datetime import datetime
#import xmlrpc.client
import xmlrpclib
from odoo.exceptions import ValidationError,UserError
import logging
logger = logging.getLogger(__name__)

class PromotionSyncWizard(models.TransientModel):
    _name = 'promotion.sync.wizard'
    
    
    @api.multi
    def action_promotion_sync(self):
        
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
        
        promotion_pool = self.env['pos.promotion']
        synclog_pool = self.env['pos.promotion.sync.log']
        model_id = self.env['ir.model'].search([('model', '=', 'pos.promotion')])
        
        con_model_id = sock.execute(database_name, uid, password, 'ir.model','search', [('model', '=', 'pos.promotion')])
        latest_auditlogs = []
        if any(synclog_pool.search([])):
            last_synclogs_id = max(synclog_pool.search([]).ids)
            last_sync_date = synclog_pool.browse(last_synclogs_id).create_date
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('create_date', '>', last_sync_date),('model_id', '=', con_model_id[0])])
        else:
            latest_auditlogs = sock.execute(database_name, uid, password, 'auditlog.log','search', [('model_id', '=', con_model_id[0])])
            
        for log_id in latest_auditlogs:
            log_data = sock.execute(database_name, uid, password, 'auditlog.log','read',log_id,['create_date','res_id','method'])
            pos_sync_id = sock.execute(database_name, uid, password, 'pos.promotion','read',log_data[0]['res_id'],['pos_sync_id'])
            if pos_sync_id:
                promotion_obj = promotion_pool.search([('pos_sync_id','=', pos_sync_id[0]['pos_sync_id'])])
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
                
                # For the  Discounts on Total Order
                discount_order_ids = sock.execute(database_name, uid, password, 'pos.promotion.discount.order','search',[('promotion_id', '=', log_data[0]['res_id'])])
                discount_vals_list = []
                for discount_id in discount_order_ids:
                    discount_data = sock.execute(database_name, uid, password, 'pos.promotion.discount.order','read',discount_id,['discount','minimum_amount'])
                    discount_vals = {
                        'discount': discount_data[0]['discount'],
                        'minimum_amount': discount_data[0]['minimum_amount'],
                    }
                    discount_vals_list.append(discount_vals)
                    
                # For the  Discount on Categories
                discount_categ_ids = sock.execute(database_name, uid, password, 'pos.promotion.discount.category','search',[('promotion_id', '=', log_data[0]['res_id'])])
                discateg_vals_list = []
                for discateg_id in discount_categ_ids:
                    discateg_data = sock.execute(database_name, uid, password, 'pos.promotion.discount.category','read',discateg_id,['discount','category_id'])
                    category_data = sock.execute(database_name, uid, password, 'pos.category','read',discateg_data[0]['category_id'][0],['pos_sync_id'])
                    if category_data:
                        pos_category_obj = self.env['pos.category'].search([('pos_sync_id','=', category_data[0]['pos_sync_id'])])
                        if pos_category_obj:
                            discateg_vals = {
                                'discount': discateg_data[0]['discount'],
                                'category_id': pos_category_obj and pos_category_obj.id or False,
                            }
                            discateg_vals_list.append(discateg_vals)
                
                # For the Discount by quantity of products
                discount_qty_ids = sock.execute(database_name, uid, password, 'pos.promotion.discount.quantity','search',[('promotion_id', '=', log_data[0]['res_id'])])
                disqty_vals_list = []
                for disqty_id in discount_qty_ids:
                    disqty_data = sock.execute(database_name, uid, password, 'pos.promotion.discount.quantity','read',disqty_id,['product_id','quantity','discount'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',disqty_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            disqty_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'quantity': disqty_data[0]['quantity'],
                                'discount': disqty_data[0]['discount'],
                            }
                            disqty_vals_list.append(disqty_vals)
                
                # For the Buy pack products discount products [Pack Items (By product x+y+z ... will discount products a+b+c ...) ]
                discount_condition_ids = sock.execute(database_name, uid, password, 'pos.promotion.discount.condition','search',[('promotion_id', '=', log_data[0]['res_id'])])
                discon_vals_list = []
                for discon_id in discount_condition_ids:
                    discon_data = sock.execute(database_name, uid, password, 'pos.promotion.discount.condition','read',discon_id,['product_id','minimum_quantity'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',discon_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            discon_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'minimum_quantity': discon_data[0]['minimum_quantity'],
                            }
                            discon_vals_list.append(discon_vals)
                # For the Buy pack products discount products [ Products will discount ]
                discount_apply_ids = sock.execute(database_name, uid, password, 'pos.promotion.discount.apply','search',[('promotion_id', '=', log_data[0]['res_id'])])
                disapply_vals_list = []
                for disapply_id in discount_apply_ids:
                    disapply_data = sock.execute(database_name, uid, password, 'pos.promotion.discount.apply','read',disapply_id,['product_id','discount'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',disapply_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            disapply_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'discount': disapply_data[0]['discount'],
                            }
                            disapply_vals_list.append(disapply_vals)
                # For the Buy pack products free products [ Pack Items (By product x+y+z ... will free products a+b+c ...) ]
                gift_cond_ids = sock.execute(database_name, uid, password, 'pos.promotion.gift.condition','search',[('promotion_id', '=', log_data[0]['res_id'])])
                gift_cond_vals_list = []
                for gift_id in gift_cond_ids:
                    giftcon_data = sock.execute(database_name, uid, password, 'pos.promotion.gift.condition','read',gift_id,['product_id','minimum_quantity'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',giftcon_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            gift_cond_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'minimum_quantity': giftcon_data[0]['minimum_quantity'],
                            }
                            gift_cond_vals_list.append(gift_cond_vals)
                            
                # For the Buy pack products free products [  Products will free (gift)  ]
                gift_free_ids = sock.execute(database_name, uid, password, 'pos.promotion.gift.free','search',[('promotion_id', '=', log_data[0]['res_id'])])
                gift_free_vals_list = []
                for gift_id in gift_free_ids:
                    giftfree_data = sock.execute(database_name, uid, password, 'pos.promotion.gift.free','read',gift_id,['product_id','quantity_free'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',giftfree_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            gift_free_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'quantity_free': giftfree_data[0]['quantity_free'],
                            }
                            gift_free_vals_list.append(gift_free_vals)
                            
                # For the price product filter by quantity
                pos_price_ids = sock.execute(database_name, uid, password, 'pos.promotion.price','search',[('promotion_id', '=', log_data[0]['res_id'])])
                pos_price_vals_list = []
                for price_id in pos_price_ids:
                    posprice_data = sock.execute(database_name, uid, password, 'pos.promotion.price','read',price_id,['product_id','minimum_quantity','list_price'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',posprice_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            posprice_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'minimum_quantity': posprice_data[0]['minimum_quantity'],
                                'list_price': posprice_data[0]['list_price'],
                            }
                            pos_price_vals_list.append(posprice_vals)
                            
                # For the Discount by Brands 
                brand_discount_ids = sock.execute(database_name, uid, password, 'pos.brand.discount.condition','search',[('promotion_id', '=', log_data[0]['res_id'])])
                branddic_vals_list = []
                for branddis_id in brand_discount_ids:
                    branddic_data = sock.execute(database_name, uid, password, 'pos.brand.discount.condition','read',branddis_id,['brand_ids','discount'])
                    pos_sync_id_list = []
                    if branddic_data[0]['brand_ids']:
                        brand_data = sock.execute(database_name, uid, password, 'product.brand','read',branddic_data[0]['brand_ids'],['pos_sync_id'])
                        for b_data in brand_data:
                            pos_sync_id_list.append(b_data['pos_sync_id'])
                    if pos_sync_id_list:
                        brand_obj = self.env['product.brand'].search([('pos_sync_id','in', pos_sync_id_list)])
                        brand_ids_list = []
                        for pb_obj in brand_obj:
                            brand_ids_list.append(pb_obj.id) 
                        if brand_obj:
                            branddis_vals = {
                                'brand_ids': [( 6, 0, brand_ids_list)],
                                'discount': branddic_data[0]['discount'],
                            }
                            branddic_vals_list.append(branddis_vals)
                
                # For the buy products free products [Products]
                product_condition_ids = sock.execute(database_name, uid, password, 'pos.product.product.condition','search',[('promotion_id', '=', log_data[0]['res_id'])])
                prodcon_vals_list = []
                for prodcon_id in product_condition_ids:
                    prodcon_data = sock.execute(database_name, uid, password, 'pos.product.product.condition','read',prodcon_id,['product_id','minimum_quantity'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',prodcon_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            prodcon_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'minimum_quantity': prodcon_data[0]['minimum_quantity'],
                            }
                            prodcon_vals_list.append(prodcon_vals)
                # For the buy products free products [ List of free product ]
                product_free_ids = sock.execute(database_name, uid, password, 'pos.product.product.free','search',[('promotion_id', '=', log_data[0]['res_id'])])
                prodfree_vals_list = []
                for prodfree_id in product_free_ids:
                    prodfree_data = sock.execute(database_name, uid, password, 'pos.product.product.free','read',prodfree_id,['product_id','max_qty'])
                    product_data = sock.execute(database_name, uid, password, 'product.product','read',prodfree_data[0]['product_id'][0],['pos_sync_id'])
                    if product_data:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','=', product_data[0]['pos_sync_id'])])
                        if pos_product_obj:
                            profree_vals = {
                                'product_id': pos_product_obj and pos_product_obj.id or False,
                                'max_qty': prodfree_data[0]['max_qty'],
                            }
                            prodfree_vals_list.append(profree_vals)
                
                # For the  Free x from group of products 
                product_group_ids = sock.execute(database_name, uid, password, 'pos.group.of.products','search',[('promotion_id', '=', log_data[0]['res_id'])])
                prodgroup_vals_list = []
                for prodgroup_id in product_group_ids:
                    prodgroup_data = sock.execute(database_name, uid, password, 'pos.group.of.products','read',prodgroup_id,['product_id','no_of_product','to_pay','min_qty','min_amount'])
                    pos_sync_id_list = []
                    if prodgroup_data[0]['product_id']:
                        product_data = sock.execute(database_name, uid, password, 'product.product','read',prodgroup_data[0]['product_id'],['pos_sync_id'])
                        for pp_data in product_data:
                            pos_sync_id_list.append(pp_data['pos_sync_id'])
                    if pos_sync_id_list:
                        pos_product_obj = self.env['product.product'].search([('pos_sync_id','in', pos_sync_id_list)])
                        product_ids_list = []
                        for pp_obj in pos_product_obj:
                            product_ids_list.append(pp_obj.id) 
                        if pos_product_obj:
                            progroup_vals = {
                                'product_id': [( 6, 0, product_ids_list)],
                                'no_of_product': prodgroup_data[0]['no_of_product'],
                                'to_pay': prodgroup_data[0]['to_pay'],
                                'min_qty': prodgroup_data[0]['min_qty'],
                                'min_amount': prodgroup_data[0]['min_amount'],
                            }
                            prodgroup_vals_list.append(progroup_vals)
                
                if log_data[0]['method'] == 'write':
                    if promotion_obj:
                        promotion_obj.write(vals)
                        # For the  Discounts on Total Order
                        client_discount_id = self.env['pos.promotion.discount.order'].search([('promotion_id','=',promotion_obj.id)])
                        client_discount_id.unlink()
                        for dis_vals in discount_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.discount.order'].create(dis_vals)
                            
                        # For the  Discount on Categories
                        client_discateg_id = self.env['pos.promotion.discount.category'].search([('promotion_id','=',promotion_obj.id)])
                        client_discateg_id.unlink()
                        for dis_vals in discateg_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.discount.category'].create(dis_vals)
                            
                        # For the Discount by quantity of products
                        client_discqty_id = self.env['pos.promotion.discount.quantity'].search([('promotion_id','=',promotion_obj.id)])
                        client_discqty_id.unlink()
                        for dis_vals in disqty_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.discount.quantity'].create(dis_vals)
                        
                        # For the Buy pack products discount products [Pack Items (By product x+y+z ... will discount products a+b+c]
                        client_disccon_id = self.env['pos.promotion.discount.condition'].search([('promotion_id','=',promotion_obj.id)])
                        client_disccon_id.unlink()
                        for dis_vals in discon_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.discount.condition'].create(dis_vals)
                        # For the Buy pack products discount products [ Products will discount ]
                        client_discapply_id = self.env['pos.promotion.discount.apply'].search([('promotion_id','=',promotion_obj.id)])
                        client_discapply_id.unlink()
                        for dis_vals in disapply_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.discount.apply'].create(dis_vals)
                        
                        # For the Buy pack products free products [ Pack Items (By product x+y+z ... will free products a+b+c ...) ]
                        client_giftcon_id = self.env['pos.promotion.gift.condition'].search([('promotion_id','=',promotion_obj.id)])
                        client_giftcon_id.unlink()
                        for dis_vals in gift_cond_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.gift.condition'].create(dis_vals)
                        # For the Buy pack products free products [  Products will free (gift)  ]
                        client_giftfree_id = self.env['pos.promotion.gift.free'].search([('promotion_id','=',promotion_obj.id)])
                        client_giftfree_id.unlink()
                        for dis_vals in gift_free_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.gift.free'].create(dis_vals)
                        
                        # For the price product filter by quantity
                        client_posprice_id = self.env['pos.promotion.price'].search([('promotion_id','=',promotion_obj.id)])
                        client_posprice_id.unlink()
                        for dis_vals in pos_price_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.promotion.price'].create(dis_vals)
                        
                        # For the Discount by brands
                        client_branddis_id = self.env['pos.brand.discount.condition'].search([('promotion_id','=',promotion_obj.id)])
                        client_branddis_id.unlink()
                        for dis_vals in branddic_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.brand.discount.condition'].create(dis_vals)
                        
                        # For the buy products free products [Products]
                        client_prodcon_id = self.env['pos.product.product.condition'].search([('promotion_id','=',promotion_obj.id)])
                        client_prodcon_id.unlink()
                        for dis_vals in prodcon_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.product.product.condition'].create(dis_vals)
                        # For the buy products free products [ List of free product ]
                        client_prodfree_id = self.env['pos.product.product.free'].search([('promotion_id','=',promotion_obj.id)])
                        client_prodfree_id.unlink()
                        for dis_vals in prodfree_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.product.product.free'].create(dis_vals)
                        # For the Free x from group of products 
                        client_prodgroup_id = self.env['pos.group.of.products'].search([('promotion_id','=',promotion_obj.id)])
                        client_prodgroup_id.unlink()
                        for dis_vals in prodgroup_vals_list:
                            dis_vals.update({'promotion_id': promotion_obj and promotion_obj.id or False})
                            self.env['pos.group.of.products'].create(dis_vals)
                if log_data[0]['method'] == 'create':
                    promotion_id = promotion_pool.create(vals)
                    # For the  Discounts on Total Order
                    for dis_vals in discount_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.discount.order'].create(dis_vals)
                    # For the  Discount on Categories
                    for dis_vals in discateg_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.discount.category'].create(dis_vals)
                    # For the Discount by quantity of products
                    for dis_vals in disqty_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.discount.quantity'].create(dis_vals)
                    # For the Buy pack products discount products [Pack Items (By product x+y+z ... will discount products a+b+c]
                    for dis_vals in discon_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.discount.condition'].create(dis_vals)
                    # For the Buy pack products discount products [ Products will discount ]
                    for dis_vals in disapply_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.discount.apply'].create(dis_vals)
                    # For the Buy pack products free products [ Pack Items (By product x+y+z ... will free products a+b+c ...) ]
                    for dis_vals in gift_cond_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.gift.condition'].create(dis_vals)
                    # For the Buy pack products free products [  Products will free (gift)  ]
                    for dis_vals in gift_free_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.gift.free'].create(dis_vals)
                    # For the price product filter by quantity
                    for dis_vals in pos_price_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.promotion.price'].create(dis_vals)
                    # For the discount by brands
                    for dis_vals in branddic_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.brand.discount.condition'].create(dis_vals)
                    # For the buy products free products [Products]
                    for dis_vals in prodcon_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.product.product.condition'].create(dis_vals)
                    # For the buy products free products [ List of free product ]
                    for dis_vals in prodfree_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.product.product.free'].create(dis_vals)
                    # For the Free x from group of products 
                    for dis_vals in prodgroup_vals_list:
                        dis_vals.update({'promotion_id': promotion_id and promotion_id.id or False})
                        self.env['pos.group.of.products'].create(dis_vals)
        synclog_pool.create({'date': fields.date.today(), 'status': status})
        return True
