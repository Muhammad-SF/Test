# -*- coding: utf-8 -*-
from dateutil import tz
import pytz
import requests
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import functools
import hashlib
import logging
import os
from ast import literal_eval
import base64
try:
    import simplejson as json
except ImportError:
    import json

import werkzeug.wrappers

import time
import odoo
from odoo import http, SUPERUSER_ID, api, _
from odoo.http import *
from odoo import http, _, fields
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)

# from main import *


def error_response(status, error, error_descrip):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers = None,
        response=json.dumps({
            'error': error,
            'error_descrip': error_descrip,
        }),
    )


class ApiRequest(WebRequest):
    _request_type = "json"

    def __init__(self, *args):
        super(ApiRequest, self).__init__(*args)
        params = collections.OrderedDict(self.httprequest.args)
        params.update(self.httprequest.form)
        params.update(self.httprequest.files)
        params.pop('session_id', None)
        self.params = params

    def _response(self, result=None, error=None):
        if error is not None:
            return error

        elif result is not None:
            return result

    def dispatch(self):
        try:
            result = self._call_function()
            return self._response(result=result)
        except Exception as exception:
            # Rollback
            if self._cr:
                self._cr.rollback()
            # End Rollback
            error = {
                'code': 500,
                'message': "Odoo Server Error",
                'data': False
            }
            if not isinstance(exception, (odoo.exceptions.Warning, SessionExpiredException, odoo.exceptions.except_orm)):
                _logger.exception("Exception during JSON request handling.")
            error = {
                'code': 500,
                'message': "Odoo Server Error",
                'data': serialize_exception(exception)
            }
            if isinstance(exception, AuthenticationError):
                error['code'] = 400
                error['message'] = "Odoo Session Invalid"
            if isinstance(exception, LoginError):
                error['code'] = 403
                error['message'] = "Login or Password Incorrect"
            if isinstance(exception, SessionExpiredException):
                error['code'] = 400
                error['message'] = "Odoo Session Expired"
            return error_response(error['code'], error['message'], error['data'] or error['message'])


def api_get_request(self, httprequest):
    # deduce type of request
    if ('/api' in httprequest.path) and (httprequest.mimetype == "application/json"):
        return ApiRequest(httprequest)
    if httprequest.args.get('jsonp'):
        return JsonRequest(httprequest)
    if httprequest.mimetype in ("application/json", "application/json-rpc"):
        return JsonRequest(httprequest)
    else:
        return HttpRequest(httprequest)


Root.get_request = api_get_request


class LoginError(Exception):
    pass


