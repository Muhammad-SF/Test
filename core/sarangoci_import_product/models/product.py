from odoo import models , fields ,api,_,exceptions
import base64
import cStringIO
import xlwt
from io import BytesIO
from xlrd import open_workbook
from datetime import datetime,timedelta,date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class timesheet_line(models.Model):
    _name = 'export.import.product'

    import_or_export = fields.Selection(
        [('import', 'Import'),
         ('export', 'Export'),
         ], 'Import/Export', default="import")
    export_data     = fields.Binary("Export File")
    name            = fields.Char('File Name', readonly=True)
    import_data     = fields.Binary("Import File")
    state           = fields.Selection(
                                [('choose', 'choose'),
                                 ('get', 'get'),
                                 ('result', 'Result'),
                                 ], default='choose')
    error_log       = fields.Text("Error")
    export_error_log = fields.Text("Export Error")
    line_create     = fields.Integer("Total Line Create")
    line_update     = fields.Integer("Total Line Update")
    line_error      = fields.Integer("Total Line Error")

    @api.multi
    def import_export_product(self):
        ctx             = self._context.copy()
        active_id       = ctx.get('active_id')
        product         = self.env['product.product']
        line_create     = 0
        line_update     = 0
        self.ensure_one()
        if self.import_or_export == 'import':
            data = base64.b64decode(self.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            all_datas = []
            count = 0
            error = 0
            update = 0
            # salesperson_id = self.env['res.users'].search([('name','=','Deepa SIVAGHANTHAM')]).id
            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    header = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                else:
                    row = (
                    map(lambda row: isinstance(row.value, unicode) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                    if row[0]:
                        product_id = self.env['product.product'].search([('name','=',row[0].strip())])
                        if not product_id:
                            product_data = {
                                'name'      : row[0].strip(),
                                'list_price': row[6] or 0,
                                'standard_price': row[7] or 0,
                                'description_sale' : row[8] or '',
                                'description_purchase' : row[9] or '',
                                'description_picking' : row[10] or '',
                                'route_ids'         : [],
                            }
                            if row[1]:
                                route_list = row[1].strip().split(',')
                                for route in route_list:
                                    if route.strip() == 'Buy':
                                        buy = self.env['stock.location.route'].search([('name','=','Buy')])
                                        if buy:
                                            product_data['route_ids'].append((4,buy.id))
                                    if route.strip() == 'Manufacture':
                                        manu = self.env['stock.location.route'].search([('name', '=', 'Manufacture')])
                                        if manu:
                                            product_data['route_ids'].append((4, manu.id))
                                    if route.strip() == 'Make To Order':
                                        order = self.env['stock.location.route'].search([('name', '=', 'Make To Order')])
                                        if order:
                                            product_data['route_ids'].append((4, order.id))
                            if row[2]:
                                if row[2].strip() == 'Stockable Product':
                                    product_data.update({'type':'product'})
                                elif row[2].strip() == 'Service':
                                    product_data.update({'type': 'service'})
                                elif row[2].strip() == 'Consumable':
                                    product_data.update({'type': 'consu'})
                            if row[3]:
                                categ_id = self.env['product.category'].search([('name','=',row[3].split('/')[-1].strip())],limit=1)
                                if categ_id:
                                    product_data.update({'categ_id': categ_id.id})
                                else:
                                    for i in range(0,len(row[3].split('/'))):
                                        categ = self.env['product.category'].search([('name', '=', row[3].split('/')[i].strip())], limit=1)
                                        if not categ:
                                            new_categ = self.env['product.category'].create({'name':row[3].split('/')[i].strip()})
                                            if (i-1) >= 0:
                                                new_categ.write({'parent_id': self.env['product.category'].search([('name', '=', row[3].split('/')[i-1].strip())], limit=1).id})
                            if row[4]:
                                uom_id  = self.env['product.uom'].search([('name','=',row[4].strip())],limit=1)
                                if uom_id:
                                    product_data.update({'uom_id': uom_id.id})
                            if row[5]:
                                uom_po_id  = self.env['product.uom'].search([('name','=',row[5].strip())],limit=1)
                                if uom_po_id:
                                    product_data.update({'uom_po_id': uom_po_id.id})
                            if row[11]:
                                att = self.env['product.attribute'].search([('name','=',row[11].strip())],limit=1)
                                if att:
                                    product_data.update({'attribute_line_ids': [(0,0,{'attribute_id': att.id,'value_ids': [(6,0,[])]})]})
                                else:
                                    product_data.update({'attribute_line_ids': [
                                        (0, 0, {'attribute_id': self.env['product.attribute'].create({'name':row[11].strip()}).id, 'value_ids': [(6, 0, [])]})]})
                            if row[12]:
                                vendor = self.env['res.partner'].search([('name','=',row[12].strip())],limit=1)
                                if vendor:
                                    product_data.update({'seller_ids': [(
                                    0, 0, {'name': vendor.id, 'min_qty': float(row[13]) if row[13] else 0,'price':float(row[14]) if row[14] else 0,'delay':float(row[15]) if row[15] else 1})]})
                            try:
                                product = product.create(product_data)
                                count += 1
                            except:
                                error += 1
                        else:
                            update_data = {
                                'name': row[0].strip(),
                                'list_price': row[6] or 0,
                                'standard_price': row[7] or 0,
                                'description_sale': row[8] or '',
                                'description_purchase': row[9] or '',
                                'description_picking': row[10] or '',
                            }
                            if row[1]:
                                route_list = row[1].strip().split(',')
                                for route in route_list:
                                    if route.strip() == 'Buy':
                                        buy = self.env['stock.location.route'].search([('name','=','Buy')])
                                        if buy:
                                            product_data['route_ids'].append((4,buy.id))
                                    if route.strip() == 'Manufacture':
                                        manu = self.env['stock.location.route'].search([('name', '=', 'Manufacture')])
                                        if manu:
                                            product_data['route_ids'].append((4, manu.id))
                                    if route.strip() == 'Make To Order':
                                        order = self.env['stock.location.route'].search([('name', '=', 'Make To Order')])
                                        if order:
                                            product_data['route_ids'].append((4, order.id))

                            if row[2]:
                                if row[2].strip() == 'Stockable Product':
                                    update_data.update({'type': 'product'})
                                elif row[2].strip() == 'Service':
                                    update_data.update({'type': 'service'})
                                elif row[2].strip() == 'Consumable':
                                    update_data.update({'type': 'consu'})
                            if row[4]:
                                uom_id = self.env['product.uom'].search([('name', '=', row[4].strip())], limit=1)
                                if uom_id:
                                    update_data.update({'uom_id': uom_id.id})
                            if row[5]:
                                uom_po_id = self.env['product.uom'].search([('name', '=', row[5].strip())], limit=1)
                                if uom_po_id:
                                    update_data.update({'uom_po_id': uom_po_id.id})
                            if row[12]:
                                vendor = self.env['res.partner'].search([('name', '=', row[12].strip())], limit=1)
                                if vendor:
                                    update_data.update({'seller_ids': [(4, self.env['product.supplierinfo'].create({'name': vendor.id,
                                                                                                'min_qty': float(row[13]) if row[13] else 0,
                                                                                                'price': float(row[14]) if row[14] else 0,
                                                                                                'delay': float(row[15]) if row[15] else 1}).id)]})
                            if row[3]:
                                categ_id = self.env['product.category'].search([('name', '=', row[3].split('/')[-1].strip())], limit=1)
                                if categ_id:
                                    update_data.update({'categ_id': categ_id.id})
                                else:
                                    for i in range(0, len(row[3].split('/'))):
                                        categ = self.env['product.category'].search(
                                            [('name', '=', row[3].split('/')[i].strip())], limit=1)
                                        if not categ:
                                            new_categ = self.env['product.category'].create(
                                                {'name': row[3].split('/')[i].strip()})
                                            if (i - 1) >= 0:
                                                new_categ.write({'parent_id': self.env['product.category'].search(
                                                    [('name', '=', row[3].split('/')[i-1].strip())], limit=1).id})
                                    new_categ_id = self.env['product.category'].search([('name', '=', row[3].split('/')[-1].strip())], limit=1)
                                    update_data.update({'categ_id': new_categ_id.id})
                            try:
                                product_id.write(update_data)
                                if row[11]:
                                    att = self.env['product.attribute'].search([('name', '=', row[11].strip())],limit=1)
                                    if att:
                                        product_id.product_tmpl_id.write({'attribute_line_ids': [(4, self.env[
                                            'product.attribute.line'].create(
                                            {'product_tmpl_id': product_id.product_tmpl_id.id, 'attribute_id': att.id,
                                             'value_ids': [(6, 0, [])]}).id)]})
                                    else:
                                        product_id.product_tmpl_id.write({'attribute_line_ids': [(4, self.env[
                                            'product.attribute.line'].create(
                                            {'product_tmpl_id': product_id.product_tmpl_id.id,
                                             'attribute_id': self.env['product.attribute'].create({'name':row[11].strip()}).id,
                                             'value_ids': [(6, 0, [])]}).id)]})
                                update += 1
                            except:
                                error += 1
            line_create = count
            line_error  = error
            line_update = update
            # self.error_log = al_error
            self.state = 'result'
            # self.line_update = line_update
            self.line_create = line_create
            self.line_update = line_update
            self.line_error = line_error
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'export.import.product',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }

        else:
            output = cStringIO.StringIO()
            # output = BytesIO()
            all_error = ''
            book = xlwt.Workbook()
            ws = book.add_sheet('sheet-1')
            # ws.write(0, 0,  )
            final_data  = []
            # orders      = self._context.get('active_ids')
            product_ids = []
            header_name = ['Product Name','Routes', 'Product Type','Internal Category','Unit of Measure','Purchase Unit of Measure','Sale Price','Cost','Description for Quotation','Description for Vendor','Description for Pickings','Attribute','Vendor','Minimal Quantity','Price','Delivery Lead Time']
            if self._context.get('active_ids',False) and self._context.get('active_model',False) == 'product.template':
                product_ids = self.env['product.template'].browse(self._context.get('active_ids',False))
            final_data.append(header_name)
            for product in product_ids:
                export_row = []
                if product.seller_ids:
                    for vendor in product.seller_ids:
                        if product.attribute_line_ids:
                            for att in product.attribute_line_ids:
                                export_row = []
                                export_row.append(product.name or '')
                                if product.route_ids:
                                    name =''
                                    count = 1
                                    for route in product.route_ids:
                                        name += route.name
                                        if len(product.route_ids) > count:
                                            name += ','
                                        count += 1
                                    export_row.append(name)
                                else:
                                    export_row.append('')
                                if product.type == 'consu':
                                    export_row.append('Consumable')
                                elif product.type == 'service':
                                    export_row.append('Service')
                                elif product.type == 'product':
                                    export_row.append('Stockable Product')
                                # export_row.append(product.type or '')
                                export_row.append(product.categ_id.display_name or '')
                                export_row.append(product.uom_id.name or '')
                                export_row.append(product.uom_po_id.name or '')
                                export_row.append(product.list_price or '')
                                export_row.append(product.standard_price or '')
                                export_row.append(product.description_sale or '')
                                export_row.append(product.description_purchase or '')
                                export_row.append(product.description_picking or '')
                                export_row.append(att.attribute_id.name or '')
                                export_row.append(vendor.name or '')
                                export_row.append(vendor.min_qty or '')
                                export_row.append(vendor.price or '')
                                export_row.append(vendor.delay or '')
                                final_data.append(export_row)
                        else:
                            export_row = []
                            export_row.append(product.name or '')
                            if product.route_ids:
                                name = ''
                                count = 1
                                for route in product.route_ids:
                                    name += route.name
                                    if len(product.route_ids) > count:
                                        name += ','
                                    count += 1
                                export_row.append(name)
                            else:
                                export_row.append('')
                            if product.type == 'consu':
                                export_row.append('Consumable')
                            elif product.type == 'service':
                                export_row.append('Service')
                            elif product.type == 'product':
                                export_row.append('Stockable Product')
                            # export_row.append(product.type or '')
                            export_row.append(product.categ_id.display_name or '')
                            export_row.append(product.uom_id.name or '')
                            export_row.append(product.uom_po_id.name or '')
                            export_row.append(product.list_price or '')
                            export_row.append(product.standard_price or '')
                            export_row.append(product.description_sale or '')
                            export_row.append(product.description_purchase or '')
                            export_row.append(product.description_picking or '')
                            export_row.append('')
                            export_row.append(vendor.name.name or '')
                            export_row.append(vendor.min_qty or '')
                            export_row.append(vendor.price or '')
                            export_row.append(vendor.delay or '')
                            final_data.append(export_row)
                else:
                    if product.attribute_line_ids:
                        for att in product.attribute_line_ids:
                            export_row = []
                            export_row.append(product.name or '')
                            if product.route_ids:
                                name = ''
                                count = 1
                                for route in product.route_ids:
                                    name += route.name
                                    if len(product.route_ids) > count:
                                        name += ','
                                    count += 1
                                export_row.append(name)
                            else:
                                export_row.append('')
                            if product.type == 'consu':
                                export_row.append('Consumable')
                            elif product.type == 'service':
                                export_row.append('Service')
                            elif product.type == 'product':
                                export_row.append('Stockable Product')
                            # export_row.append(product.type or '')
                            export_row.append(product.categ_id.display_name or '')
                            export_row.append(product.uom_id.name or '')
                            export_row.append(product.uom_po_id.name or '')
                            export_row.append(product.list_price or '')
                            export_row.append(product.standard_price or '')
                            export_row.append(product.description_sale or '')
                            export_row.append(product.description_purchase or '')
                            export_row.append(product.description_picking or '')
                            export_row.append(att.attribute_id.name or '')
                            export_row.append('')
                            export_row.append('')
                            export_row.append('')
                            export_row.append('')
                            final_data.append(export_row)
                    else:
                        export_row = []
                        export_row.append(product.name or '')
                        if product.route_ids:
                            name = ''
                            count = 1
                            for route in product.route_ids:
                                name += route.name
                                if len(product.route_ids) > count:
                                    name += ','
                                count += 1
                            export_row.append(name)
                        else:
                            export_row.append('')
                        if product.type == 'consu':
                            export_row.append('Consumable')
                        elif product.type == 'service':
                            export_row.append('Service')
                        elif product.type == 'product':
                            export_row.append('Stockable Product')
                        # export_row.append(product.type or '')
                        export_row.append(product.categ_id.display_name or '')
                        export_row.append(product.uom_id.name or '')
                        export_row.append(product.uom_po_id.name or '')
                        export_row.append(product.list_price or '')
                        export_row.append(product.standard_price or '')
                        export_row.append(product.description_sale or '')
                        export_row.append(product.description_purchase or '')
                        export_row.append(product.description_picking or '')
                        export_row.append('')
                        export_row.append('')
                        export_row.append('')
                        export_row.append('')
                        export_row.append('')
                        final_data.append(export_row)

                # final_data.append(export_row)

            for i, l in enumerate(final_data):
                for j, col in enumerate(l):
                    ws.write(i, j, col)
            book.save(output)
            self.export_data = base64.b64encode(output.getvalue())
            self.name = "%s%s" % ('export_product', '.xls')
            self.state = 'get'
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'export.import.product',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }

    @api.multi
    def action_done(self):
        return {
            'type': 'ir.actions.act_window_close'
        }