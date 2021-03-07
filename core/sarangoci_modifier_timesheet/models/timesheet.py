from odoo import models , fields ,api,_,exceptions
import base64
import cStringIO
import xlwt
from io import BytesIO
from xlrd import open_workbook
from datetime import datetime,timedelta,date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class timesheet_line(models.Model):
    _name = 'export.import.account.analytic.line'

    import_or_export = fields.Selection(
        [('import', 'Import'),
         ('export', 'Export'),
         ], 'Import/Export', default="import")
    export_data     = fields.Binary("Export File")
    name            = fields.Char('File Name', readonly=True)
    import_data     = fields.Binary("Import File")
    project_id      = fields.Many2one('project.project','Project')
    state           = fields.Selection(
                                [('choose', 'choose'),
                                 ('get', 'get'),
                                 ('result', 'Result'),
                                 ], default='choose')
    error_log       = fields.Text("Error")
    export_error_log = fields.Text("Export Error")
    line_create     = fields.Integer("Total Line Create")
    line_update     = fields.Integer("Total Line Update")
    date_from       = fields.Date('Date From')
    date_to         = fields.Date('Date To')
    employee_ids    = fields.Many2many('hr.employee',string='Employee')

    @api.multi
    def import_export_timesheet(self):
        ctx             = self._context.copy()
        active_id       = ctx.get('active_id')
        account         = self.env['account.analytic.account']
        line            = self.env['account.analytic.line']
        project_id      = self.env['project.project']
        line_create     = 0
        line_update     = 0
        self.ensure_one()
        if self.import_or_export == 'import':
            data = base64.b64decode(self.import_data)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            all_datas = []
            count = 0
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
                        employee = self.env['hr.employee'].search(
                            [('employee_id', '=', row[0].split('.')[0]), ('name', '=', row[1])])
                        if not employee:
                            employee_data = {
                                'name': row[1],
                                'employee_id': row[0].split('.')[0],
                                'gender': False,
                                'join_date': str(date.today()),
                                'work_email': row[2],
                            }
                            employee = self.env['hr.employee'].create(employee_data)
                        for i in range(0,len(sheet.row_values(0,4)) ):
                            try:
                                day = float(sheet.row_values(0,4)[i])
                                tempDate = datetime(1900, 1, 1)
                                deltaDays = timedelta(days=int(day) - 2)
                                import_day = (tempDate + deltaDays).strftime("%Y-%d-%m")
                            except:
                                import_day = datetime.strptime(sheet.row_values(0,4)[i],'%d/%m/%Y').strftime('%Y-%m-%d')
                            # day = float(sheet.row_values(0,4)[i])
                            # tempDate = datetime(1900, 1, 1)
                            # deltaDays = timedelta(days=int(day) - 2)
                            # import_day = (tempDate + deltaDays).strftime("%Y-%d-%m")
                            if (float(row[i+4]) + 8) != 0:
                                import_data = {
                                    'date'          : import_day,
                                    'unit_amount'   : float(row[i+4]) + 8,
                                    'account_id'    : self.project_id.analytic_account_id.id,
                                    'project_id'    : self.project_id.id,
                                    'user_id'       : employee.user_id.id or False,
                                    'name'          : '/'
                                }
                                line_id = line.create(import_data)
                                count += 1
            line_create = count
            # self.error_log = al_error
            self.state = 'result'
            # self.line_update = line_update
            self.line_create = line_create
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'export.import.account.analytic.line',
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
            orders      = self._context.get('active_ids')
            header_name = ['ID#', 'Name','Email','Location']
            period      = datetime.strptime(self.date_to,DEFAULT_SERVER_DATE_FORMAT) - datetime.strptime(self.date_from,DEFAULT_SERVER_DATE_FORMAT)

            for i in range(0,period.days+1):
                day = (datetime.strptime(self.date_from,DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=i)).strftime('%A %d/%m/%Y')
                header_name.append(day)
            final_data.append(header_name)
            for employee in self.employee_ids:
                export_row = []
                export_row.append(employee.employee_id or '')
                export_row.append(employee.name or '')
                export_row.append(employee.work_email or '')
                export_row.append(employee.work_location or '')
                for j in range(0, period.days + 1):
                    day = (datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=j)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                    aal = line.search([('user_id','=',employee.user_id.id),('date','=',day),('project_id','=',self.project_id.id)])
                    if aal:
                        export_row.append(aal[0].unit_amount)
                    else:
                        export_row.append(0)
                final_data.append(export_row)

            for i, l in enumerate(final_data):
                for j, col in enumerate(l):
                    ws.write(i, j, col)
            book.save(output)
            self.export_data = base64.b64encode(output.getvalue())
            self.name = "%s%s" % ('timesheet', '.xls')
            self.state = 'get'
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'export.import.account.analytic.line',
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