# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api , _
import xlsxwriter
import StringIO
import xlwt
import locale
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import base64

class SalesTeamQtyReport(models.TransientModel):
    _name = 'sales.team.qty.report'

    year = fields.Selection([(num, str(num)) for num in range((datetime.now().year) - 10, (datetime.now().year) + 11)],
                            string='Year', default=datetime.now().year)
    product_id = fields.Many2one('product.product', string="Product")
    crm_team_id = fields.Many2one("crm.team", string="Sales Team")
    product_ids = fields.Many2many('product.product','rel_st_qty_report_prodcut_product','qty_report_id','product_product_id', string="Product")

    @api.multi
    def action_generate_report(self):
        # row = 1
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet1')
        
        bold_format = workbook.add_format({'bold': 1,'align': 'center'})
        merge_format = workbook.add_format({'bold': 1, 'border': 0, 'align': 'center', 'valign': 'vcenter','font_size':16 })
        sales_team_name = str(self.crm_team_id.name)+" Team"
        worksheet.merge_range(1,0,1,1,sales_team_name,merge_format)
        worksheet.set_column(1, 0, 18)

        row = 2
        col = 1
        for product in self.product_ids:
            list = []
            data = {}
            product_list = []
            sales_target_pro_line =  self.env['sales.target.product.line'].search([('crm_team_id','=',self.crm_team_id.id),('product_id','=',product.id),('sale_target_qty_year','=',self.year)])
            # sales_target_pro_line =  self.env['sales.target.product.line'].search([('crm_team_id','=',self.crm_team_id.id),('sale_target_qty_year','=',self.year)])
            for pro_line in sales_target_pro_line:
                data = {'product':pro_line.product_id.name}
                member_list = []
                for member in pro_line.salesperson_detail_id.sales_per_target_qty_line_ids:
                    product_list.append(member.product_id.id)
                    # Actual sale data
                    self.env.cr.execute("""
                    SELECT date_part( 'month', line_confirmation_date) as Month, SUM(product_uom_qty)
                    FROM sale_order_line WHERE salesman_id = %s and date_part( 'year', line_confirmation_date) = %s and product_id = %s GROUP BY Month order by Month
                    """, (member.member_id.id, self.year , product.id))

                    results = self.env.cr.fetchall()

                    sales_target_pro_line_ids = self.env['sales.target.qty.line'].search([('year','=',self.year),('product_id','=',product.id),('member_id','=',member.member_id.id)])
                    # sales_target_pro_line_ids = self.env['sales.target.qty.line'].search([('year','=',self.year),('member_id','=',member.member_id.id)])


                    sale_01 = sale_02 = sale_03 = sale_04 = sale_05 = sale_06 = sale_07 = sale_08 = sale_09 = sale_10 = sale_11 = sale_12 = '' 
                    detail = {}

                    for pro_sale in sales_target_pro_line_ids:
                        sale_01 = pro_sale.t_january
                        sale_02 = pro_sale.t_february
                        sale_03 = pro_sale.t_march
                        sale_04 = pro_sale.t_april
                        sale_05 = pro_sale.t_may
                        sale_06 = pro_sale.t_june
                        sale_07 = pro_sale.t_july
                        sale_08 = pro_sale.t_august
                        sale_09 = pro_sale.t_september
                        sale_10 = pro_sale.t_october
                        sale_11 = pro_sale.t_november
                        sale_12 = pro_sale.t_december

                    detail.update({
                                'member_id':member.member_id.name,
                                'sale_01':sale_01,
                                'sale_02':sale_02,
                                'sale_03':sale_03,
                                'sale_04':sale_04,
                                'sale_05':sale_05,
                                'sale_06':sale_06,
                                'sale_07':sale_07,
                                'sale_08':sale_08,
                                'sale_09':sale_09,
                                'sale_10':sale_10,
                                'sale_11':sale_11,
                                'sale_12':sale_12
                    })

                    a_sale_01 = a_sale_02 = a_sale_03 = a_sale_04 = a_sale_05 = a_sale_06 = a_sale_07 = a_sale_08 = a_sale_09 = a_sale_10 = a_sale_11 = a_sale_12 = 0 
                    
                    for month in results:
                        if(month[0] == 1.0):
                            a_sale_01 = month[1]

                        if(month[0] == 2.0):
                            a_sale_02 = month[1]

                        if(month[0] == 3.0):
                            a_sale_03 = month[1]

                        if(month[0] == 4.0):
                            a_sale_04 = month[1]

                        if(month[0] == 5.0):
                            a_sale_05 = month[1]

                        if(month[0] == 6.0):
                            a_sale_06 = month[1]
                        
                        if(month[0] == 7.0):
                            a_sale_07 = month[1]

                        if(month[0] == 8.0):
                            a_sale_08 = month[1]

                        if(month[0] == 9.0):
                            a_sale_09 = month[1]

                        if(month[0] == 10.0):
                            a_sale_10 = month[1]

                        if(month[0] == 11.0):
                            a_sale_11 = month[1]

                        if(month[0] == 12.0):
                            a_sale_12 = month[1]


                    detail.update({
                                'member_id':member.member_id.name,
                                'a_sale_01':a_sale_01,
                                'a_sale_02':a_sale_02,
                                'a_sale_03':a_sale_03,
                                'a_sale_04':a_sale_04,
                                'a_sale_05':a_sale_05,
                                'a_sale_06':a_sale_06,
                                'a_sale_07':a_sale_07,
                                'a_sale_08':a_sale_08,
                                'a_sale_09':a_sale_09,
                                'a_sale_10':a_sale_10,
                                'a_sale_11':a_sale_11,
                                'a_sale_12':a_sale_12,
                    })
                    
                    member_list.append(detail)
                    # worksheet.write(row, 0, member.member_id.name)
                    # row = row + 1
                

                dict = {'member':member_list}
                data.update(dict)
                list.append(data)


            if product.id not in product_list:
                member_list = []
                data = {'product':product.name}
                crm_team =  self.env['crm.team'].search([('id','=',self.crm_team_id.id)])
                for crm in crm_team:
                    for member in crm.member_ids:
                        detail = {}
                        sale_01 = sale_02 = sale_03 = sale_04 = sale_05 = sale_06 = sale_07 = sale_08 = sale_09 = sale_10 = sale_11 = sale_12 = '' 

                        detail.update({
                                        'member_id':member.name,
                                        'sale_01':sale_01,
                                        'sale_02':sale_02,
                                        'sale_03':sale_03,
                                        'sale_04':sale_04,
                                        'sale_05':sale_05,
                                        'sale_06':sale_06,
                                        'sale_07':sale_07,
                                        'sale_08':sale_08,
                                        'sale_09':sale_09,
                                        'sale_10':sale_10,
                                        'sale_11':sale_11,
                                        'sale_12':sale_12
                                })

                        a_sale_01 = a_sale_02 = a_sale_03 = a_sale_04 = a_sale_05 = a_sale_06 = a_sale_07 = a_sale_08 = a_sale_09 = a_sale_10 = a_sale_11 = a_sale_12 = 0 

                        detail.update({
                                        'member_id':member.name,
                                        'a_sale_01':a_sale_01,
                                        'a_sale_02':a_sale_02,
                                        'a_sale_03':a_sale_03,
                                        'a_sale_04':a_sale_04,
                                        'a_sale_05':a_sale_05,
                                        'a_sale_06':a_sale_06,
                                        'a_sale_07':a_sale_07,
                                        'a_sale_08':a_sale_08,
                                        'a_sale_09':a_sale_09,
                                        'a_sale_10':a_sale_10,
                                        'a_sale_11':a_sale_11,
                                        'a_sale_12':a_sale_12,
                            })
                        
                        member_list.append(detail)

                    dict = {'member':member_list}
                    data.update(dict)
                    list.append(data)

            for pro_detail in list:

                sales_header = "Sales Team Qty ("+str(pro_detail.get('product'))+") Report on "+str(self.year)


                font_size_format = workbook.add_format()
                font_size_format.set_font_size(10.5)

                worksheet.merge_range(row+1,0,row+1,4,sales_header,merge_format)
            
                cell_format = workbook.add_format({'align': 'center',
                                                   'valign': 'vcenter',
                                                   'bold':1,
                                                   'font':18
                                                   })
                row = row + 2
                worksheet.merge_range(row+1,1,row+1,2,"January", cell_format)
                worksheet.merge_range(row+1,3,row+1,4,"February", cell_format)
                worksheet.merge_range(row+1,5,row+1,6,"March", cell_format)
                worksheet.merge_range(row+1,7,row+1,8,"April", cell_format)
                worksheet.merge_range(row+1,9,row+1,10,"May", cell_format)
                worksheet.merge_range(row+1,11,row+1,12,"June", cell_format)
                worksheet.merge_range(row+1,13,row+1,14,"July", cell_format)
                worksheet.merge_range(row+1,15,row+1,16,"August", cell_format)
                worksheet.merge_range(row+1,17,row+1,18,"September", cell_format)
                worksheet.merge_range(row+1,19,row+1,20,"October", cell_format)
                worksheet.merge_range(row+1,21,row+1,22,"November", cell_format)
                worksheet.merge_range(row+1,23,row+1,24,"December", cell_format)

               

                row = row + 2
                worksheet.write(row, 0, 'Sales Person', bold_format)
                worksheet.set_column(row, 0, 18)

                worksheet.write(row, 1, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 1, 18)

                worksheet.write(row, 2, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 2, 18)
                
                worksheet.write(row, 3, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 3, 18)

                worksheet.write(row, 4, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 4, 18)

                worksheet.write(row, 5, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 5, 18)

                worksheet.write(row, 6, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 6, 18)

                worksheet.write(row, 7, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 7, 18)

                worksheet.write(row, 8, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 8, 18)

                worksheet.write(row, 9, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 9, 18)

                worksheet.write(row, 10, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 10, 18)

                worksheet.write(row, 11, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 11, 18)

                worksheet.write(row, 12, 'Sales  Qty Target', bold_format)
                worksheet.set_column(row, 12, 18)

                worksheet.write(row, 13, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 13, 18)

                worksheet.write(row, 14, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 14, 18)

                worksheet.write(row, 15, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 15, 18)

                worksheet.write(row, 16, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 16, 18)

                worksheet.write(row, 17, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 17, 18)

                worksheet.write(row, 18, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 18, 18)

                worksheet.write(row, 19, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 19, 18)

                worksheet.write(row, 20, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 20, 18)

                worksheet.write(row, 21, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 21, 18)

                worksheet.write(row, 22, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 22, 18)

                worksheet.write(row, 23, 'Actual Qty Target', bold_format)
                worksheet.set_column(row, 23, 18)

                worksheet.write(row, 24, 'Sales Qty Target', bold_format)
                worksheet.set_column(row, 24, 18)

                for pro_line in pro_detail.get('member'):
                    worksheet.write(row+1, 0, pro_line.get('member_id'))
                    worksheet.write(row+1, 1, pro_line.get('a_sale_01'))
                    worksheet.write(row+1, 3, pro_line.get('a_sale_02'))
                    worksheet.write(row+1, 5, pro_line.get('a_sale_03'))
                    worksheet.write(row+1, 7, pro_line.get('a_sale_04'))
                    worksheet.write(row+1, 9, pro_line.get('a_sale_05'))
                    worksheet.write(row+1, 11, pro_line.get('a_sale_06'))
                    worksheet.write(row+1, 13, pro_line.get('a_sale_07'))
                    worksheet.write(row+1, 15, pro_line.get('a_sale_08'))
                    worksheet.write(row+1, 17, pro_line.get('a_sale_09'))
                    worksheet.write(row+1, 19, pro_line.get('a_sale_10'))
                    worksheet.write(row+1, 21, pro_line.get('a_sale_11'))
                    worksheet.write(row+1, 23, pro_line.get('a_sale_12'))
                    
                    worksheet.write(row+1, 2, pro_line.get('sale_01'))
                    worksheet.write(row+1, 4, pro_line.get('sale_02'))
                    worksheet.write(row+1, 6, pro_line.get('sale_03'))
                    worksheet.write(row+1, 8, pro_line.get('sale_04'))
                    worksheet.write(row+1, 10, pro_line.get('sale_05'))
                    worksheet.write(row+1, 12, pro_line.get('sale_06'))
                    worksheet.write(row+1, 14, pro_line.get('sale_07'))
                    worksheet.write(row+1, 16, pro_line.get('sale_08'))
                    worksheet.write(row+1, 18, pro_line.get('sale_09'))
                    worksheet.write(row+1, 20, pro_line.get('sale_10'))
                    worksheet.write(row+1, 22, pro_line.get('sale_11'))
                    worksheet.write(row+1, 24, pro_line.get('sale_12'))
                    row = row + 1
                row = row + 2


        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'SalesQtyTargetReport', 'datas_fname': 'SalesQtyTargetReport.xlsx', 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
        }

SalesTeamQtyReport()