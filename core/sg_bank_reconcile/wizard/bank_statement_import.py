# -*- coding: utf-8 -*-
from odoo import api, fields, models
import openpyxl
from tempfile import TemporaryFile
from odoo.exceptions import UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class bank_statement_import(models.TransientModel):
    _name = 'bank.statement.import'
    _description = 'Bank Statement Import'

    file = fields.Binary('File to import', attachment=True)

    @api.multi
    def action_bank_statement_import(self):
        ctx = self._context if self._context else {}
        if 'bank_statement_import_id' in ctx:
            bank_statement_obj = self.env['bank.acc.rec.statement'].browse(ctx['bank_statement_import_id'])
            try:
                excel_file = self.file.decode('base64')
                excel_fileobj = TemporaryFile('wb+')
                excel_fileobj.write(excel_file)
                excel_fileobj.seek(0)

                workbook = openpyxl.load_workbook(excel_fileobj, data_only=True)
                sheet = workbook[workbook.get_sheet_names()[0]]
                count = -1

            except Exception, e:
                _logger.exception("Kindly check the file. The file must be in Excel format(i.e. .XLS, .XLSX)")
                raise UserError(("Kindly check the file. The file must be in Excel format(i.e. .XLS, .XLSX)"))

            error = ''
            try:
                count = 0

                bank_statement_vals, bank_statement_line_vals = {}, {}
                for row in sheet.rows:
                    row0 = row[0].value
                    row1 = row[1].value
                    row2 = row[2].value
                    row3 = row[3].value
                    row4 = row[4].value
                    row5 = row[5].value
                    row6 = row[6].value
                    sheet_vals = {'values': [row0,row1,row2,row3,row4,row5,row6]}

                    count += 1

                    if count == 1:
                        bank_statement_line_vals['name'] = sheet_vals['values'][1]

                    if count == 2:
                        bank_statement_vals['starting_date'] = datetime.strptime(str(sheet_vals['values'][1]), '%d-%b-%Y').strftime('%Y-%m-%d')
                        bank_statement_vals['ending_date'] = datetime.strptime(str(sheet_vals['values'][3]), '%d-%b-%Y').strftime('%Y-%m-%d')

                    if count == 3:
                        if bank_statement_obj.starting_balance == 0.0:
                            bank_statement_vals['starting_balance'] = sheet_vals['values'][1]

                    if count == 4:
                        bank_statement_vals['ending_balance'] = bank_statement_obj.ending_balance - (-sheet_vals['values'][1])

                    if count >= 7:
                        bank_statement_line_vals['date'] = datetime.strptime(str(sheet_vals['values'][0]), '%d-%b-%Y').strftime('%Y-%m-%d')
                        bank_statement_line_vals['first_description'] = sheet_vals['values'][2]
                        bank_statement_line_vals['second_description'] = sheet_vals['values'][3]
                        bank_statement_line_vals['debit'] = sheet_vals['values'][4] if sheet_vals['values'][4] else 0.0
                        bank_statement_line_vals['credit'] = sheet_vals['values'][5] if sheet_vals['values'][5] else 0.0
                        bank_statement_line_vals['statement_id'] = bank_statement_obj.id
                        # bank_statement_line_vals['move_line_id'] = bank_statement_obj.id
                        bank_statement_line_vals['type'] = 'cr'

                        # Creating credit lines via import
                        self.env['bank.acc.rec.statement.line'].create(bank_statement_line_vals)
                        # Updating starting balance, start and end date
                        bank_statement_obj.write(bank_statement_vals)
                        # Updating journal items to cleared
                        for debit_line in bank_statement_obj.debit_move_line_ids:
                            debit_line.draft_assigned_to_statement = True
                            debit_line.write({'move_line_id': debit_line.move_line_id.id})
                            for credit_line in bank_statement_obj.credit_move_line_ids:
                                credit_line.draft_assigned_to_statement = True
                                credit_line.write({'move_line_id': debit_line.move_line_id.id})

            except Exception, e:
                raise UserError("Import Error!\nError occurred in row : %s\n\nError :\n%s" % (count, error or e))
        return True

bank_statement_import()