class ControllerREST(http.Controller):

    def set_tz(self, date_string, tz_from, tz_to):
        res = date_string
        if date_string:
            res = fields.Datetime.from_string(
                date_string).replace(tzinfo=tz.gettz(tz_from))
            res = res.astimezone(tz.gettz(tz_to))
            res = res.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return res

    def prepare_fields_GET(self, model_name, res, list_deleted_key=[]):
        Model = request.env[model_name].sudo()
        for key in res:
            if isinstance(Model._fields[key], fields.Many2one):
                if isinstance(res[key], tuple):
                    res[key] = {
                        "id": res[key][0],
                        "name": res[key][1],
                    }
                if not res[key]:
                    res[key] = {
                        "id": 0,
                        "name": '',
                    }

            if isinstance(Model._fields[key], fields.Datetime):
                if res[key]:
                    res[key] = self.set_tz(res[key], 'Asia/Jakarta', 'UTC')
            if isinstance(Model._fields[key], fields.Char) or isinstance(Model._fields[key], fields.Text) or isinstance(Model._fields[key], fields.Date):
                if not res[key]:
                    res[key] = ""
            if isinstance(Model._fields[key], fields.Binary):
                if 'image' in key:
                    res[key] = request.env['ir.config_parameter'].sudo().get_param(
                        'web.base.url') + '/web/image?model=' + model_name + '&id=' + str(res['id']) + '&field=' + key
                else:
                    list_deleted_key.append(key)
            if isinstance(Model._fields[key], fields.Selection):
                if res[key] and Model._fields[key].selection:
                    try:
                        selection_dict = dict(Model._fields[key].selection)
                        res[key] = {
                            "value": res[key],
                            "name": selection_dict.get(res[key]),
                        }
                    except:
                        res[key] = {"value": "", "name": ""}
                else:
                    res[key] = {"value": "", "name": ""}

        for key in list_deleted_key:
            del res[key]
        return res

    def prepare_fields_POST(self, model_name, res):
        Model = request.env[model_name]
        list_deleted_key = []
        for key in res:
            if isinstance(Model._fields[key], fields.Binary):
                list_deleted_key.append(key)
            if isinstance(Model._fields[key], fields.Many2one):
                if isinstance(res[key], dict) and "id" in res[key]:
                    res[key] = res[key]["id"]
            if isinstance(Model._fields[key], fields.Selection):
                if isinstance(res[key], dict) and "value" in res[key]:
                    res[key] = res[key]["value"]
            if isinstance(Model._fields[key], fields.Datetime):
                if res[key]:
                    res[key] = self.set_tz(res[key], 'UTC', 'Asia/Jakarta')

        for key in list_deleted_key:
            del res[key]

        return res

    def filter_same_fields(self, model_name, model_id, update_values):
        Model = request.env[model_name].sudo()
        db_values = Model.browse(model_id).read([])
        list_deleted_key = []
        if db_values:
            db_values = db_values[0]
        for key in update_values:
            if (key in db_values and update_values[key] == db_values[key]):
                list_deleted_key.append(key)
        for key in list_deleted_key:
            del update_values[key]
        return update_values

    def error_response(self, status, error, error_descrip):
        return werkzeug.wrappers.Response(
            status=status,
            content_type='application/json; charset=utf-8',
            # headers = None,
            response=json.dumps({
                'error': error,
                'error_descrip': error_descrip,
            }),
        )

    def success_response(self, res):
        mime = 'application/json'
        body = json.dumps(res)
        return Response(body, headers=[('Content-Type', mime),
                                       ('Content-Length', len(body))])

    def check_session_id(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):

            if not request.session.uid:
                return self.error_response(401, 'Unauthorized', 'Unauthorized')
            else:
                request.uid = request.session.uid

            # The code, following the decorator
            return func(self, *args, **kwargs)
        return wrapper

    @http.route('/api/selections/<model>/<field>', methods=['GET'], type="http", auth="none", csrf=False, cors='*')
    def get_selections(self, model, field, **kw):
        Model = http.request.env[model].sudo()
        if isinstance(Model._fields[field], fields.Selection):
            res = []
            try:
                selection_dict = dict(Model._fields[field].selection)
                for key in selection_dict:
                    res.append({
                        'name': selection_dict.get(key),
                        'value': key,
                        'subtitle': "",
                    })
            except:
                res = []
        else:
            res = []
        return http.request.make_response(json.dumps(res), headers=[
            ('Content-Type', 'application/json'),
        ])

    @http.route(['/api/list/<model>'], methods=['GET'], type="http", auth="none", csrf=False, cors='*')
    def get_list(self, model, **kw):
        offset = int(kw.get('offset', 0))
        limit = int(kw.get('limit', 0))
        fields = kw.get('fields', '["id", "name"]')
        domains = kw.get('domains', '[]')
        order = kw.get('order', 'id asc')
        res = http.request.env[model].sudo().search_read(
            literal_eval(domains), literal_eval(fields), offset=offset, limit=limit, order=order)
        for r in res:
            r = self.prepare_fields_GET(model, r)
        return http.request.make_response(json.dumps(res), headers=[
            ('Content-Type', 'application/json'),
        ])

    @http.route(['/api/values'], methods=['GET'], type="http", auth="none", csrf=False, cors='*')
    def get_distinct_values(self, **kw):
        model_id = kw.get('model_id', False)
        field_id = kw.get('field_id', False)
        params = kw.get('params', '')
        if not model_id or not field_id:
            return self.error_response(500, 'Error', 'Cannot find model and field.')
        model_name = request.env['ir.model'].sudo().browse(int(model_id)).model
        field = request.env['ir.model.fields'].sudo().browse(int(field_id))
        field_name = field.name
        table_name = model_name.replace('.', '_')
        query_search = ''
        if params:
            if field.ttype == 'char':
                params = '%' + params + '%'
                query_search = """ WHERE %s ilike '%s' """ % (field_name, params)
            elif field.ttype == 'integer':
                query_search = """ WHERE %s = %s """ % (field_name, params)
            
        query = """
            SELECT DISTINCT (%(field_name)s)
            FROM
                %(table_name)s
            %(query_search)s
            ORDER BY %(field_name)s
            """ % {
                'field_name': field_name,
                'table_name': table_name,
                'query_search': query_search
            }

        request._cr.execute(query)
        query_result = request._cr.fetchall()
        res = []
        ids = []
        for qr in query_result:
            if qr and len(qr):
                ids.append(qr[0])
                if field.ttype == 'char':
                    res.append({
                        'name': str(qr[0]),
                        'value': "'" + str(qr[0]) + "'"
                    })
                else:
                    res.append({
                        'name': str(qr[0]),
                        'value': qr[0]
                    })
        # For Many2One
        if field.ttype == 'many2one':
            records = request.env[field.relation].sudo().search_read([('id', 'in', ids), ('name', 'ilike', params)], ['id', 'name'])
            res = []
            for r in records:
                res.append({
                    'name': r['name'],
                    'value': r['id']
                })
        return http.request.make_response(json.dumps(res), headers=[
            ('Content-Type', 'application/json'),
        ])

    @http.route('/api/resetpassword', methods=['POST'], type="json", auth="none", csrf=False, cors='*')
    def reset_password(self, **kw):
        try:
            jdata = json.loads(kw.get('request_body').decode('utf-8'))
        except:
            jdata = {}

        User = request.env['res.users'].sudo()
        email = jdata['email']

        res = {}
        try:
            User.reset_password(email)

        except:
            return self.error_response(500, 'Error', 'Cannot send reset email.')
        return self.success_response(res)

    @http.route('/api/login', type="json", auth="none", methods=['POST'], csrf=False, cors='*')
    def login(self, **kw):
        jdata = json.loads(kw.get('request_body').decode('utf-8'))
        res = {}
        User = request.env['res.users'].sudo()
        Partner = request.env['res.partner'].sudo()
        Employee = request.env['hr.employee'].sudo()

        if jdata:
            login = jdata.get('login', False)
            password = jdata.get('password', False)
            db = request.db
            uid = request.session.authenticate(db, login, password)

            if uid:
                request.uid = uid

                user = User.search([('id', '=', uid)])
                partner = user.partner_id

                user_id = request.uid

                res = {}
                # Check if manager
                if user.has_group('hr_inj.group_hr_overtime_approval') and user.get_overtime_approval():
                    res.update({
                        'role': 'manager',
                        'id': uid,
                        'name': user.name,
                        'username': user.login,
                        'session_id': request.env['ir.http'].session_info()['session_id'],
                        'employee_id': user.id
                    })
                # Else then user
                else:
                    if user_id:
                        employee = Employee.search(
                            [('user_id', '=', user_id)], limit=1)
                    else:
                        return self.error_response(500, 'User not found', 'User not found')
                    if not employee:
                        return self.error_response(500, 'Employee not found', 'Employee not found')
                    if not user.has_group('hr_inj.group_hr_employee'):
                        return self.error_response(403, "You cannot login as employee because insufficient role. Ask your Administrator",
                                                   "You cannot login as employee because insufficient role. Ask your Administrator")
                    res.update({
                        'role': 'employee',
                        'id': uid,
                        'name': employee.name,
                        'username': employee.code,
                        'session_id': request.env['ir.http'].session_info()['session_id'],
                        'employee_id': employee.id
                    })
            else:
                return self.error_response(403, "Login or Password Incorrect", "Login or Password Incorrect")

        return self.success_response(res)

    def simplify_amount_id(self, amount):
        ret = str(amount)
        if amount >= (1000 * 1000 * 1000):
            ret = "{:.1f}".format(amount / (1000 * 1000 * 1000)) + ' bil'
        elif amount >= (1000 * 1000):
            ret = "{:.1f}".format(amount / (1000 * 1000)) + ' mil'
        elif amount >= (10000):
            ret = "{:.1f}".format(amount / (1000)) + ' k'
        elif amount <= -(1000 * 1000 * 1000):
            ret = "{:.1f}".format(amount / (1000 * 1000 * 1000)) + ' bil'
        elif amount <= -(1000 * 1000):
            ret = "{:.1f}".format(amount / (1000 * 1000)) + ' mil'
        elif amount <= -(10000):
            ret = "{:.1f}".format(amount / (1000)) + ' k'
        return ret

    def simplify_amount_value(self, query_result):
        if not query_result:
            return query_result
        total_value = 0
        for val_dict in query_result:
            total_value += val_dict['Value']
        avg_value = total_value / len(query_result)
        
        divider = 1
        if avg_value >= (1000 * 1000 * 1000):
            divider = (1000 * 1000 * 1000)
        elif avg_value >= (1000 * 1000):
            divider = (1000 * 1000)
        elif avg_value >= (10000):
            divider = (1000)

        for index, val_dict in enumerate(query_result):
            query_result[index]['Value'] = query_result[index]['Value'] / divider
        return query_result

    @http.route('/api/dashboard-name/<int:dashboard_id>', type="http", auth="none", methods=['GET'], csrf=False, cors='*')
    @check_session_id
    def get_dashboard_name(self, dashboard_id, **kw):
        try:
            User = request.env['res.users']
            Dashboard = request.env['web.dashboard']
            user_id = request.session.uid
            user = User.browse(user_id)
            is_manager = False
            if (user.has_group('web_dynamic_dashboard.group_ddashboard_manager')):
                is_manager = True
            res = {
                'is_manager': is_manager,
                'dashboards': []
            }
            if dashboard_id == 0:
                dashboards = Dashboard.search([])
                res['dashboards'].append({
                    'id': 0,
                    'name': 'All'
                })
            else:
                dashboards = Dashboard.search([('id', '=', dashboard_id)])
            for db in dashboards:
                res['dashboards'].append({
                    'id': db.id,
                    'name': db.name,
                    'dashboard_source': db.dashboard_source,
                    'tableau_url': db.tableau_url
                })
            return self.success_response(res)
        except Exception as exception:
            error = {
                'code': 500,
                'message': "Odoo Server Error",
                'data': serialize_exception(exception)
            }
            return error_response(error['code'], error['message'], error['data'] or error['message'])

    def get_data_block(self, block):
        User = request.env['res.users']
        company = False
        if request.session.uid:
            user = User.browse(request.session.uid)
            company = user.company_id
        data_block = {}
        if block.data_source == 'function':
            query_result, label_field, legend_field, label_ttype, legend_ttype = block.get_data_function()
        else:
            if not block.model_id or not block.field_id:
                return self.empty_block_data(block)
            # NOTE: data_source == 'config' or other values
            # ===============================================================================
            # Old Method : Using Manual Query. Faster. But Cant Handle Some Inheritance Issue
            # ===============================================================================
            model_name = block.model_id.model
            table_name = model_name.replace('.', '_')
            field_name = block.field_id.name
            label_field = False
            legend_field = False
            label_ttype = False
            legend_ttype = False
            query_operation_field = field_name
            if block.operation == 'count':
                query_operation_field = 'COUNT(COALESCE(%s.%s, 0 )) as "Value"' % (table_name, field_name)
            if block.operation == 'sum':
                query_operation_field = 'SUM(COALESCE(%s.%s, 0 )) as "Value"' % (table_name, field_name)
            if block.operation == 'average':
                query_operation_field = 'AVG(COALESCE(%s.%s, 0 )) as "Value"' % (table_name, field_name)

            query_table_join = table_name
            query_group = ''
            query_sort = """ORDER BY "Value" DESC"""  # Default sort by value, except group by date/time see below.
            if block.sort:
                query_sort = """ORDER BY "Value" %s""" % block.sort
            query_operation_field_before = query_operation_field
            query_group_before = ''
            query_sort_before = query_sort

            # Check if Time Comparation
            time_comparation = False
            if (block.group_field_id.ttype == 'datetime' or block.group_field_id.ttype == 'date')\
                and (block.subgroup_field_id.ttype == 'datetime' or block.subgroup_field_id.ttype == 'date'):
                time_comparation = True

            if block.group_field_id:
                group_field_name = block.group_field_id.name
                label_field = block.group_field_id.field_description
                label_ttype = block.group_field_id.ttype
                if block.group_field_id.ttype == 'many2one':
                    relation_group_model_name = block.group_field_id.relation
                    relation_group_table_name = relation_group_model_name.replace(
                        '.', '_')
                    query_on = """ (%s.%s = %s.id) """ % (
                        table_name, group_field_name, relation_group_table_name)
                    query_table_join = query_table_join + """ 
                        LEFT JOIN %(relation_group_table_name)s
                        ON %(query_on)s
                        """ % {
                        'relation_group_table_name': relation_group_table_name,
                        'query_on': query_on
                    }
                    query_operation_field = query_operation_field + \
                        """ , %s.id as "%s" """ % (
                            relation_group_table_name, label_field)
                    query_group = """GROUP BY "%s" """ % label_field
                    query_sort = query_sort + """ ,  "%s" """ % label_field
                    # For Before Query
                    query_operation_field_before = query_operation_field
                    query_group_before = """GROUP BY "%s" """ % label_field
                    query_sort_before = query_sort
                elif block.group_field_id.ttype == 'datetime' or block.group_field_id.ttype == 'date':
                    if not block.group_date_format:
                        block.group_date_format = 'day'
                    # day, week, month, year. DD YY/MM
                    date_format = 'YYYY/MM' if not time_comparation else 'MM'
                    if block.group_date_format in ('day', 'week'):
                        date_format = 'YYYY/MM/DD' if not time_comparation else 'DD'
                    elif block.group_date_format in ('year',):
                        date_format = 'YYYY'
                    if time_comparation:
                        label_field = 'Group' + label_field
                    query_operation_field = query_operation_field + """ , to_char(date_trunc('%s', %s.%s),'%s') as "%s" """ % (
                        block.group_date_format, table_name, group_field_name, date_format, label_field)
                    query_group = """GROUP BY "%s" """ % label_field
                    query_sort = """ORDER BY "%s" """ % label_field  # If group by date/time, then sort by time not value
                else:
                    query_operation_field = query_operation_field + \
                        """ , %s.%s as "%s" """ % (
                            table_name, group_field_name, label_field)
                    query_group = """GROUP BY "%s" """ % label_field
                    query_sort = query_sort + """ ,  "%s" """ % label_field
                    # For Before Query
                    query_operation_field_before = query_operation_field
                    query_group_before = """GROUP BY "%s" """ % label_field
                    query_sort_before = query_sort

            if block.subgroup_field_id:
                subgroup_field_name = block.subgroup_field_id.name
                legend_field = block.subgroup_field_id.field_description
                legend_ttype = block.subgroup_field_id.ttype
                if block.subgroup_field_id.ttype == 'many2one':
                    relation_group_model_name = block.subgroup_field_id.relation
                    relation_group_table_name = relation_group_model_name.replace(
                        '.', '_')
                    query_on = """ (%s.%s = %s.id) """ % (
                        table_name, subgroup_field_name, relation_group_table_name)
                    query_table_join = query_table_join + """ 
                        LEFT JOIN %(relation_group_table_name)s
                        ON %(query_on)s
                        """ % {
                        'relation_group_table_name': relation_group_table_name,
                        'query_on': query_on
                    }
                    query_operation_field = query_operation_field + \
                        """ , %s.id as "%s" """ % (
                            relation_group_table_name, legend_field)
                    query_group = query_group + """ , "%s" """ % legend_field
                    query_sort = query_sort + """ , "%s" """ % legend_field
                    # For Before Query
                    query_operation_field_before = query_operation_field_before + \
                        """ , %s.id as "%s" """ % (
                            relation_group_table_name, legend_field)
                    if query_group_before:
                        query_group_before = query_group_before + """ , "%s" """ % legend_field
                    else:
                        query_group_before = """GROUP BY "%s" """ % legend_field
                    query_sort_before = query_sort_before + """ , "%s" """ % legend_field
                elif block.subgroup_field_id.ttype == 'datetime' or block.subgroup_field_id.ttype == 'date':
                    if not block.subgroup_date_format:
                        block.subgroup_date_format = 'day'
                    # day, week, month, year. DD YY/MM
                    date_format = 'YYYY/MM' if not time_comparation else 'MM'
                    if block.subgroup_date_format in ('day', 'week'):
                        date_format = 'YYYY/MM/DD' if not time_comparation else 'DD'
                    elif block.subgroup_date_format in ('year',):
                        date_format = 'YYYY'
                    if time_comparation:
                        legend_field = 'SubGroup' + legend_field
                    query_operation_field = query_operation_field + """ , to_char(date_trunc('%s', %s.%s),'%s') as "%s" """ % (
                        block.subgroup_date_format, table_name, subgroup_field_name, date_format, legend_field)
                    query_group = query_group + """ ,  "%s" """ % legend_field
                    query_sort = query_sort + """ ,  "%s" """ % legend_field
                else:
                    query_operation_field = query_operation_field + \
                        """ , %s.%s as "%s" """ % (
                            table_name, subgroup_field_name, legend_field)
                    query_group = query_group + """ , "%s" """ % legend_field
                    query_sort = query_sort + """ , "%s" """ % legend_field
                    # For Before Query
                    query_operation_field_before = query_operation_field_before + \
                        """ , %s.%s as "%s" """ % (
                            table_name, subgroup_field_name, legend_field)
                    if query_group_before:
                        query_group_before = query_group_before + """ , "%s" """ % legend_field
                    else:
                        query_group_before = """GROUP BY "%s" """ % legend_field
                    query_sort_before = query_sort_before + """ , "%s" """ % legend_field

            # SORT
            # If block type = line, sort by dimension, not value. Because line is commonly used for trends, dates
            if block.block_type in ('line', 'area', 'line-treshold'):
                if label_field:
                    query_sort = """ORDER BY "%s" """ % label_field
                if legend_field:
                    query_sort = query_sort + """ ,  "%s" """ % legend_field

            query_domain = ''
            # Domain ORM
            if block.domain:
                query_domain = request.env[block.model_id.model].sudo(
                )._where_calc(literal_eval(block.domain))
                tables, where_clause, where_clause_params = query_domain.get_sql()
                for index, val in enumerate(where_clause_params):
                    word = where_clause_params[index]
                    if type(word) is str and not word.replace('.', '', 1).isdigit():
                        where_clause_params[index] = " '" + where_clause_params[index] + "' "
                query_domain = 'WHERE ' + \
                    where_clause % tuple(where_clause_params)
            
            # Domain Values
            if block.domain_values_field_id and block.domain_values_string:
                if query_domain:
                    query_domain += """ AND %s.%s in (%s) """ % (table_name, block.domain_values_field_id.name, block.domain_values_string)
                else:
                    query_domain = """ WHERE %s.%s in (%s) """ % (table_name, block.domain_values_field_id.name, block.domain_values_string)
            if block.subdomain_values_field_id and block.subdomain_values_string:
                if query_domain:
                    query_domain += """ AND %s.%s in (%s) """ % (table_name, block.subdomain_values_field_id.name, block.subdomain_values_string)
                else:
                    query_domain = """ WHERE %s.%s in (%s) """ % (table_name, block.subdomain_values_field_id.name, block.subdomain_values_string)
            
            # Domain Date
            query_domain_before = query_domain
            if block.domain_date_field_id and block.domain_date:
                # Today
                start_date = datetime.today()
                end_date = datetime.today()
                if block.domain_date == 'this_week':
                    start_date = start_date - timedelta(days=start_date.weekday())
                    end_date = start_date + timedelta(days=6)
                elif block.domain_date == 'last_10':
                    start_date = start_date - timedelta(days=10)
                elif block.domain_date == 'last_30':
                    start_date = start_date - timedelta(days=30)
                elif block.domain_date == 'last_60':
                    start_date = start_date - timedelta(days=60)
                elif block.domain_date == 'before_today':
                    start_date = start_date.replace(year=start_date.year - 50)
                    end_date = end_date - timedelta(days=1)
                elif block.domain_date == 'after_today':
                    start_date = start_date + timedelta(days=1)
                    end_date = end_date.replace(year=end_date.year + 50)
                elif block.domain_date == 'before_and_today':
                    start_date = start_date.replace(year=start_date.year - 50)
                elif block.domain_date == 'today_and_after':
                    end_date = end_date.replace(year=end_date.year + 50)
                elif block.domain_date == 'this_month':
                    start_date = start_date.replace(day=1)
                    next_month = start_date.replace(day=28) + timedelta(days=4)
                    end_date = next_month - timedelta(days=next_month.day)
                elif block.domain_date == 'last_month':
                    start_date = start_date.replace(day=1) - timedelta(days=1)
                    start_date = start_date.replace(day=1)
                    next_month = start_date.replace(day=28) + timedelta(days=4)
                    end_date = next_month - timedelta(days=next_month.day)
                elif block.domain_date == 'last_two_months':
                    next_month = start_date.replace(day=28) + timedelta(days=4)
                    start_date = start_date.replace(day=1) - timedelta(days=1)
                    start_date = start_date.replace(day=1)
                    end_date = next_month - timedelta(days=next_month.day)
                elif block.domain_date == 'last_three_months':
                    next_month = start_date.replace(day=28) + timedelta(days=4)
                    start_date = start_date.replace(day=1) - timedelta(days=1)
                    start_date = start_date.replace(day=1) - timedelta(days=1)
                    start_date = start_date.replace(day=1)
                    end_date = next_month - timedelta(days=next_month.day)
                elif block.domain_date == 'this_year':
                    start_date = start_date.replace(day=1, month=1)
                    end_date = end_date.replace(day=31, month=12)
                
                start_date = start_date.strftime("%Y-%m-%d")
                end_date = end_date.strftime("%Y-%m-%d")
                if block.domain_date_field_id.ttype == 'datetime':
                    start_date = start_date + " 00:00:00"
                    end_date = end_date + " 23:59:59"

                if query_domain:
                    query_domain += """ AND %s.%s >= '%s' AND %s.%s <= '%s' """ % (table_name, block.domain_date_field_id.name, start_date, table_name, block.domain_date_field_id.name, end_date)
                else:
                    query_domain += """ WHERE %s.%s >= '%s' AND %s.%s <= '%s' """ % (table_name, block.domain_date_field_id.name, start_date, table_name, block.domain_date_field_id.name, end_date)
                
                # Cumulative
                if query_domain_before:
                    query_domain_before += """ AND %s.%s < '%s' """ % (table_name, block.domain_date_field_id.name, start_date)
                else:
                    query_domain_before += """ WHERE %s.%s < '%s' """ % (table_name, block.domain_date_field_id.name, start_date)

            # Domain Company
            Model = request.env[model_name]
            if block.domain_values_field_id.name != 'company_id' and \
                block.subdomain_values_field_id.name != 'company_id' and \
                company and 'company_id' in Model._fields and \
                isinstance(Model._fields['company_id'], fields.Many2one) and \
                Model._fields['company_id'].comodel_name == 'res.company':
                if query_domain:
                    query_domain += """ AND %s.company_id = %s """ % (table_name, str(company.id))
                else:
                    query_domain += """ WHERE %s.company_id = %s """ % (table_name, str(company.id))

            query_limit = ''
            if block.limit:
                query_limit = """LIMIT """ + block.limit

            query = """
                SELECT
                    %(query_operation_field)s
                FROM
                    %(query_table_join)s
                %(query_domain)s
                %(query_group)s
                %(query_sort)s
                %(query_limit)s
                """ % {
                    'query_operation_field': query_operation_field,
                    'query_table_join': query_table_join,
                    'query_domain': query_domain,
                    'query_group': query_group,
                    'query_sort': query_sort,
                    'query_limit': query_limit
            }

            request._cr.execute(query)
            query_result = request._cr.dictfetchall()

            if block.time_calculation_method == 'before':
                query_before = """
                    SELECT
                        %(query_operation_field_before)s
                    FROM
                        %(query_table_join)s
                    %(query_domain_before)s
                    %(query_group_before)s
                    %(query_sort_before)s
                    %(query_limit)s
                    """ % {
                        'query_operation_field_before': query_operation_field_before,
                        'query_table_join': query_table_join,
                        'query_domain_before': query_domain_before,
                        'query_group_before': query_group_before,
                        'query_sort_before': query_sort_before,
                        'query_limit': query_limit
                }

                request._cr.execute(query_before)
                query_result_before = request._cr.dictfetchall()

        # Write to DataBlockFormat
        if block.block_type == 'tile':
            value = query_result[0]["Value"]
            data_block = {
                'id': block.id,
                'block_type': block.block_type,
                'block_size': block.block_size,
                'menu_id': block.menu_id.id if block.menu_id else '',
                'link': block.link or '',
                'background': '',
                'icon': block.tile_icon,
                'value': self.simplify_amount_id(value) if value else '0',
                'uom': '',
                'desc': block.name,
                'title': block.name,
                'model_id': block.model_id.id,
                'model_name': block.model_id.name,
                'field_id': block.field_id.id,
                'field_name': block.field_id.field_description,
                'operation': block.operation,
                'sort': block.sort,
                'group_field_id': block.group_field_id.id,
                'group_field_ttype': block.group_field_id.ttype,
                'group_field_name': block.group_field_id.field_description,
                'group_date_format': block.group_date_format,
                'group_limit': block.group_limit,
                'show_group_others': block.show_group_others,
                'subgroup_field_id': block.subgroup_field_id.id,
                'subgroup_field_ttype': block.subgroup_field_id.ttype,
                'subgroup_field_name': block.subgroup_field_id.field_description,
                'subgroup_date_format': block.subgroup_date_format,
                'subgroup_limit': block.subgroup_limit,
                'show_subgroup_others': block.show_subgroup_others,
                'domain_date_field_id': block.domain_date_field_id.id,
                'domain_date_field_name': block.domain_date_field_id.field_description,
                'domain_date': block.domain_date,
                'domain_values_field_id': block.domain_values_field_id.id,
                'domain_values_field_name': block.domain_values_field_id.field_description,
                'domain_values_string': block.domain_values_string,
                'subdomain_values_field_id': block.subdomain_values_field_id.id,
                'subdomain_values_field_name': block.subdomain_values_field_id.field_description,
                'subdomain_values_string': block.subdomain_values_string,
                'time_calculation_method': block.time_calculation_method,
                'domain': block.domain
            }
        else:
            # query_result = self.simplify_amount_value(query_result)
            series_by_label_legend = {}
            labels = []
            legends = []
            for row in query_result:
                if label_field and label_field in row:
                    if row[label_field] not in labels:
                        labels.append(row[label_field])
                        series_by_label_legend[row[label_field]] = {}
                    if legend_field:
                        if legend_field in row:
                            series_by_label_legend[row[label_field]
                                                ][row[legend_field]] = row["Value"]
                            if row[legend_field] not in legends:
                                legends.append(row[legend_field])
                    else:
                        series_by_label_legend[row[label_field]
                                            ] = row["Value"]

            series = []
            # Write to Labels, Legends, and Series
            # Defines Limit
            limit_label = 1000  # Unlimited
            limit_legend = 1000  # Unlimited
            if block.block_type in ('bar', 'line', 'line-treshold', 'stackbar', 'hbar'):
                if not legends:
                    if label_ttype not in ('date', 'datetime'):
                        limit_label = 40
                else:
                    if label_ttype not in ('date', 'datetime'):
                        limit_label = 25
                    if legend_ttype not in ('date', 'datetime'):
                        limit_legend = 10

                    # Limit Legends
                    total_per_legend = {}
                    sorted_legends = []
                    for legend in legends:
                        total_per_legend[legend] = 0
                        for label in labels:
                            if legend in series_by_label_legend[label]:
                                total_per_legend[legend] += series_by_label_legend[label][legend]

                        index = 0
                        for sorted_legend in sorted_legends:
                            if total_per_legend[legend] > total_per_legend[sorted_legend]:
                                break
                            index += 1
                        sorted_legends.insert(index, legend)
                    legends = sorted_legends

            if block.block_type in ('pie', 'donut', 'gauge'):
                limit_label = 10

            # Check Value of Label/Legend Limit
            if block.group_limit:
                limit_label = block.group_limit
            if block.subgroup_limit:
                limit_legend = block.subgroup_limit

            # Iterate Legends and Labels to Fill Series
            if legends:
                for index_legend, legend in enumerate(legends):
                    if index_legend <= limit_legend:
                        # Others
                        if not block.show_subgroup_others and index_legend == limit_legend:
                            continue

                        subseries = []
                        for index_label, label in enumerate(labels):
                            if index_label < limit_label:
                                if legend in series_by_label_legend[label]:
                                    subseries.append(
                                        series_by_label_legend[label][legend])
                                else:
                                    subseries.append(0)
                            else:
                                # Others
                                if block.show_group_others:
                                    if index_label == limit_label:
                                        if legend in series_by_label_legend[label]:
                                            subseries.append(
                                                series_by_label_legend[label][legend])
                                        else:
                                            subseries.append(0)
                                    else:
                                        if legend in series_by_label_legend[label]:
                                            subseries[limit_label] += series_by_label_legend[label][legend]
                        series.append(subseries)
                    else:
                        # Others
                        if block.show_subgroup_others:
                            for index_label, label in enumerate(labels):
                                if index_label <= limit_label:
                                    if legend in series_by_label_legend[label]:
                                        series[limit_legend][index_label] += series_by_label_legend[label][legend]

            else:
                for index, label in enumerate(labels):
                    if index < limit_label:
                        series.append(series_by_label_legend[label])
                    else:
                        # Others
                        if block.show_group_others:
                            if index == limit_label:
                                series.append(series_by_label_legend[label])
                            else:
                                series[limit_label] += series_by_label_legend[label]
                if block.block_type in ('bar', 'line', 'line-treshold', 'stackbar', 'hbar'):
                    series = [series]

            # Others
            if len(labels) > limit_label:
                last_n = len(labels) - (limit_label)
                del labels[-last_n:]
                if block.show_group_others:
                    labels.append('Others')
            if len(legends) > limit_legend:
                last_n = len(legends) - (limit_legend)
                del legends[-last_n:]
                if block.show_subgroup_others:
                    legends.append('Others')

            # Recheck Labels and Legends. For Many2one, Selection, and Null Values
            for index_legend, legend in enumerate(legends):
                if legend == 'Others':
                    continue
                elif not legend:
                    legends[index_legend] = 'Undefined'
                elif legend_ttype == 'many2one':
                    legends[index_legend] = request.env[block.subgroup_field_id.relation].browse(legend).name
                elif legend_ttype == 'selection':
                    legends[index_legend] = legends[index_legend].replace('_', ' ').capitalize()
            for index_label, label in enumerate(labels):
                if label == 'Others':
                    continue
                elif not label:
                    labels[index_label] = 'Undefined'
                elif label_ttype == 'many2one':
                    labels[index_label] = request.env[block.group_field_id.relation].browse(label).name
                elif label_ttype == 'selection':
                    labels[index_label] = labels[index_label].replace('_', ' ').capitalize()

            # Exception for Pie. Legends = Labels
            if block.block_type in ('pie', 'donut', 'gauge'):
                legends = labels

            # Cumulative Calculation
            if block.time_calculation_method in ('cumulative', 'before'):
                if label_ttype in ('date', 'datetime'):
                    for index_series, subseries in enumerate(series):
                        total_cur_value = 0
                        for index_subseries, value in enumerate(subseries):
                            series[index_series][index_subseries] = total_cur_value + value
                            total_cur_value = series[index_series][index_subseries]
            if block.time_calculation_method == 'before': 
                if label_ttype in ('date', 'datetime'):
                    for index_series, subseries in enumerate(series):
                        total_cur_value = 0
                        for index_subseries, value in enumerate(subseries):
                            # Check From Query Result Before
                            for record in query_result_before:
                                if 'Value' in record and record['Value']:
                                    if legends and record[legend_field] == legends[index_series]:
                                        series[index_series][index_subseries] = record['Value'] + value
                                    elif not legends:
                                        series[index_series][index_subseries] = record['Value'] + value

            data_block = {
                'id': block.id,
                'title': block.name,
                'series': series,
                'labels': labels,
                'legends': legends,
                'threshold': 0,
                'block_type': block.block_type,
                'block_size': block.block_size,
                'menu_id': block.menu_id.id if block.menu_id else '',
                'link': block.link or '',
                'model_id': block.model_id.id,
                'model_name': block.model_id.name,
                'field_id': block.field_id.id,
                'field_name': block.field_id.field_description,
                'operation': block.operation,
                'sort': block.sort,
                'group_field_id': block.group_field_id.id,
                'group_field_ttype': block.group_field_id.ttype,
                'group_field_name': block.group_field_id.field_description,
                'group_date_format': block.group_date_format,
                'group_limit': block.group_limit,
                'show_group_others': block.show_group_others,
                'subgroup_field_id': block.subgroup_field_id.id,
                'subgroup_field_ttype': block.subgroup_field_id.ttype,
                'subgroup_field_name': block.subgroup_field_id.field_description,
                'subgroup_date_format': block.subgroup_date_format,
                'subgroup_limit': block.subgroup_limit,
                'show_subgroup_others': block.show_subgroup_others,
                'domain_date_field_id': block.domain_date_field_id.id,
                'domain_date_field_name': block.domain_date_field_id.field_description,
                'domain_date': block.domain_date,
                'domain_values_field_id': block.domain_values_field_id.id,
                'domain_values_field_name': block.domain_values_field_id.field_description,
                'domain_values_string': block.domain_values_string,
                'subdomain_values_field_id': block.subdomain_values_field_id.id,
                'subdomain_values_field_name': block.subdomain_values_field_id.field_description,
                'subdomain_values_string': block.subdomain_values_string,
                'time_calculation_method': block.time_calculation_method,
                'domain': block.domain
            }
        return data_block

    def empty_block_data(self, block, exception=False):
        data_block = {
                'id': block.id,
                'title': block.name,
                'block_type': block.block_type,
                'block_size': block.block_size,
                'series': [],
                'labels': [],
                'legends': [],
                'value': '0',
                'uom': '',
                'desc': block.name,
                'model_id': block.model_id.id,
                'model_name': block.model_id.name,
                'field_id': block.field_id.id,
                'field_name': block.field_id.field_description,
                'operation': block.operation,
                'sort': block.sort,
                'group_field_id': block.group_field_id.id,
                'group_field_ttype': block.group_field_id.ttype,
                'group_field_name': block.group_field_id.field_description,
                'group_date_format': block.group_date_format,
                'group_limit': block.group_limit,
                'show_group_others': block.show_group_others,
                'subgroup_field_id': block.subgroup_field_id.id,
                'subgroup_field_ttype': block.subgroup_field_id.ttype,
                'subgroup_field_name': block.subgroup_field_id.field_description,
                'subgroup_date_format': block.subgroup_date_format,
                'subgroup_limit': block.subgroup_limit,
                'show_subgroup_others': block.show_subgroup_others,
                'domain_date_field_id': block.domain_date_field_id.id,
                'domain_date_field_name': block.domain_date_field_id.field_description,
                'domain_date': block.domain_date,
                'domain_values_field_id': block.domain_values_field_id.id,
                'domain_values_field_name': block.domain_values_field_id.field_description,
                'domain_values_string': block.domain_values_string,
                'subdomain_values_field_id': block.subdomain_values_field_id.id,
                'subdomain_values_field_name': block.subdomain_values_field_id.field_description,
                'subdomain_values_string': block.subdomain_values_string,
                'time_calculation_method': block.time_calculation_method,
                'domain': block.domain
            }
        if exception:
            data_block['error'] = serialize_exception(exception)
        return data_block

    @http.route('/api/dashboard/new_block/<int:dashboard_id>/<block_size>', type="http", auth="none", methods=['GET'], csrf=False, cors='*')
    @check_session_id
    def new_block(self, dashboard_id, block_size, **kw):
        User = request.env['res.users']
        Dashboard = request.env['web.dashboard']
        DashboardBlock = request.env['web.dashboard.block']

        user_id = request.session.uid
        user = User.browse(user_id)

        dashboard = False
        if dashboard_id == 0:
            dashboard = Dashboard.search([], limit=1)
        else:
            dashboard = Dashboard.search([('id', '=', dashboard_id)], limit=1)
        
        if not dashboard:
            return error_response(400, 'ID not found', 'ID not found')
        if not block_size:
            return error_response(400, 'Block size not found', 'Block size not found')

        dashboard = dashboard[0]
        block_ids = DashboardBlock.search([('dashboard_id', '=', dashboard.id)], order='sequence asc, id asc')
        data_block = False
        for index, block in enumerate(block_ids):
            if (index+1 < len(block_ids) and block.block_size == block_size and block_size != block_ids[index+1].block_size) \
                or index+1 == len(block_ids):
                new_block = DashboardBlock.create({
                    'block_type': block.block_type,
                    'block_size': block_size,
                    'data_source': 'query',
                    'name': 'New Block',
                    'sequence': block.sequence + 1,
                    'dashboard_id': block.dashboard_id.id
                })
                data_block = self.empty_block_data(new_block)
                break
        if not data_block:
            return error_response(500, 'Cannot create block', 'Cannot create block')
        return self.success_response(data_block)

    @http.route('/api/dashboard/<int:dashboard_id>', type="http", auth="none", methods=['GET'], csrf=False, cors='*')
    @check_session_id
    def get_dashboard(self, dashboard_id, **kw):
        User = request.env['res.users']
        Dashboard = request.env['web.dashboard']
        DashboardBlock = request.env['web.dashboard.block']

        user_id = request.session.uid
        user = User.browse(user_id)

        if dashboard_id == 0:
            dashboards = Dashboard.search([])
        else:
            dashboards = Dashboard.search([('id', '=', dashboard_id)])

        data_blocks = []
        for db in dashboards:
            block_ids = DashboardBlock.search([('dashboard_id', '=', db.id)], order='sequence asc, id asc')
            for index, block in enumerate(block_ids):
                try:
                    data_block = self.get_data_block(block)
                except Exception as exception:
                    data_block = self.empty_block_data(block, exception)
                    request._cr.rollback()
                data_blocks.append(data_block)

        return self.success_response(data_blocks)

    @http.route('/api/dashboard/block/<int:block_id>', type="json", auth="none", methods=['POST'], csrf=False, cors='*')
    @check_session_id
    def get_updated_dashboard_block(self, block_id, **kw):
        update_fields = ('name', 'model_id', 'field_id', 'operation', 'sort', 'group_field_id', 'subgroup_field_id', 'group_date_format', 'subgroup_date_format',
                        'group_limit', 'subgroup_limit', 'show_group_others', 'show_subgroup_others', 'block_type',
                        'domain_date_field_id', 'domain_date', 'domain_values_field_id', 'domain_values_string', 'subdomain_values_field_id', 'subdomain_values_string',
                        'time_calculation_method', 'domain')
        try:
            jdata = json.loads(request.httprequest.stream.read().decode('utf-8')) or {}
            User = request.env['res.users']
            DashboardBlock = request.env['web.dashboard.block']

            user_id = request.session.uid
            user = User.browse(user_id)

            if not block_id:
                return error_response(400, 'ID tidak ditemukan', 'ID tidak ditemukan')

            block = DashboardBlock.browse(block_id)
            vals = {}
            for field in update_fields:
                if field in jdata:
                    vals[field] = jdata[field]

            # Reset Model
            if jdata.get('reset_model') and jdata.get('model_id'):
                field_model = request.env['ir.model.fields'].search([
                    ('model_id', '=', int(jdata.get('model_id'))),
                    ('name', '=', 'id')
                ])
                vals = {
                    'model_id': int(jdata.get('model_id')),
                    'field_id': field_model.id or False,
                    'operation': 'sum',
                    'sort': 'desc',
                    'group_field_id': False,
                    'subgroup_field_id': False,
                    'group_date_format': False,
                    'subgroup_date_format': False,
                    'group_limit': 0,
                    'subgroup_limit': 0,
                    'show_group_others': False,
                    'show_subgroup_others': False,
                    'domain_date_field_id': False, 
                    'domain_date': False,
                    'domain': False,
                    'time_calculation_method': 'normal',
                    'domain_values_field_id': False,
                    'domain_values_string': False,
                    'subdomain_values_field_id': False,
                    'subdomain_values_string': False,
                }
            # Allow edit if it will be rolled back
            if not (jdata.get('save', False)):
                block = block.sudo()
            block.update(vals)
            data_block = self.get_data_block(block)
            
            # Save if jdata contains save = true, else rollback
            if not (jdata.get('save', False)):
                request._cr.rollback()

            return self.success_response(data_block)
        except Exception as exception:
            error = {
                'code': 500,
                'message': "Odoo Server Error",
                'data': serialize_exception(exception)
            }
            return error_response(error['code'], error['message'], error['data'] or error['message'])
