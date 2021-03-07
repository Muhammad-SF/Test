# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    update_reach = fields.Boolean(string='Update Reach', copy=False)


    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.so_entitle_commission_interval()
        return res

    @api.multi
    def so_entitle_commission_interval(self):
        self.update_reach = False
        """ this method will fetch the applicable schemes for the order while the
        interval is not transaction and entitle commission """
        self.ensure_one()
        if self.order_line and self.state=='sale' and self.user_id and self.team_id:
            # only process further when salesperson and team both are set
            if not self.user_id == self.team_id.user_id and self.user_id in self.team_id.member_ids:
                commission_amount = 0.0
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.name or '',
                    'invoice_reference': 'N/A',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': 0.0,
                    'commission_amount': 0.0,
                    'target': 0.0,
                    'achieved': 0.0,
                }
                commissioned_product = []
                commissioned_category = []
                # sales person : has to be member of team
                if self.team_id.commission_scheme_salesperson_id and self.team_id.commission_scheme_salesperson_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesperson_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and not scheme.interval == 'transaction':
                            scheme.update_interval()
                            if scheme.start_date <= self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='so':
                                    commission_vals['commission_calculation_type'] = 'SO'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.order_line:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for ol in self.order_line:
                                                        if ol.product_id.categ_id and not ol.product_id.categ_id in categ_list and ol.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(line.product_id.categ_id) if not line.product_id.categ_id in categ_list else ''
                                                    for categ in categ_list:
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.order_line.search([('order_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_total += rec.price_subtotal
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if not self.update_reach:
                                                                    pc.reached += category_total
                                                                if pc.reached >= pc.target:
                                                                    # this means the target is achieved
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[SO] SP > Amount >Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    # create record with 0.0 commission amount
                                                                    commission_vals['commission_amount'] = 0.0
                                                                commission_vals['target'] = pc.target
                                                                commission_vals['achieved'] = category_total
                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)

                                        else:
                                            # if category and product both are set on scheme
                                            # ignore category, commission based on product
                                            for product in scheme.commission_scheme_product_ids:
                                                for line in self.order_line:
                                                    if product.product_id.id == line.product_id.id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            product.reached += self.amount_total
                                                        if product.reached >= product.target:
                                                            # means the target is achieved
                                                            if not product.percent_of_sales == 0.0:
                                                                commission_amount += product.commission_amount
                                                                commission_amount += line.price_subtotal * (product.percent_of_sales / 100)
                                                            else:
                                                                commission_amount += product.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[SO] SP > Amount > Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0
                                                            # create record with 0.0 commission amount
                                                        commission_vals['target'] = product.target
                                                        commission_vals['achieved'] = product.reached
                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)
                                        
                                        
                                        
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [SO] SP > Amount", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

        # ====================================================================== FIRST MILESTONE ======================================================================

                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.order_line:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for ol in self.order_line:
                                                        if ol.product_id.categ_id and not ol.product_id.categ_id in categ_list and ol.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(ol.product_id.categ_id)
                                                    for categ in categ_list:
                                                        category_qty = 0.0
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.order_line.search([('order_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_qty += rec.product_uom_qty
                                                                category_total += rec.price_subtotal
                                                            if not self.update_reach:
                                                                pc.reached += category_qty
                                                            
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0
                                                                commission_vals['target'] = pc.target
                                                                commission_vals['achieved'] = category_qty
                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        
                                        else:
                                            for line in self.order_line:
                                                for p in scheme.commission_scheme_product_ids:
                                                    if line.product_id == p.product_id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            p.reached += line.product_uom_qty
                                                        
                                                        if p.target <= p.reached:
                                                            if not p.percent_of_sales == 0.0:
                                                                commission_amount += p.commission_amount
                                                                commission_amount += line.price_subtotal * (p.percent_of_sales/100)
                                                            else:
                                                                commission_amount += p.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0
                                                        commission_vals['target'] = p.target
                                                        commission_vals['achieved'] = p.reached
                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)

                                        
                                        if scheme.commission_scheme_total_sales_ids:
                                            for line in scheme.commission_scheme_total_sales_ids:
                                                if line.max_sales >= self.amount_total >= line.target:
                                                    total_sales_commission = 0.0
                                                    if not line.percent_of_sales == 0.0:
                                                        total_sales_commission += line.commission_amount
                                                        total_sales_commission += self.amount_total * (line.percent_of_sales / 100)
                                                    else:
                                                        total_sales_commission += line.commission_amount
                                                    # print"[SO] SP > Qty > Interval Commission on Total Sales: ", total_sales_commission
                                                    commission_vals['commission_amount'] += total_sales_commission
                                        
                                        
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [SO] SP > Qty", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True
                                            

        # ====================================================================== SECOND MILESTONE =====================================================================
                
            if self.team_id.user_id or self.user_id == self.team_id.user_id:
                commission_amount = 0.0
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.name or '',
                    'invoice_reference': 'N/A',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': 0.0,
                    'commission_amount': 0.0,
                    'target': 0.0,
                    'achieved': 0.0,
                }
                commissioned_product = []
                commissioned_category = []
                # team leader
                if self.team_id.commission_scheme_salesteamleader_id and self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and not scheme.interval == 'transaction':
                            scheme.update_interval()
                            if scheme.start_date <= self.date_order <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='so':
                                    commission_vals['commission_calculation_type'] = 'SO'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.order_line:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for ol in self.order_line:
                                                        if ol.product_id.categ_id and not ol.product_id.categ_id in categ_list and ol.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(line.product_id.categ_id) if not line.product_id.categ_id in categ_list else ''
                                                    for categ in categ_list:
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.order_line.search([('order_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_total += rec.price_subtotal
                                                            if not self.update_reach:
                                                                pc.reached += category_total

                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0
                                                            else:
                                                                commission_vals['commission_amount'] = 0.0
                                                            commission_vals['target'] = pc.target
                                                            commission_vals['achieved'] = category_total
                                                            commission_vals['base_amount'] = self.amount_total
                                                            commissioned_product.append(line.product_id)
                                                            commissioned_category.append(line.product_id.categ_id)
                                        else:
                                            # if category and product both are set on scheme
                                            # ignore category, commission based on product
                                            for product in scheme.commission_scheme_product_ids:
                                                for line in self.order_line:
                                                    if product.product_id.id == line.product_id.id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            product.reached += self.amount_total
                                                        
                                                        if product.reached >= product.target:
                                                            if not product.percent_of_sales == 0.0:
                                                                commission_amount += product.commission_amount
                                                                commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                            else:
                                                                commission_amount += product.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0
                                                        commission_vals['target'] = product.target
                                                        commission_vals['achieved'] = product.reached
                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)

                                        
                                        if scheme.commission_scheme_total_sales_ids:
                                            for line in scheme.commission_scheme_total_sales_ids:
                                                if line.max_sales >= self.amount_total >= line.target:
                                                    total_sales_commission = 0.0
                                                    if not line.percent_of_sales == 0.0:
                                                        total_sales_commission += line.commission_amount
                                                        total_sales_commission += self.amount_total * (line.percent_of_sales / 100)
                                                    else:
                                                        total_sales_commission += line.commission_amount
                                                    # print"[SO] TL > Amount >Interval Commission on Total Sales: ", total_sales_commission
                                                    commission_vals['commission_amount'] += total_sales_commission
                                        
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [SO] TL > Amount", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)

                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    if pc.reached >= pc.target:
                                                        pc.reached = 0.0
                                                for product in scheme.commission_scheme_product_ids:
                                                    if product.reached >= product.target:
                                                        product.reached = 0.0
                                                    
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                    
                                                if not self.update_reach:
                                                    self.update_reach = True
                                            
        # ====================================================================== THIRD MILESTONE ======================================================================

                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.order_line:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for ol in self.order_line:
                                                        if ol.product_id.categ_id and not ol.product_id.categ_id in categ_list and ol.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(line.product_id.categ_id) if not line.product_id.categ_id in categ_list else ''
                                                    for categ in categ_list:
                                                        category_qty = 0.0
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.order_line.search([('order_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_qty += rec.product_uom_qty
                                                                category_total += rec.price_subtotal
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if not self.update_reach:
                                                                    pc.reached += category_qty
                                                                
                                                                if pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0
                                                                commission_vals['target'] = pc.target
                                                                commission_vals['achieved'] = category_qty
                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        else:
                                            for line in self.order_line:
                                                for p in scheme.commission_scheme_product_ids:
                                                    if line.product_id == p.product_id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            p.reached += line.product_uom_qty
                                                        
                                                        if p.reached >= p.target:
                                                            if not p.percent_of_sales == 0.0:
                                                                commission_amount += p.commission_amount
                                                                commission_amount += line.price_subtotal * (p.percent_of_sales/100)
                                                            else:
                                                                commission_amount += p.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0
                                                        commission_vals['target'] = p.target
                                                        commission_vals['achieved'] = p.reached
                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)

                                        
                                        if scheme.commission_scheme_total_sales_ids:
                                            for line in scheme.commission_scheme_total_sales_ids:
                                                if line.max_sales >= self.amount_total >= line.target:
                                                    total_sales_commission = 0.0
                                                    if not line.percent_of_sales == 0.0:
                                                        total_sales_commission += line.commission_amount
                                                        total_sales_commission += self.amount_total * (line.percent_of_sales / 100)
                                                    else:
                                                        total_sales_commission += line.commission_amount
                                                    # print"[SO] TL > Qty > Interval Commission on Total Sales: ", total_sales_commission
                                                    commission_vals['commission_amount'] += total_sales_commission
                                        
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [SO] TL > Qty", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    if pc.reached >= pc.target:
                                                        pc.reached = 0.0
                                                for product in scheme.commission_scheme_product_ids:
                                                    if product.reached >= product.target:
                                                        product.reached = 0.0
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True
                                            
        # ====================================================================== FORTH MILESTONE ======================================================================



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    update_reach = fields.Boolean(string='Update Reach', copy=False)


    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        self.invoice_entitle_commission_interval()
        # self.payment_entitle_commission_interval()
        return res

    @api.multi
    def invoice_entitle_commission_interval(self):
        

        if self.invoice_line_ids and self.state=='open' and self.user_id and self.team_id:
            # only process further when salesperson and team both are set
            if not self.user_id == self.team_id.user_id and self.user_id in self.team_id.member_ids:
                commissioned_product = []
                commissioned_category = []
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': 0.0,
                    'commission_amount': 0.0,
                }
                commission_amount = 0.0
                # sales person : has to be member of team
                if self.team_id.commission_scheme_salesperson_id and self.team_id.commission_scheme_salesperson_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesperson_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and not scheme.interval == 'transaction':
                            scheme.update_interval()
                            if scheme.start_date <= self.create_date <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='invoice':
                                    commission_vals['commission_calculation_type'] = 'Invoice'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(line.product_id.categ_id) if not line.product_id.categ_id in categ_list else ''
                                                    for categ in categ_list:
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_total += rec.price_subtotal
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if not self.update_reach:
                                                                    pc.reached += category_total
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Invoice] SP > Amount >Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        else:
                                            # if category and product both are set on scheme
                                            # ignore category, commission based on product
                                            for product in scheme.commission_scheme_product_ids:
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            product.reached += self.amount_total
                                                        if product.max_sales >= product.reached >= product.target:
                                                            if not product.percent_of_sales == 0.0:
                                                                commission_amount += product.commission_amount
                                                                commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                            else:
                                                                commission_amount += product.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Invoice] SP > Amount >Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Invoice] SP > Amount", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True
        # =============================================================================================FIRST MILESTONE=============================================================================================

                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(il.product_id.categ_id)
                                                    for categ in categ_list:
                                                        category_qty = 0.0
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_qty += rec.quantity
                                                                category_total += rec.price_subtotal
                                                            if not self.update_reach:
                                                                pc.reached += category_qty

                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0 and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0 and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Invoice] SP > Qty >Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        
                                        else:
                                            for line in self.invoice_line_ids:
                                                for p in scheme.commission_scheme_product_ids:
                                                    if line.product_id == p.product_id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            p.reached += line.product_uom_qty
                                                        
                                                        if p.max_sales >= p.target <= p.reached:
                                                            if not p.percent_of_sales == 0.0:
                                                                commission_amount += p.commission_amount
                                                                commission_amount += line.price_subtotal * (p.percent_of_sales/100)
                                                            else:
                                                                commission_amount += p.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Invoice] SP > Qty >Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Invoice] SP > Qty", commission_vals['commission_amount']
                                            if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                                commission_vals['salesperson'] = self.user_id.name or ''
                                                if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                    if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                        self._create_commission_record(commission_vals)
                                                    else:
                                                        commission_vals['commission_amount'] = 0.0
                                                        self._create_commission_record(commission_vals)
                                                    
                                                    if not self.update_reach:
                                                        self.update_reach = True

                                                else:
                                                    if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                        self._create_commission_record(commission_vals)
                                                    else:
                                                        commission_vals['commission_amount'] = 0.0
                                                        self._create_commission_record(commission_vals)
                                                    
                                                    if not self.update_reach:
                                                        self.update_reach = True


        # =============================================================================================SECOND MILESTONE=============================================================================================

                
            if self.team_id.user_id or self.user_id == self.team_id.user_id:
                commissioned_product = []
                commissioned_category = []
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': 'N/A',
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': 0.0,
                    'commission_amount': 0.0,
                }
                commission_amount = 0.0
                # team leader
                if self.team_id.commission_scheme_salesteamleader_id and self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and not scheme.interval == 'transaction':
                            scheme.update_interval()
                            if scheme.start_date <= self.create_date <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='invoice':
                                    commission_vals['commission_calculation_type'] = 'Invoice'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(line.product_id.categ_id) if not line.product_id.categ_id in categ_list else ''
                                                    for categ in categ_list:
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_total += rec.price_subtotal
                                                            if not self.update_reach:
                                                                pc.reached += category_total
                                                            
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Invoice] TL > Amount >Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        else:
                                            # if category and product both are set on scheme
                                            # ignore category, commission based on product
                                            for product in scheme.commission_scheme_product_ids:
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            product.reached += self.amount_total
                                                        
                                                        if product.max_sales >= product.reached >= product.target:
                                                            if not product.percent_of_sales == 0.0:
                                                                commission_amount += product.commission_amount
                                                                commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                            else:
                                                                commission_amount += product.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Invoice] TL > Amount >Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Invoice] TL > Amount", commission_vals['commission_amount']
                                            if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                                commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                                if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                    if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                        self._create_commission_record(commission_vals)
                                                    else:
                                                        commission_vals['commission_amount'] = 0.0
                                                        self._create_commission_record(commission_vals)
                                                        
                                                    for pc in scheme.commission_scheme_product_category_ids:
                                                        if pc.reached >= pc.target:
                                                            pc.reached = 0.0
                                                    for product in scheme.commission_scheme_product_ids:
                                                        if product.reached >= product.target:
                                                            product.reached = 0.0

                                                    if not self.update_reach:
                                                        self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                    
                                                if not self.update_reach:
                                                    self.update_reach = True
                                            
        # ============================================================================================= THIRD MILESTONE =============================================================================================

                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(il.product_id.categ_id)
                                                    for categ in categ_list:
                                                        category_qty = 0.0
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_qty += rec.quantity
                                                                category_total += rec.price_subtotal
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if not self.update_reach:
                                                                    pc.reached += category_qty
                                                                
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Invoice] TL > Qty >Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        
                                        else:
                                            for line in self.invoice_line_ids:
                                                for p in scheme.commission_scheme_product_ids:
                                                    if line.product_id == p.product_id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            p.reached += line.product_uom_qty
                                                        
                                                        if p.max_sales >= p.reached >= p.target:
                                                            if not p.percent_of_sales == 0.0:
                                                                commission_amount += p.commission_amount
                                                                commission_amount += line.price_subtotal * (p.percent_of_sales/100)
                                                            else:
                                                                commission_amount += p.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Invoice] TL > Qty >Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                            commission_vals['base_amount'] = self.amount_total
                                                            commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Invoice] TL > Qty", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)

                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    if pc.reached >= pc.target:
                                                        pc.reached = 0.0
                                                for product in scheme.commission_scheme_product_ids:
                                                    if product.reached >= product.target:
                                                        product.reached = 0.0
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True
                                            
        # ============================================================================================== FORTH MILESTONE ==============================================================================================

    @api.multi
    def payment_entitle_commission_interval(self):
        if self.invoice_line_ids and self.state=='paid' and self.user_id and self.team_id:
            # only process further when salesperson and team both are set
            if not self.user_id == self.team_id.user_id and self.user_id in self.team_id.member_ids:
                commissioned_product = []
                commissioned_category = []
                all_payment_references = ""
                for payment in self.payment_ids:
                    if payment.state == 'posted':
                        all_payment_references += (payment.name + ", ")
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': all_payment_references.rstrip(", "),
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': 0.0,
                    'commission_amount': 0.0,
                }
                commission_amount = 0.0
                # sales person : has to be member of team
                if self.team_id.commission_scheme_salesperson_id and self.team_id.commission_scheme_salesperson_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesperson_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and not scheme.interval == 'transaction':
                            scheme.update_interval()
                            if scheme.start_date <= self.payment_ids[-1].payment_date <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='payment':
                                    commission_vals['commission_calculation_type'] = 'Payment'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(line.product_id.categ_id) if not line.product_id.categ_id in categ_list else ''
                                                    for categ in categ_list:
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_total += rec.price_subtotal
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if not self.update_reach:
                                                                    pc.reached += category_total
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Payment] SP > Amount > Product Category >Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        else:
                                            # if category and product both are set on scheme
                                            # ignore category, commission based on product
                                            for product in scheme.commission_scheme_product_ids:
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            product.reached += self.amount_total
                                                        if product.max_sales >= product.reached >= product.target:
                                                            if not product.percent_of_sales == 0.0:
                                                                commission_amount += product.commission_amount
                                                                commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                            else:
                                                                commission_amount += product.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Payment] SP > Amount > Product > Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Payment] SP > Amount", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True
        # =============================================================================================FIRST MILESTONE=============================================================================================

                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(il.product_id.categ_id)
                                                    for categ in categ_list:
                                                        category_qty = 0.0
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_qty += rec.quantity
                                                                category_total += rec.price_subtotal
                                                            if not self.update_reach:
                                                                pc.reached += category_qty

                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0 and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0 and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Payment] SP > Qty > Product Category > Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        
                                        else:
                                            for line in self.invoice_line_ids:
                                                for p in scheme.commission_scheme_product_ids:
                                                    if line.product_id == p.product_id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            p.reached += line.product_uom_qty
                                                        
                                                        if p.max_sales >= p.target <= p.reached:
                                                            if not p.percent_of_sales == 0.0:
                                                                commission_amount += p.commission_amount
                                                                commission_amount += line.price_subtotal * (p.percent_of_sales/100)
                                                            else:
                                                                commission_amount += p.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Payment] SP > Qty > Product > Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Payment] SP > Qty", commission_vals['commission_amount']
                                            if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                                commission_vals['salesperson'] = self.user_id.name or ''
                                                if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                    if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                        self._create_commission_record(commission_vals)
                                                    else:
                                                        commission_vals['commission_amount'] = 0.0
                                                        self._create_commission_record(commission_vals)
                                                    
                                                    if not self.update_reach:
                                                        self.update_reach = True

                                                else:
                                                    if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                        self._create_commission_record(commission_vals)
                                                    else:
                                                        commission_vals['commission_amount'] = 0.0
                                                        self._create_commission_record(commission_vals)
                                                    
                                                    if not self.update_reach:
                                                        self.update_reach = True


        # =============================================================================================SECOND MILESTONE=============================================================================================

                
            if self.team_id.user_id or self.user_id == self.team_id.user_id:
                commissioned_product = []
                commissioned_category = []
                all_payment_references = ""
                for payment in self.payment_ids:
                    if payment.state == 'posted':
                        all_payment_references += (payment.name + ", ")
                commission_vals = {
                    'salesperson': '',
                    'sales_team': self.team_id.name or '',
                    'so_reference': self.origin or '',
                    'invoice_reference':  self.number or '',
                    'payment_reference': all_payment_references.rstrip(", "),
                    'date': datetime.today(),
                    'commission_calculation_type': '',
                    'target_type': '',
                    'commission_scheme_id': '',
                    'base_amount': 0.0,
                    'commission_amount': 0.0,
                }
                commission_amount = 0.0
                # team leader
                if self.team_id.commission_scheme_salesteamleader_id and self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids:
                    commission_schemes = self.team_id.commission_scheme_salesteamleader_id.commission_scheme_ids
                    for scheme in commission_schemes:
                        if scheme.interval and not scheme.interval == 'transaction':
                            scheme.update_interval()
                            if scheme.start_date <= self.payment_ids[-1].payment_date <= scheme.end_date:
                                commission_vals['commission_scheme_id'] = (scheme.name + ", ").rstrip(', ')
                                if scheme.based_on and scheme.based_on=='payment':
                                    commission_vals['commission_calculation_type'] = 'Payment'
                                    if scheme.target_type and scheme.target_type=='amount':
                                        commission_vals['target_type'] = 'Amount'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(line.product_id.categ_id) if not line.product_id.categ_id in categ_list else ''
                                                    for categ in categ_list:
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_total += rec.price_subtotal
                                                            if not self.update_reach:
                                                                pc.reached += category_total
                                                            
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_total:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Payment] TL > Amount > Product Category > Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        else:
                                            # if category and product both are set on scheme
                                            # ignore category, commission based on product
                                            for product in scheme.commission_scheme_product_ids:
                                                for line in self.invoice_line_ids:
                                                    if product.product_id.id == line.product_id.id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            product.reached += self.amount_total
                                                        
                                                        if product.max_sales >= product.reached >= product.target:
                                                            if not product.percent_of_sales == 0.0:
                                                                commission_amount += product.commission_amount
                                                                commission_amount += self.amount_total * (product.percent_of_sales / 100)
                                                            else:
                                                                commission_amount += product.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Payment] TL > Amount > Product > Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                        commission_vals['base_amount'] = self.amount_total
                                                        commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Payment] TL > Amount", commission_vals['commission_amount']
                                            if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                                commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                                if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                    if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                        self._create_commission_record(commission_vals)
                                                    else:
                                                        commission_vals['commission_amount'] = 0.0
                                                        self._create_commission_record(commission_vals)

                                                    for pc in scheme.commission_scheme_product_category_ids:
                                                        if pc.reached >= pc.target:
                                                            pc.reached = 0.0
                                                    for product in scheme.commission_scheme_product_ids:
                                                        if product.reached >= product.target:
                                                            product.reached = 0.0
                                                        
                                                    if not self.update_reach:
                                                        self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                    
                                                if not self.update_reach:
                                                    self.update_reach = True
                                            
        # ============================================================================================= THIRD MILESTONE =============================================================================================

                                    elif scheme.target_type and scheme.target_type=='qty':
                                        # commission on qty
                                        commission_vals['target_type'] = 'Qty'
                                        if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                            categ_list = []
                                            for line in self.invoice_line_ids:
                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    for il in self.invoice_line_ids:
                                                        if il.product_id.categ_id and not il.product_id.categ_id in categ_list and il.product_id.categ_id == pc.product_category_id:
                                                            categ_list.append(il.product_id.categ_id)
                                                    for categ in categ_list:
                                                        category_qty = 0.0
                                                        category_total = 0.0
                                                        if categ not in commissioned_category:
                                                            categ_prod = self.invoice_line_ids.search([('invoice_id', '=', self.id), ('product_id.categ_id', '=', categ.id)])
                                                            for rec in categ_prod:
                                                                category_qty += rec.quantity
                                                                category_total += rec.price_subtotal
                                                            if line.product_id.categ_id and line.product_id.categ_id == pc.product_category_id  and not line.product_id in commissioned_product and not line.product_id.categ_id in commissioned_category:
                                                                if not self.update_reach:
                                                                    pc.reached += category_qty
                                                                
                                                                if pc.max_sales >= pc.reached >= pc.target:
                                                                    if not pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                        commission_amount += category_total * (pc.percent_of_sales/100)
                                                                    elif pc.percent_of_sales == 0.0:  # and pc.target <= category_qty:
                                                                        commission_amount += pc.commission_amount
                                                                    commission_vals['commission_amount'] = commission_amount
                                                                    if scheme.commission_scheme_total_sales_ids:
                                                                        for ts in scheme.commission_scheme_total_sales_ids:
                                                                            if ts.max_sales >= self.amount_total >= ts.target:
                                                                                total_sales_commission = 0.0
                                                                                if not ts.percent_of_sales == 0.0:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                    total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                                else:
                                                                                    total_sales_commission += ts.commission_amount
                                                                                # print"[Payment] TL > Qty > Product Category > Interval Commission on Total Sales: ", total_sales_commission
                                                                                commission_vals['commission_amount'] += total_sales_commission
                                                                else:
                                                                    commission_vals['commission_amount'] = 0.0

                                                                commission_vals['base_amount'] = self.amount_total
                                                                commissioned_product.append(line.product_id)
                                                                commissioned_category.append(line.product_id.categ_id)
                                        
                                        else:
                                            for line in self.invoice_line_ids:
                                                for p in scheme.commission_scheme_product_ids:
                                                    if line.product_id == p.product_id and not line.product_id in commissioned_product:
                                                        if not self.update_reach:
                                                            p.reached += line.product_uom_qty
                                                        
                                                        if p.max_sales >= p.reached >= p.target:
                                                            if not p.percent_of_sales == 0.0:
                                                                commission_amount += p.commission_amount
                                                                commission_amount += line.price_subtotal * (p.percent_of_sales/100)
                                                            else:
                                                                commission_amount += p.commission_amount
                                                            commission_vals['commission_amount'] = commission_amount
                                                            if scheme.commission_scheme_total_sales_ids:
                                                                for ts in scheme.commission_scheme_total_sales_ids:
                                                                    if ts.max_sales >= self.amount_total >= ts.target:
                                                                        total_sales_commission = 0.0
                                                                        if not ts.percent_of_sales == 0.0:
                                                                            total_sales_commission += ts.commission_amount
                                                                            total_sales_commission += self.amount_total * (ts.percent_of_sales / 100)
                                                                        else:
                                                                            total_sales_commission += ts.commission_amount
                                                                        # print"[Payment] TL > Qty > Product > Interval Commission on Total Sales: ", total_sales_commission
                                                                        commission_vals['commission_amount'] += total_sales_commission
                                                        else:
                                                            commission_vals['commission_amount'] = 0.0

                                                            commission_vals['base_amount'] = self.amount_total
                                                            commissioned_product.append(line.product_id)
                                        if commission_vals['commission_amount'] or commission_vals['commission_amount']==0.0:
                                            commission_vals['salesperson'] = self.team_id.user_id.name or ''
                                            # print"INTERVAL COMMISSION: [Payment] TL > Qty", commission_vals['commission_amount']
                                            if scheme.commission_scheme_product_category_ids and not scheme.commission_scheme_product_ids:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_category_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)

                                                for pc in scheme.commission_scheme_product_category_ids:
                                                    if pc.reached >= pc.target:
                                                        pc.reached = 0.0
                                                for product in scheme.commission_scheme_product_ids:
                                                    if product.reached >= product.target:
                                                        product.reached = 0.0
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True

                                            else:
                                                if all(line.reached >= line.target for line in scheme.commission_scheme_product_ids):
                                                    self._create_commission_record(commission_vals)
                                                else:
                                                    commission_vals['commission_amount'] = 0.0
                                                    self._create_commission_record(commission_vals)
                                                
                                                if not self.update_reach:
                                                    self.update_reach = True
                                            
        # ============================================================================================== FORTH MILESTONE ==============================================================================================



class AccountPayment(models.Model):
    _inherit = 'account.payment'


    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        active_id = self.env.context.get('active_id')
        invoice = self.env['account.invoice'].browse(active_id)
        invoice.payment_entitle_commission_interval()
        return res
