# -*- coding: utf-8 -*-
import base64
import datetime
import tempfile

from odoo import fields, models, api
from odoo import tools
from odoo.tools.translate import _


class e_tax_wiz(models.TransientModel):
    _inherit = "account.common.account.report"

    _name = 'e.tax.wiz'

    sold_accounts = {}

    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')
    account_report_id = fields.Many2one('account.financial.report', string='Account Reports', required=False,
                                        default=_get_account_report)

    def _compute_account_balance(self, accounts):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accoutns with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    @api.multi
    def _sum_debit_account(self, account):
        context = dict(self._context)
        obj_move = self.env['account.move.line']
        context.update({
            'date_from': context.get('datas').get('date_from'),
            'date_to': context.get('datas').get('date_to'),
        })
        domain = []
        if context.get('date_from', False):
            domain += [('date', '>=', context.get('date_from'))]
        if context.get('date_to', False):
            domain += [('date', '<=', context.get('date_to'))]
        move_state = ('draft', 'posted')
        if context.get('datas').get('target_move') == 'posted':
            move_state = ('posted', '')

        tables, where_clause, where_params = self.env['account.move.line'].with_context(context)._query_get(
            domain=domain)
        where_params = [account.id] + [tuple(move_state)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT  SUM(debit)
                      FROM account_move_line
                      JOIN account_move am ON (am.id = account_move_line.move_id) \
                      WHERE (account_move_line.account_id = %s) \
                      AND (am.state IN %s) \
                      """ + where_clause
                         , where_params)
        sum_debit = self._cr.fetchone()[0] or 0.0
        return sum_debit

    @api.multi
    def _sum_credit_account(self, account):
        context = dict(self._context)
        obj_move = self.env['account.move.line']
        context.update({
            'date_from': context.get('datas').get('date_from'),
            'date_to': context.get('datas').get('date_to'),
        })
        move_state = ('draft', 'posted')
        if context.get('datas').get('target_move') == 'posted':
            move_state = ('posted', '')

        tables, where_clause, where_params = self.env['account.move.line'].with_context(context)._query_get()
        where_params = [account.id] + [tuple(move_state)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT  SUM(credit)
                      FROM account_move_line
                      JOIN account_move am ON (am.id = account_move_line.move_id) \
                      WHERE (account_move_line.account_id = %s) \
                      AND (am.state IN %s) \
                      """ + where_clause
                         , where_params)
        sum_credit = self._cr.fetchone()[0] or 0.0
        return sum_credit

    @api.multi
    def _sum_balance_account(self, account):
        context = dict(self._context)
        obj_move = self.env['account.move.line']
        move_state = ('draft', 'posted')
        if context.get('datas').get('target_move') == 'posted':
            move_state = ('posted', '')
        tables, where_clause, where_params = self.env['account.move.line'].with_context(context)._query_get()
        where_params = [account.id] + [tuple(move_state)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT (sum(debit) - sum(credit)) as tot_balance \
                      FROM account_move_line
                      JOIN account_move am ON (am.id = account_move_line.move_id) \
                      WHERE (account_move_line.account_id = %s) \
                      AND (am.state IN %s) \
                      """ + where_clause
                         , where_params)
        sum_balance = self._cr.fetchone()[0] or 0.0
        return sum_balance

    ###    @api.multi
    ###    def get_children_accounts(self, account):
    ###        context = dict(self._context)
    ###        res = []
    ###        obj_move = self.env['account.move.line']
    ###        currency_obj = self.env['res.currency']
    ###        ids_acc = self.env['account.account']._get_children_and_consol(account.id)
    ###        currency = account.currency_id and account.currency_id or account.company_id.currency_id
    ###        query = obj_move.with_context(context)._query_get()
    ###        for child_account in self.env['account.account'].browse(ids_acc):
    ###            sql = """
    ###                SELECT count(id)
    ###                FROM account_move_line AS l
    ###                WHERE %s AND l.account_id = %%s
    ###            """ % (query)
    ###            self._cr.execute(sql, (child_account.id,))
    ###            num_entry = self._cr.fetchone()[0] or 0
    ###            sold_account = self._sum_balance_account(child_account)
    ###            self.sold_accounts[child_account.id] = sold_account
    ###            if context.get('datas').get('display_account') == 'movement':
    ###                if child_account.type != 'view' and num_entry <> 0:
    ###                    res.append(child_account)
    ###            elif context.get('datas').get('display_account') == 'not_zero':
    ###                if child_account.type != 'view' and num_entry <> 0:
    ###                    if not currency_obj.is_zero(cr, uid, currency, sold_account):
    ###                        res.append(child_account)
    ###            else:
    ###                res.append(child_account)
    ###        if not res:
    ###            return [account]
    ###        return res

    @api.multi
    def lines(self, accounts, init_balance, sortby, display_account):
        """
        :param:
                accounts: the recordset of accounts
                init_balance: boolean value of initial_balance
                sortby: sorting by date or partner and journal
                display_account: type of account(receivable, payable and both)

        Returns a dictionary of accounts with following key and value {
                'code': account code,
                'name': account name,
                'debit': sum of total debit amount,
                'credit': sum of total credit amount,
                'balance': total balance,
                'amount_currency': sum of amount_currency,
                'move_lines': list of move line
        }
        """
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = dict(map(lambda x: (x, []), accounts.ids))

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, NULL AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                NULL AS currency_id,\
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                '' AS partner_name\
                FROM account_move_line l\
                LEFT JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                WHERE l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
            m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
            FROM account_move_line l\
            JOIN account_move m ON (l.move_id=m.id)\
            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
            JOIN account_journal j ON (l.journal_id=j.id)\
            JOIN account_account acc ON (l.account_id = acc.id) \
            WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        return account_res

    def convert_two_decimal(self, number):
        return "{0:.2f}".format(number)

    @api.multi
    def check_report(self):
        cr, uid, context = self.env.args
        if context is None:
            context = {}
        context = dict(self._context)
        data = self.read([])[0]
        context.update({
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'datas': data
        })
        res_users_obj = self.env['res.users']
        period_id = []
        date_from = context.get('date_from', False)
        date_to = context.get('date_to', False)
        company_data = res_users_obj.browse(uid).company_id
        purchase_order_obj = self.env['purchase.order']
        acc_invoice_obj = self.env['account.invoice']
        tax_obj = self.env['account.tax']
        move_obj = self.env['account.move']
        journal_obj = self.env['account.journal']
        account_obj = self.env['account.account']
        cur_obj = self.env['res.currency']
        cust_arg = [('type', '=', 'out_invoice'), ('state', 'in', ['open', 'paid'])]
        supp_arg = [('type', '=', 'in_invoice'), ('state', 'in', ['open', 'paid'])]

        if date_from:
            cust_arg.append(('date_invoice', '>=', date_from))
            supp_arg.append(('date_invoice', '>=', date_from))

        if date_to:
            cust_arg.append(('date_invoice', '<=', date_to))
            supp_arg.append(('date_invoice', '<=', date_to))

        customer_invoice_ids = acc_invoice_obj.search(cust_arg)
        supplier_invoice_ids = acc_invoice_obj.search(supp_arg)
        tgz_tmp_filename = tempfile.mktemp('.' + "txt")
        tmp_file = False
        try:
            tmp_file = open(tgz_tmp_filename, "wr")
            company_record = tools.ustr('CompInfoStart|') + \
                             "\r\n" + \
                             tools.ustr(
                                 'CompanyName|CompanyUEN|GSTNo|PeriodStart|PeriodEnd|IAFCreationDate|ProductVersion|IAFVersion|') + \
                             "\r\n" + \
                             tools.ustr(company_data and company_data.name or '') + \
                             '|'.ljust(1) + \
                             tools.ustr(company_data and company_data.company_uen or '') + \
                             '|'.ljust(1) + \
                             tools.ustr(company_data and company_data.gst_no or '') + \
                             '|'.ljust(1) + \
                             tools.ustr(company_data and company_data.period_start or '') + \
                             '|'.ljust(1) + \
                             tools.ustr(company_data and company_data.period_end or '') + \
                             '|'.ljust(1) + \
                             tools.ustr(company_data and company_data.iaf_creation_date or '') + \
                             '|'.ljust(1) + \
                             tools.ustr(company_data and company_data.product_version or '') + \
                             '|'.ljust(1) + \
                             tools.ustr(company_data and company_data.iaf_version or '') + \
                             '|'.ljust(1) + \
                             "\r\n" + \
                             tools.ustr('CompInfoEnd|') + \
                             "\r\n" + \
                             "\r\n" + \
                             tools.ustr('PurcDataStart|') + \
                             "\r\n" + \
                             tools.ustr(
                                 'SupplierName|SupplierUEN|InvoiceDate|InvoiceNo|PermitNo|LineNo|ProductDescription|PurchaseValueSGD|GSTValueSGD|TaxCode|FCYCode|PurchaseFCY|GSTFCY|') + \
                             "\r\n"
            tmp_file.write(company_record)
            tot_line = 0
            tot_pur_sgd = tot_gst_sg = 0.0
            for supplier in supplier_invoice_ids:
                line_no = 1
                for line in supplier.invoice_line_ids:
                    SupplierName = supplier.partner_id.name or ''
                    SupplierUEN = supplier.partner_id.supplier_uen or ''
                    InvoiceDate = supplier and supplier.date_invoice or ''
                    #                    InvoiceNo = supplier.supplier_invoice_number or ''
                    InvoiceNo = supplier.number or supplier.supplier_invoice_number or ''
                    PermitNo = supplier.permit_no or ''
                    LineNo = line_no
                    ProductDescription = line.name or ''

                    if supplier.currency_id.id == supplier.company_id.currency_id.id:
                        PurchaseValueSGD = line.price_subtotal or 0.0
                        GSTValueSGD = 0.0
                        TaxCode = ''
                        FCYCode = 'XXX'
                        PurchaseFCY = 0.0
                        GSTFCY = 0.0
                    else:
                        PurchaseValueSGD = supplier.currency_id.with_context({'date': supplier.date_invoice}).compute(
                            line.price_subtotal, supplier.company_id.currency_id)
                        GSTValueSGD = 0.0
                        TaxCode = ''
                        FCYCode = supplier.currency_id.name or ''
                        PurchaseFCY = line.price_subtotal or 0.0
                        GSTFCY = 0.0
                    tot_pur_sgd += PurchaseValueSGD
                    for tax in line.invoice_line_tax_ids:
                        tax_amt = tax_amt_foreign = 0.0
                        tax_name = ''
                        tax_data = \
                        tax.compute_all((line.price_unit * (1 - (line.discount or 0.0) / 100.0)), supplier.currency_id,
                                        line.quantity, line.product_id, supplier.partner_id)['taxes']
                        if tax_data:
                            tax_amt = tax_data[0]['amount']
                            tax_rec = tax_obj.browse(tax_data[0].get('id'))
                            if tax_rec.tag_ids and tax_rec.tag_ids.ids:
                                tax_name = tax_rec and tax_rec.tag_ids[0].name
                        if supplier.currency_id.id == supplier.company_id.currency_id.id:
                            GSTValueSGD = tax_amt
                            TaxCode += tax_name
                            GSTFCY = 0.0
                        else:
                            GSTValueSGD = supplier.currency_id.with_context({'date': supplier.date_invoice}).compute(
                                tax_amt, supplier.company_id.currency_id)
                            TaxCode += tax_name
                            GSTFCY = tax_amt
                        tot_gst_sg += GSTValueSGD
                    supplier_record = tools.ustr(SupplierName) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(SupplierUEN) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(InvoiceDate) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(InvoiceNo) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(PermitNo) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(int(LineNo)) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(ProductDescription) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(PurchaseValueSGD)) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(GSTValueSGD)) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(TaxCode) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(FCYCode) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(PurchaseFCY)) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(GSTFCY)) + \
                                      '|'.ljust(1) + \
                                      "\r\n"
                    tmp_file.write(supplier_record)
                    line_no += 1
                    tot_line += 1
            customer_data = tools.ustr('PurcDataEnd|') + \
                            tools.ustr(self.convert_two_decimal(float(tot_pur_sgd)) or self.convert_two_decimal(0.00)) + \
                            '|'.ljust(1) + \
                            tools.ustr(self.convert_two_decimal(float(tot_gst_sg)) or self.convert_two_decimal(0.00)) + \
                            '|'.ljust(1) + \
                            tools.ustr(int(tot_line)) + \
                            '|'.ljust(1) + \
                            "\r\n" + \
                            "\r\n" + \
                            tools.ustr('SuppDataStart|') + \
                            "\r\n" + \
                            tools.ustr(
                                'CustomerName|CustomerUEN|InvoiceDate|InvoiceNo|LineNo|ProductDescription|SupplyValueSGD|GSTValueSGD|TaxCode|Country|FCYCode|SupplyFCY|GSTFCY|') + \
                            "\r\n"
            tmp_file.write(customer_data)

            tot_supp_line_no = 0
            tot_supp_sgd = tot_gst_sg = 0.00
            for customer in customer_invoice_ids:
                supp_line_no = 1
                for line in customer.invoice_line_ids:
                    CustomerName = customer.partner_id.name or ''
                    CustomerUEN = customer.partner_id.customer_uen or ''
                    InvoiceDate = customer and customer.date_invoice or ''
                    InvoiceNo = customer.number or ''
                    LineNo = supp_line_no
                    ProductDescription = line.name or ''
                    Country = customer.partner_id.country_id and customer.partner_id.country_id.name or ''
                    if customer.currency_id.id == customer.company_id.currency_id.id:
                        SupplyValueSGD = line.price_subtotal or 0.0
                        GSTValueSGD = 0.0
                        TaxCode = ''
                        FCYCode = 'XXX'
                        SupplyFCY = 0.0
                        GSTFCY = 0.0
                    else:
                        SupplyValueSGD = cur_obj.with_context({'date': customer.date_invoice}).compute(
                            line.price_subtotal, customer.company_id.currency_id)
                        GSTValueSGD = 0.0
                        TaxCode = ''
                        FCYCode = customer.currency_id.name or ''
                        SupplyFCY = line.price_subtotal or 0.0
                        GSTFCY = 0.0
                    tot_supp_sgd += SupplyValueSGD
                    for tax in line.invoice_line_tax_ids:
                        tax_amt = tax_amt_foreign = 0.0
                        tax_name = ''
                        tax_data = \
                        tax.compute_all((line.price_unit * (1 - (line.discount or 0.0) / 100.0)), customer.currency_id,
                                        line.quantity, line.product_id, customer.partner_id)['taxes']
                        if tax_data:
                            tax_amt = tax_data[0]['amount']
                            tax_rec = tax_obj.browse(tax_data[0].get('id'))
                            if tax_rec.tag_ids and tax_rec.tag_ids.ids:
                                tax_name = tax_rec and tax_rec.tag_ids[0].name

                        if customer.currency_id.id == customer.company_id.currency_id.id:
                            GSTValueSGD = tax_amt
                            TaxCode += tax_name
                            GSTFCY = 0.0
                        else:
                            GSTValueSGD = cur_obj.with_context({'date': customer.date_invoice}).compute(tax_amt,
                                                                                                        customer.currency_id)
                            TaxCode += tax_name
                            GSTFCY = tax_amt
                        tot_gst_sg += GSTValueSGD
                    supplier_record = tools.ustr(CustomerName) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(CustomerUEN) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(InvoiceDate) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(InvoiceNo) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(int(LineNo)) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(ProductDescription).encode('ascii', 'ignore').decode('ascii') + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(SupplyValueSGD)) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(GSTValueSGD)) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(TaxCode) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(Country) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(FCYCode) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(float(SupplyFCY))) + \
                                      '|'.ljust(1) + \
                                      tools.ustr(self.convert_two_decimal(GSTFCY)) + \
                                      '|'.ljust(1) + \
                                      "\r\n"
                    tmp_file.write(supplier_record)
                    supp_line_no += 1
                    tot_supp_line_no += 1
            account_data = tools.ustr('SuppDataEnd|') + \
                           tools.ustr(self.convert_two_decimal(float(tot_supp_sgd)) or self.convert_two_decimal(0.00)) + \
                           '|'.ljust(1) + \
                           tools.ustr(self.convert_two_decimal(float(tot_gst_sg)) or self.convert_two_decimal(0.00)) + \
                           '|'.ljust(1) + \
                           tools.ustr(int(tot_supp_line_no)) + \
                           '|'.ljust(1) + \
                           "\r\n" + \
                           "\r\n" + \
                           tools.ustr('GLDataStart|') + \
                           "\r\n" + \
                           tools.ustr(
                               'TransactionDate|AccountID|AccountName|TransactionDescription|Name|TransactionID|SourceDocumentID|SourceType|Debit|Credit|Balance|') + \
                           "\r\n"
            tmp_file.write(account_data)

            #            account = account_obj.browse(context.get('datas').get('chart_account_id')[0])
            #            child_data = self.get_children_accounts(account)
            accounts = self.env['account.account'].search([])
            tot_credit = tot_debit = 0.0
            tot_account_line = 0
            currency = self.env.user.company_id.currency_id.name
            AccountMoveLine = self.env['account.move.line']
            for account in accounts:
                # child_data = account._get_children_by_order()
                # results = self.with_context(context)._compute_report_balance(child_data)
                if len(AccountMoveLine.search([('account_id', '=', account.id)])) == 0:
                    continue
                ctx = {'date_from': context.get('datas').get('date_from'),
                       'date_to': context.get('datas').get('date_to'),
                       }
                ctx.update({'datas': context.get('datas'),
                            })
                debit_amt = self.with_context(ctx)._sum_debit_account(account)
                credit_amt = self.with_context(ctx)._sum_credit_account(account)
                balance_account = self.with_context(ctx)._sum_balance_account(account)
                opening_balance = tools.ustr(datetime.datetime.today().strftime("%Y-%m-01") or '') + \
                                  '|'.ljust(1) + \
                                  tools.ustr(account.code) + \
                                  '|'.ljust(1) + \
                                  tools.ustr(account.name) + \
                                  '|'.ljust(1) + \
                                  tools.ustr('OPENING BALANCE') + \
                                  '|||||'.ljust(1) + \
                                  tools.ustr(self.convert_two_decimal(0) or self.convert_two_decimal(0.00)) + \
                                  '|'.ljust(1) + \
                                  tools.ustr(self.convert_two_decimal(0) or self.convert_two_decimal(0.00)) + \
                                  '|'.ljust(1) + \
                                  tools.ustr(
                                      self.convert_two_decimal(0) or self.convert_two_decimal(0.00)) + \
                                  '|'.ljust(1) + \
                                  "\r\n"
                tmp_file.write(opening_balance)
                move_state = ('draft', 'posted')
                if context.get('datas').get('target_move') == 'posted':
                    move_state = ('posted', '')
                move_domain = [('account_id', '=', account.id), ('move_id.id', '>', 0),
                               ('move_id.state', 'in', move_state)]
                if date_from:
                    move_domain += [('date', '>=', date_from)]
                if date_to:
                    move_domain += [('date', '<=', date_to)]
                balance_section_amount = 0
                for move_line in AccountMoveLine.search(move_domain):
                    balance_section_amount += move_line.debit
                    balance_section_amount -= move_line.credit
                    line_balance = tools.ustr(move_line.date or '') + \
                                   '|'.ljust(1) + \
                                   tools.ustr(account.code) + \
                                   '|'.ljust(1) + \
                                   tools.ustr(account.name) + \
                                   '|'.ljust(1) + \
                                   tools.ustr(move_line.name or '') + \
                                   '|'.ljust(1) + \
                                   tools.ustr(move_line.partner_id.name or '') + \
                                   '|'.ljust(1) + \
                                   tools.ustr(move_line.id) + \
                                   '|'.ljust(1) + \
                                   tools.ustr(move_line.ref) + \
                                   '|'.ljust(1) + \
                                   tools.ustr(move_line.journal_id.code) + \
                                   '|'.ljust(1) + \
                                   tools.ustr(
                                       self.convert_two_decimal(move_line.debit) or self.convert_two_decimal(0.00)) + \
                                   '|'.ljust(1) + \
                                   tools.ustr(
                                       self.convert_two_decimal(move_line.credit) or self.convert_two_decimal(0.00)) + \
                                   '|'.ljust(1) + \
                                   tools.ustr(
                                       self.convert_two_decimal(
                                           balance_section_amount) or self.convert_two_decimal(0.00)) + \
                                   '|'.ljust(1) + \
                                   "\r\n"

                    tmp_file.write(line_balance)
                    tot_account_line += 1
                    tot_debit += move_line.debit
                    tot_credit += move_line.credit

                    #             for report in child_data:
                    #                 if results[report.id].get('account'):
                    #                     for acc,values in results[report.id]['account'].items():
                    #                         acc = self.env['account.account'].browse(acc)
                    #                         ctx = {'date_from':context.get('datas').get('date_from'),
                    #                                'date_to':context.get('datas').get('date_to'),
                    #                                }
                    #                         ctx.update({'datas': context.get('datas'),
                    #                                     })
                    #                         debit_amt = self.with_context(ctx)._sum_debit_account(acc)
                    #                         credit_amt = self.with_context(ctx)._sum_credit_account(acc)
                    #                         tot_debit += debit_amt
                    #                         tot_credit += credit_amt
                    #                         # currency = acc.currency_id.name or ''
                    #                         balance_account = self.with_context(ctx)._sum_balance_account(acc)
                    #                         if date_from:
                    #                             opening_balance = tools.ustr(date_from or '') + \
                    #                                               '|'.ljust(1) + \
                    #                                               tools.ustr(acc.code) + \
                    #                                               '|'.ljust(1) + \
                    #                                               tools.ustr(acc.name) + \
                    #                                               '|'.ljust(1) + \
                    #                                               tools.ustr('OPENING BALANCE') + \
                    #                                               '|||||'.ljust(1) + \
                    #                                               tools.ustr(self.convert_two_decimal(debit_amt) or self.convert_two_decimal(0.00)) + \
                    #                                               '|'.ljust(1) + \
                    #                                               tools.ustr(self.convert_two_decimal(credit_amt) or self.convert_two_decimal(0.00)) + \
                    #                                               '|'.ljust(1) + \
                    #                                               tools.ustr(self.convert_two_decimal(balance_account) or self.convert_two_decimal(0.00)) + \
                    #                                               '|||'.ljust(1) + \
                    #                                               "\r\n"
                    #                             tmp_file.write(opening_balance)
                    # #                        acc_data = self.with_context(ctx).lines(acc)
                    #                         sortby = 'sort_date'
                    #                         display_account ='movement'
                    #                         acc_data = self.with_context(ctx).lines(acc, False, sortby, display_account)
                    #                        # continue
                    # #                        acc_data = []
                    #                         tot_account_line += 1
                    #                         for ac in acc_data:
                    #                             tot_debit += ac.get('debit', 0.0)
                    #                             tot_credit += ac.get('credit', 0.0)
                    #                             # currency = ac.get('currency_id', '') or ''
                    #                             movedata_date = ''
                    #                             if 'move_lines' in ac:
                    #                                 for move in ac['move_lines']:
                    #                                     if move.get('ldate'):
                    #                                         move_data = tools.ustr(move.get('ldate') or '') + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(acc.code) + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(acc.name) + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(move.get('lname') or '') + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(move.get('partner_name') or '') + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(move.get('lid') or '') + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(move.get('lref') or '') + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(move.get('lcode') or '') + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(self.convert_two_decimal(float(move.get('debit'))) or self.convert_two_decimal(0.00)) + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(self.convert_two_decimal(float(move.get('credit'))) or self.convert_two_decimal(0.00)) + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     tools.ustr(self.convert_two_decimal(move.get('progress')) or self.convert_two_decimal(0.00)) + \
                    #                                                     '|'.ljust(1) + \
                    #                                                     '\r\n'
                    #                                         tmp_file.write(move_data)
                tot_account_line += 1
            account_glend_data = tools.ustr('GLDataEnd|') + \
                                 tools.ustr(
                                     self.convert_two_decimal(float(tot_debit)) or self.convert_two_decimal(0.00)) + \
                                 '|'.ljust(1) + \
                                 tools.ustr(
                                     self.convert_two_decimal(float(tot_credit)) or self.convert_two_decimal(0.00)) + \
                                 '|'.ljust(1) + \
                                 tools.ustr(int(tot_account_line)) + \
                                 '|'.ljust(1) + \
                                 tools.ustr(currency) + \
                                 '|'.ljust(1)
            tmp_file.write(account_glend_data)
        finally:
            if tmp_file:
                tmp_file.close()
        file = open(tgz_tmp_filename, "rb")
        out = file.read()
        file.close()
        res = base64.b64encode(out)
        module_rec = self.env['binary.e.tax.text.file.wizard'].create({'name': 'ETAX.txt', 'etax_txt_file': res})
        return {
            'name': _('Binary'),
            'res_id': module_rec.id,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'binary.e.tax.text.file.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }


class binary_e_tax_text_file_wizard(models.TransientModel):
    _name = 'binary.e.tax.text.file.wizard'

    name = fields.Char('Name', default='ETAX.txt')
    etax_txt_file = fields.Binary('Click On Save As Button To Download File', readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
