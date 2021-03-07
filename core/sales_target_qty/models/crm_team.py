# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime
from xml.etree.ElementTree import fromstring, ElementTree, Element, tostring
from collections import OrderedDict

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_confirmation_date = fields.Datetime('Confirmation Date',related='order_id.confirmation_date',store=True)

SaleOrderLine()

class CrmTeam(models.Model):
    _inherit = "crm.team"

    sales_qty_targets = fields.One2many('sales.target.qty', 'crm_team_id', string='Sales Team Target')
    sales_target_qty_line_ids = fields.Many2many('sales.target.qty.line', string='Sale Quantity Target')
    sale_target_qty_year = fields.Selection([(num, str(num)) for num in range((datetime.now().year) - 5, (datetime.now().year) + 20)],
                            'Year', default=datetime.now().year)
    product_id = fields.Many2one('product.product', "Product")
    currency_id = fields.Many2one('res.currency', "Currency", default=lambda self: self.env.user.company_id.currency_id)
    actual_sales_target_qty_line_ids = fields.Many2many('sales.target.qty.line',string='Actual Sales Figure')
    
    # for test
    sales_target_product_line_ids = fields.Many2many('sales.target.product.line','crm_team_product_line','crm_team_id','product_line_id', string='Sale Quantity Target')
    
    sales_target_product_line = fields.One2many('sales.target.product.line','crm_team_id', string='Sale Quantity Target')
    actual_sales_target_product_line = fields.One2many('sales.target.product.line','crm_team_id', string='Actual Sales Figure')

    # sales_target_product_line_ref = fields.One2many('sales.target.product.line.ref','crm_team_id', string='Sale Quantity Target')
    
    # @api.onchange('sale_target_qty_year')
    # def _onnchange_sale_target_qty_year(self):
    #     member_list = []

    #     for res in self:
    #         # res.sales_target_product_line = []
    #         sales_target_product_line_ids = self.env['sales.target.product.line'].search([('sale_target_qty_year', '=', res.sale_target_qty_year)])
    #         print('\n sales_target_product_line ############## ',sales_target_product_line_ids)
            
    #         for line in res.sales_target_product_line:
    #             print('\n line ffffffffffff ',line)
    #             # line.unlink()
    #             line.write({'crm_team_id':False})

    #         # for line in sales_target_product_line_ids:
                
    #             # details = (0,0,{
    #             #              'product_id':line.product_id.id,
    #             #              'sale_target_qty_year':line.sale_target_qty_year,
    #             #              'crm_team_id':self.id,
    #             #              'salesperson_detail_id':line.salesperson_detail_id,
    #             #              't_january':line.t_january,
    #             #              't_february':line.t_february,
    #             #              't_march':line.t_march,
    #             #              't_may':line.t_may,
    #             #              't_june':line.t_june,
    #             #              't_july':line.t_july,
    #             #              't_august':line.t_august,
    #             #              't_september':line.t_september,
    #             #              't_october':line.t_october,
    #             #              't_november':line.t_november,
    #             #              't_december':line.t_december
    #             #         })
    #             # member_list.append(details)

    #             # res.write({'sales_target_product_line':[(4,line.product_line_id.id)]})
    #     # res['sales_target_product_line'] = member_list
    #     # res.sales_target_product_line = member_list

    #     # self.actual_sales_target_product_line= [(6,0,sales_target_product_line.ids)]
    #     # self.sales_target_product_line_ids= [(6,0,sales_target_product_line.ids)]
    #     # return res
    
    @api.model
    def create(self, vals):
        if "sales_target_product_line" in vals.keys():
            for line in vals['sales_target_product_line']:
                if line[0] == 0:
                    line[2]['created'] = True
         
        res = super(CrmTeam, self).create(vals)
        return res
    
    @api.multi
    def write(self, vals):
        if "sales_target_product_line" in vals.keys():
            for line in vals['sales_target_product_line']:
                if line[0] == 0:
                    line[2]['created'] = True

                if line[0] == 4:
                    cus4 = self.env['sales.target.product.line'].search([('id','=',line[1]),
                                    ('created','=',True)               ])
                    if cus4.sale_target_qty_year == self.sale_target_qty_year:
                        cus4.write({'active' : True})
                    else:
                        cus4.write({'active' : False})

                if line[0] == 2:
                    cus2 = self.env['sales.target.product.line'].search([('id','=',line[1]),('created','=',True)])
                    if 'sale_target_qty_year' in vals and  cus2.sale_target_qty_year == vals['sale_target_qty_year']:
                        cus2.write({'active' : True})
                    else:
                        cus2.write({'active' : False})
                
        res = super(CrmTeam, self).write(vals)
        return res
    
    @api.multi
    @api.onchange('sale_target_qty_year')
    def onchange1_sale_target_qty_year(self):
        for rec in self:
            sales_target_product_line1 = self.env['sales.target.product.line'].search([('sale_target_qty_year', '=', rec.sale_target_qty_year),
                        ('crm_team_id','=',self._origin.id),('active','=',False)])
            ids = []
            if sales_target_product_line1:
                for d1 in sales_target_product_line1:
                    c = 0
                    for d2 in sales_target_product_line1:
                        if d2.sale_target_qty_year == d1.sale_target_qty_year and d2.crm_team_id.id == d1.crm_team_id.id and \
                            d2.pt_january == d1.pt_january and d2.pt_february == d1.pt_february and \
                                d2.pt_march == d1.pt_march and d2.pt_april == d1.pt_april and d2.pt_may == d1.pt_may and d2.pt_june == d1.pt_june and \
                                d2.pt_july == d1.pt_july and d2.pt_august == d1.pt_august and d2.pt_september == d1.pt_september and d2.pt_october == d1.pt_october and d2.pt_november == d1.pt_november and \
                                d2.pt_december == d1.pt_december:
                            c += 1
                        if c >= 2:
                            ids.append(d2.id)
            if len(ids) != 0:
                records = self.env['sales.target.product.line'].search([('id','in',ids)])
                for line in records:
                    line.write({'created' : False})
            else:
                for inact in sales_target_product_line1:
                    inact.write({'active' : True,})
                    
            sales_target_product_line2 = self.env['sales.target.product.line'].search([('sale_target_qty_year', '=', rec.sale_target_qty_year),
                        ('crm_team_id','=',self._origin.id),('active','=',True)])

            if sales_target_product_line2:
                rec.sales_target_product_line = [(6,0,sales_target_product_line2.ids)]
            else:
                rec.sales_target_product_line = False
                
    @api.depends('member_ids', 'sale_target_qty_year','sales_target_product_line.product_id')
    @api.onchange('member_ids', 'sale_target_qty_year','sales_target_product_line.product_id')
    def onchange_qty_team_member_and_year(self):
        for record in self:
            sales_target_line_ids = []
            if not record.year: record.year = datetime.now().year

            for member_id in record.member_ids:
                team_id = self.env['crm.team'].search([('name', '=', record.name)], limit=1)
                sales_target_line = record.env['sales.target.qty.line'].search([('member_id', '=', member_id.id), ('year', '=', record.sale_target_qty_year),('product_id','=',record.product_id.id)], limit=1)
                if not sales_target_line and team_id:
                    sales_target_line = record.env['sales.target.qty.line'].create({
                        'member_id' : member_id.id,
                        'year' : record.sale_target_qty_year,
                        'product_id':record.product_id.id,
                        'crm_team_id' : team_id.id,
                    })

                sales_target_line_ids.append(sales_target_line.id)
            self.update({
                'sales_target_qty_line_ids': [(6, 0, sales_target_line_ids)],
                # 'actual_sales_target_qty_line_ids': [(6, 0, sales_target_line_ids)]
            })

    @api.constrains('member_ids', 'year_team')
    @api.onchange('member_ids', 'year_team')
    def onchange_qty_team_member(self):
        sales_qty_targets = self.env['sales.target.qty'].search(['&', ('year', '=', datetime.now().year), ('crm_team_id', '=', self.id),('product_id','=',self.product_id.id)], limit=1)
        if not sales_qty_targets:
            self.update({
                'sales_qty_targets': [(0, 0, {
                    'crm_team_id': self.id,
                    'year': datetime.now().year,
                    'product_id':self.product_id.id,
                })]
            })
        # sales_targets = self.sales_targets.browse([('year', '=', self.year_team)])

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CrmTeam, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                   submenu=submenu)
        if res.get('arch', False) and view_type == 'kanban':
            arch = fromstring(res.get('arch'))
            target = arch.findall(".//field[@name='invoiced']/../../..")
            if target[0].tag == 'div':
                add_xml = self.parse_sales_qty_view_for_view()
                if add_xml:
                    for element in add_xml:
                        target[0].append(element)
                    res['arch'] = tostring(arch)
        return res

    @api.model
    def parse_sales_qty_view_for_view(self):
        xml_string = ""
        flag = False
        res = []
        sales_teams = self.search([])
        cnt = 0
        for sales_team in sales_teams:
            sales_target_product_line_ids = self.env['sales.target.product.line'].search(
                [('crm_team_id', '=', sales_team.id), ('sale_target_qty_year', '=', sales_team.year)])
            all_line_ids = []

            for single_obj in sales_target_product_line_ids:
                for ln in self.env['sales.target.qty.line'].search([('product_id', '=', single_obj.product_id.id),
                                                                    ('year', '=', single_obj.sale_target_qty_year),
                                                                    ('line_product_id', '=',
                                                                     single_obj.salesperson_detail_id.id)]):
                    flag = True
                    if ln.product_id.id not in all_line_ids:
                        all_line_ids.append(ln.product_id.id)
                        xml_string += '<div class="row" style="height: 100px; ' \
                                      'margin-bottom: 60px; overflow-y: scroll;" ' \
                                      't-if="record.id.raw_value == %s"> <div><b> %s </b></div>' % (
                                          sales_team.id, ln.product_id.name)
                    cnt = 1
                    target_amount = {}
                    actual_amount = {}
                    target_amount['t_january'] = ln.t_january
                    target_amount['t_february'] = ln.t_february
                    target_amount['t_march'] = ln.t_march
                    target_amount['t_april'] = ln.t_april
                    target_amount['t_may'] = ln.t_may
                    target_amount['t_june'] = ln.t_june
                    target_amount['t_july'] = ln.t_july
                    target_amount['t_august'] = ln.t_august
                    target_amount['t_september'] = ln.t_september
                    target_amount['t_october'] = ln.t_october
                    target_amount['t_november'] = ln.t_november
                    target_amount['t_december'] = ln.t_december

                    actual_amount['a_january'] = ln.january
                    actual_amount['a_february'] = ln.february
                    actual_amount['a_march'] = ln.march
                    actual_amount['a_april'] = ln.april
                    actual_amount['a_may'] = ln.may
                    actual_amount['a_june'] = ln.june
                    actual_amount['a_july'] = ln.july
                    actual_amount['a_august'] = ln.august
                    actual_amount['a_september'] = ln.september
                    actual_amount['a_october'] = ln.october
                    actual_amount['a_november'] = ln.november
                    actual_amount['a_december'] = ln.december

                    current_target_month = 't_' + datetime.now().strftime('%B').lower()
                    current_actual_target = 'a_' + datetime.now().strftime('%B').lower()
                    current_target_amount = target_amount.get(current_target_month)
                    current_actual_amount = actual_amount.get(current_actual_target)
                    current_target = current_target_amount or 0

                    percent = int(current_actual_amount * 100 / current_target) if current_target else 100
                    color = '#cb2431' if current_actual_amount < current_target else '#1e9880'
                    xml_string += """
                                        <div class="col-xs-12" style="padding-top: 0px; padding-bottom: 0px;">
                                                                               <div class="o_progressbar">
                                                                                   <div class="o_progressbar_title" style="width:22%%">%s</div>
                                                                                   <div class="o_progress" style="width:60%%">
                                                                                       <div class="o_progressbar_complete" style="width: %s%% ; background-color: %s;"></div>
                                                                                   </div>
                                                                                   <div class="o_progressbar_value" style="width:18%%">%s / %s</div>
                                                                               </div>
                                                                           </div>
                                                                       """ % (
                    ln.member_id.name, percent, color, int(current_actual_amount), int(current_target))
                xml_string += "</div>"

        if flag:
            xml_string = "<div>"+xml_string+"</div>"
        else:
            xml_string = "<div></div>"
        res.append(fromstring(xml_string))
        return res if xml_string != [] else False


