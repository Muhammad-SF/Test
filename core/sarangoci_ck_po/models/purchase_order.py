from odoo import fields, api, models
from odoo.http import request
from datetime import datetime,date
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import xmlrpclib

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        res = super(purchase_order, self).button_confirm()
        if self.partner_id and self.partner_id.name == 'Central Kitchen':
            url = 'http://kitchenoci.equip.asia'
            # url = 'http://beta-dev1.hashmicro.com'
            dbname = 'kitchenoci'
            username = 'admin'
            pwd = 'Hash98992Micro'

            sock_common = xmlrpclib.ServerProxy(url + '/xmlrpc/common')
            uid = sock_common.login(dbname, username, pwd)
            if not uid:
                raise ValueError('Can not connect to database %s' % (dbname))
            sock = xmlrpclib.ServerProxy(url + '/xmlrpc/object')
            # partner = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('name', '=', 'Sarang Oci')])
            partner = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('name', '=', self.env.user.branch_id.name)])
            # partner = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('name', '=', 'Central Kitchen')])
            if not partner:
                partner_data = {
                    'name': self.env.user.branch_id.name,
                    'child_ids' : [(0,0,{'type':'invoice','street': self.env.user.branch_id.address or '','phone':self.env.user.branch_id.telephone_no}),
                                   (0, 0, {'type': 'delivery', 'street': self.env.user.branch_id.address or '','phone': self.env.user.branch_id.telephone_no})
                                   ]
                }
                partner_data.update(sock.execute(dbname, uid, pwd, 'res.partner', 'default_get',
                                                 ['invoice_warn', 'sale_warn', 'notify_email', 'purchase_warn',
                                                  'property_account_receivable_id', 'property_account_payable_id',
                                                  'picking_warn']))

                partner = sock.execute(dbname, uid, pwd, 'res.partner', 'create', partner_data)
            else:
                partner = partner[0]

            # user_id = sock.execute(dbname, uid, pwd, 'res.users', 'search',[('login', '=', self.env.user.login)])
            # if not user_id:
            #     user_id = sock.execute(dbname, uid, pwd, 'res.users', 'create', {
            #         'login': self.env.user.login,
            #         'name': self.env.user.name,
            # #         'is_warehouse': self.env.user.branch_id.is_warehouse,
            # #         'country_code': self.env.user.branch_id.country_code,
            #     })
            # else:
            #     user_id = user_id[0]
            partner_invoice_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('parent_id', '=', partner), ('type', '=', 'invoice')])
            partner_shipping_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('parent_id', '=', partner), ('type', '=', 'delivery')])
            if partner_invoice_id:
                partner_invoice_id = partner_invoice_id[0]
            else:
                raise ValueError(_("Please add Invoice Address to %s Customer")%self.env.user.branch_id.name)
            if partner_shipping_id:
                partner_shipping_id = partner_shipping_id[0]
            else:
                raise ValueError(_("Please add Shipping Address to %s Customer")%self.env.user.branch_id.name)

            # branch_read = sock.execute(dbname, uid, pwd, 'res.branch', 'read',branch_id, ['warehouse_id'])
            partner_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read',partner, ['property_product_pricelist','currency_id'])

            data = {
                # 'branch_id': branch_id,
                'date_order': str(datetime.now()),
                'partner_id': partner,
                # 'warehouse_id': branch_read[0]['warehouse_id'][0],
                'partner_invoice_id': partner_invoice_id,
                'partner_shipping_id': partner_shipping_id,
                'pricelist_id': partner_read[0]['property_product_pricelist'][0],
                'currency_id': partner_read[0]['currency_id'][0],
            }


            data.update(sock.execute(dbname, uid, pwd, 'sale.order', 'default_get',['name', 'picking_policy','branch_id','warehouse_id']))

            sale_order = sock.execute(dbname, uid, pwd, 'sale.order', 'create',data)
            sale_order_line = []

            for line in self.order_line:
                product_id = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('name', '=', line.product_id.name)])
                if not product_id:
                    product_vals = {
                        'name': line.product_id.name,
                        'default_code': line.product_id.default_code,
                        'type': line.product_id.type,
                        'sale_ok': line.product_id.sale_ok,
                        'purchase_ok': line.product_id.purchase_ok,
                        'lst_price': line.product_id.lst_price,
                        'standard_price': line.product_id.standard_price,
                        'uom_id'        : line.product_uom.id,
                    }
                    product_id = sock.execute(dbname, uid, pwd, 'product.product', 'create', product_vals)
                    # product_data = sock.execute(dbname, uid, pwd, 'res.partner', 'read', product_id,['product_tmpl_id'])
                    # if product_data:
                    #     product_tmpl_id = product_data[0]['product_tmpl_id']
                    #     if product_tmpl_id:
                    #         sock.execute(dbname, uid, pwd, 'product.template', 'write', product_tmpl_id,{'uom_id':line.product_id.uom_id.id,'uom_po_id':line.product_id.uom_po_id.id})
                else:
                    product_id = product_id[0]
                line_data={
                    'product_id': product_id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'name': line.name,
                    'customer_lead': 5,
                    'order_id': sale_order,
                }
                line_id = sock.execute(dbname, uid, pwd, 'sale.order.line', 'create', line_data)
                sale_order_line.append(line_id)
            sock.execute(dbname, uid, pwd, 'sale.order', 'write', sale_order,{'order_line': [(6, 0, sale_order_line)]})
            # task_list_data = {
            #     'user_id': 1,
            #     'res_model_id':sock.execute(dbname, uid, pwd, 'ir.model', 'search', [('model', '=', 'sale.order')])[0],
            #     'res_id': sale_order,
            #     'date_deadline': str(date.today()),
            # }
            # sock.execute(dbname, uid, pwd, 'mail.activity', 'create', task_list_data)