class SaleTargetQty(models.Model):
    _name = "sales.target.qty"

    @api.multi
    def get_sales_amount(self):
        return 0
        # months = ['january', 'february', 'march', 'april', 'may', 'jun', 'july', 'august', 'september', 'october',
        #           'november', 'december']
        # for record in self:
        #     if self.crm_team_id and self.crm_team_id.member_ids:
        #         self.env.cr.execute("""SELECT date_part( 'month', confirmation_date) as Month, SUM(amount_total) FROM sale_order WHERE user_id in %s and confirmation_date is not NULL and product_id = %s GROUP BY Month order by Month""",
        #                             (member_ids,self.product_id.id))
        #         results = self.env.cr.fetchall()
        #         data = {}
        #         map(lambda month: data.update({month: 0}), months)
        #         map(lambda result: data.update({months[int(result[0]) - 1]: result[1]}), results)
        #         map(lambda month: setattr(record, month, data[month]), months)
        #         member_ids = tuple(self.crm_team_id.member_ids.ids)

    crm_team_id = fields.Many2one('crm.team', string='Sale Team')
    year = fields.Selection([(num, str(num)) for num in range((datetime.now().year) - 5, (datetime.now().year) + 20)],
                            'Year', default=datetime.now().year, required=True, readonly=True)
    product_id = fields.Many2one('product.product', "Product")
    currency_id = fields.Many2one('res.currency', "Currency", default=lambda self: self.env.user.company_id.currency_id)

    t_january = fields.Float('January')
    t_february = fields.Float('February')
    t_march = fields.Float('March')
    t_april = fields.Float('April')
    t_may = fields.Float('May')
    t_june= fields.Float('Jun')
    t_july = fields.Float('July')
    t_august = fields.Float('August')
    t_september = fields.Float('September')
    t_october = fields.Float('October')
    t_november = fields.Float('November')
    t_december = fields.Float('December')



class SaleTargetQtyLine(models.Model):
    _name = "sales.target.qty.line"

    # crm_team_ids = fields.Many2many('crm.team', 'crm_team_sales_target_line_rel', 'crm_team_id', 'sales_target_line_id', string='Sale Team')
    crm_team_id = fields.Many2one('crm.team',string = "Sales Team")
    member_id = fields.Many2one('res.users', string='Sales Person')
    year = fields.Integer('Year')
    show_year = fields.Char('Year',compute="show_year_amount")
    product_id = fields.Many2one('product.product', string="Product")
    currency_id = fields.Many2one('res.currency', "Currency", default=lambda self: self.env.user.company_id.currency_id)

    january = fields.Float('January', compute="update_sale_amount")
    february = fields.Float('February', compute="update_sale_amount")
    march = fields.Float('March', compute="update_sale_amount")
    april = fields.Float('April', compute="update_sale_amount")
    may = fields.Float('May', compute="update_sale_amount")
    june = fields.Float('Jun', compute="update_sale_amount")
    july = fields.Float('July', compute="update_sale_amount")
    august = fields.Float('August', compute="update_sale_amount")
    september = fields.Float('September', compute="update_sale_amount")
    october = fields.Float('October', compute="update_sale_amount")
    november = fields.Float('November', compute="update_sale_amount")
    december = fields.Float('December', compute="update_sale_amount")

    t_january = fields.Float('January')
    t_february = fields.Float('February')
    t_march = fields.Float('March')
    t_april = fields.Float('April')
    t_may = fields.Float('May')
    t_june = fields.Float('June')
    t_july = fields.Float('July')
    t_august = fields.Float('August')
    t_september = fields.Float('September')
    t_october = fields.Float('October')
    t_november = fields.Float('November')
    t_december = fields.Float('December')

    current_amount = fields.Float('Sales Amount', compute="get_current_amount")
    current_tartget = fields.Float('Sales Target', compile="get_current_target")

    # ssss
    line_product_id = fields.Many2one('salesperson.detail',string="Product Line")

    @api.multi
    def update_sale_amount(self):
        months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
                  'november', 'december']
        for record in self:
            if record.product_id.id and record.year:
                self.env.cr.execute("""
                    SELECT date_part( 'month', line_confirmation_date) as Month, SUM(product_uom_qty)
                    FROM sale_order_line WHERE salesman_id = %s and date_part( 'year', line_confirmation_date) = %s and product_id = %s GROUP BY Month order by Month
                    """, (record.member_id.id, record.year , record.product_id.id))
                results = self.env.cr.fetchall()
                data = {}
                map(lambda month: data.update({month: 0}), months)
                map(lambda result: data.update({months[int(result[0]) - 1]: result[1]}), results)
                map(lambda month: setattr(record, month, data[month]), months)

    @api.multi
    def show_year_amount(self):
        for data in self:
            # data.show_year = str(data.year)
            data.show_year = str(data.line_product_id.sale_target_qty_year)
            data.year = data.line_product_id.sale_target_qty_year

    def get_current_target(self):
        return getattr(self, 't_' + datetime.now().strftime('%B').lower())

    def get_current_amount(self):
        if self.product_id:
            self.env.cr.execute("""            
                SELECT SUM(product_uom_qty) FROM sale_order_line WHERE salesman_id = %s and 
                date_part( 'year', line_confirmation_date) = %s and date_part( 'month', line_confirmation_date) = %s and product_id = %s """, (self.member_id.id, datetime.now().year, datetime.now().month,self.product_id.id))
            results = self.env.cr.fetchall()
            return results[0][0]

    @api.multi
    def update_sale_target(self, value):
        return setattr(self, 't_' + datetime.now().strftime('%B').lower(), value)


class SaleTargetProductLine(models.Model):
    _name = "sales.target.product.line"

    crm_team_id = fields.Many2one('crm.team',string="Crm Team")
    sale_target_qty_year = fields.Selection([(num, str(num)) for num in range((datetime.now().year) - 5, (datetime.now().year) + 20)],
                            'Year')
    product_id = fields.Many2one('product.product', "Product")
    currency_id = fields.Many2one('res.currency', "Currency", default=lambda self: self.env.user.company_id.currency_id)
    
    t_january = fields.Float('January', compute="total_month_qty")
    t_february = fields.Float('February', compute="total_month_qty")
    t_march = fields.Float('March', compute="total_month_qty")
    t_april = fields.Float('April', compute="total_month_qty")
    t_may = fields.Float('May', compute="total_month_qty")
    t_june= fields.Float('Jun', compute="total_month_qty")
    t_july = fields.Float('July', compute="total_month_qty")
    t_august = fields.Float('August', compute="total_month_qty")
    t_september = fields.Float('September', compute="total_month_qty")
    t_october = fields.Float('October', compute="total_month_qty")
    t_november = fields.Float('November', compute="total_month_qty")
    t_december = fields.Float('December', compute="total_month_qty")

    # save ---
    pt_january = fields.Float('January')
    pt_february = fields.Float('February')
    pt_march = fields.Float('March')
    pt_april = fields.Float('April')
    pt_may = fields.Float('May')
    pt_june= fields.Float('Jun')
    pt_july = fields.Float('July')
    pt_august = fields.Float('August')
    pt_september = fields.Float('September')
    pt_october = fields.Float('October')
    pt_november = fields.Float('November')
    pt_december = fields.Float('December')



    january = fields.Float('January', compute="total_month_qty")
    february = fields.Float('February', compute="total_month_qty")
    march = fields.Float('March', compute="total_month_qty")
    april = fields.Float('April', compute="total_month_qty")
    may = fields.Float('May', compute="total_month_qty")
    june = fields.Float('Jun', compute="total_month_qty")
    july = fields.Float('July', compute="total_month_qty")
    august = fields.Float('August', compute="total_month_qty")
    september = fields.Float('September', compute="total_month_qty")
    october = fields.Float('October', compute="total_month_qty")
    november = fields.Float('November', compute="total_month_qty")
    december = fields.Float('December', compute="total_month_qty")

    # sales_per_target_qty_line_ids = fields.One2many('sales.target.qty.line','product_line_id',string='Sale Quantity Target')
    salesperson_detail_id = fields.Many2one('salesperson.detail',string="Salesperson Detail")
    created = fields.Boolean("Created?")
    active = fields.Boolean("Active",default=True,)
    
    @api.model
    def create(self,vals):
        res = super(SaleTargetProductLine,self).create(vals)
        if "sale_target_qty_year" in vals.keys():
            sale_target_qty_year = self.env['sales.target.product.line'].search_count([('sale_target_qty_year','=',vals['sale_target_qty_year']),('crm_team_id','=',vals['crm_team_id'])])
            if sale_target_qty_year > 1:
                yr = self.env['sales.target.product.line'].search([('sale_target_qty_year','=',vals['sale_target_qty_year']),('crm_team_id','=',vals['crm_team_id']),('created','=',False)],order="id desc")
                if yr:
                    yr.unlink()
        if res:
            res.sale_target_qty_year = res.crm_team_id.sale_target_qty_year
        return res
            
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.created == False:
                return super(SaleTargetProductLine, self).unlink() 
            
    @api.multi
    def total_month_qty(self):
        for res in self:
            sum_t_january = sum_t_february = sum_t_march = sum_t_april = sum_t_may = sum_t_june = sum_t_july = sum_t_august = sum_t_september = sum_t_october = sum_t_november = sum_t_december = 0 
            sum_january = sum_february = sum_march = sum_april = sum_may = sum_june = sum_july = sum_august = sum_september = sum_october = sum_november = sum_december = 0 
            
            for line in res.salesperson_detail_id.sales_per_target_qty_line_ids:
                sum_t_january += line.t_january
                sum_t_february += line.t_february
                sum_t_march += line.t_march
                sum_t_april += line.t_april
                sum_t_may += line.t_may
                sum_t_june += line.t_june
                sum_t_july += line.t_july
                sum_t_august += line.t_august
                sum_t_september += line.t_september
                sum_t_october += line.t_october
                sum_t_november += line.t_november
                sum_t_december += line.t_december

            res.t_january = sum_t_january
            res.t_february = sum_t_february
            res.t_march = sum_t_march
            res.t_april = sum_t_april
            res.t_may = sum_t_may
            res.t_june = sum_t_june
            res.t_july = sum_t_july
            res.t_august = sum_t_august
            res.t_september = sum_t_september
            res.t_october = sum_t_october
            res.t_november = sum_t_november
            res.t_december = sum_t_december

            res.write({'pt_january': sum_t_january})
            res.write({'pt_february': sum_t_february})
            res.write({'pt_march': sum_t_march})
            res.write({'pt_april': sum_t_april})
            res.write({'pt_may': sum_t_may})
            res.write({'pt_june': sum_t_june})
            res.write({'pt_july': sum_t_july})
            res.write({'pt_august': sum_t_august})
            res.write({'pt_september': sum_t_september})
            res.write({'pt_october': sum_t_october})
            res.write({'pt_november': sum_t_november})
            res.write({'pt_december': sum_t_december})

            for line in res.salesperson_detail_id.actual_sales_per_target_qty_line_ids:
                sum_january += line.january
                sum_february += line.february
                sum_march += line.march
                sum_april += line.april
                sum_may += line.may
                sum_june += line.june
                sum_july += line.july
                sum_august += line.august
                sum_september += line.september
                sum_october += line.october
                sum_november += line.november
                sum_december += line.december


            res.january = sum_january
            res.february = sum_february
            res.march = sum_march
            res.april = sum_april
            res.may = sum_may
            res.june = sum_june
            res.july = sum_july
            res.august = sum_august
            res.september = sum_september
            res.october = sum_october
            res.november = sum_november
            res.december = sum_december
            
    @api.multi
    def show_detail(self):

        view_id = self.env.ref('sales_target_qty.show_in_detail_form_view').id
        context = self._context.copy()
        context['default_product_id'] = self.product_id.id or False 
        context['default_sale_target_qty_year'] = self.crm_team_id.sale_target_qty_year 
        context['default_first'] = True 
        res = {
                'name':'Product Detail',
                'view_type':'form',
                'view_mode':'tree',
                'views':[(view_id,'form')],
                'res_model':'salesperson.detail',
                'type':'ir.actions.act_window',
                'target':'new',
                'context':context,
                # 'flags': {'form': {'action_buttons': False}},
            }

        if self.salesperson_detail_id:
            res['res_id'] = self.salesperson_detail_id.id
        return res

    @api.multi
    def show_detail_actual(self):

        view_id = self.env.ref('sales_target_qty.show_in_detail_form_view').id
        context = self._context.copy()
        context['default_product_id'] = self.product_id.id or False 
        context['default_sale_target_qty_year'] = self.crm_team_id.sale_target_qty_year 
        
        context['is_actual_target'] = True 
        res = {
                'name':'Product Detail',
                'view_type':'form',
                'view_mode':'tree',
                'views':[(view_id,'form')],
                'res_model':'salesperson.detail',
                'type':'ir.actions.act_window',
                'target':'new',
                'context':context,
                # 'flags': {'form': {'action_buttons': False}},
            }

        if self.salesperson_detail_id:
            res['res_id'] = self.salesperson_detail_id.id
        return res

