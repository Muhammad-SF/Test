# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import json
import odoo
import os
import sys
import jinja2
from odoo import http, tools
from odoo.addons.web.controllers.main import Database, Binary
from odoo.addons.web.controllers import main
from odoo.modules import get_resource_path
from odoo.http import request

from odoo import http
from odoo.addons.web.controllers.main import WebClient
from odoo.addons.web.controllers import main as controllers_main
import functools
from odoo.modules import get_module_resource
import io
import base64

from ..models.ir_translation import debrand, debrand_bytes

db_monodb = http.db_monodb

if hasattr(sys, 'frozen'):
    # When running on compiled windows binary, we don't have access to package loader.
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'views'))
    loader = jinja2.FileSystemLoader(path)
else:
    loader = jinja2.PackageLoader('odoo.addons.sync_uppercrust_debranding', "views")
env = main.jinja2.Environment(loader=loader, autoescape=True)
env.filters["json"] = json.dumps
db_monodb = http.db_monodb


class OdooDebrand(Database):
    # Render the Database management html page
    def _render_template(self, **d):
        d.setdefault('manage', True)
        d['insecure'] = odoo.tools.config['admin_passwd'] == 'admin'
        d['list_db'] = odoo.tools.config['list_db']
        d['langs'] = odoo.service.db.exp_list_lang()
        d['countries'] = odoo.service.db.exp_list_countries()
        d['pattern'] = main.DBNAME_PATTERN
        # databases list
        d['databases'] = []
        try:
            d['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            monodb = db_monodb()
            if monodb:
                d['databases'] = [monodb]
        try:
            d['company_name'] = request.env['ir.values'].get_default('debrand.config.settings', "sync_app_system_name")
            d['favicon_url'] = request.env['ir.values'].get_default('debrand.config.settings', "sync_app_company_fevicon")
            return env.get_template("database_manager_extend.html").render(d)
        except Exception as e:
            d['company_name'] = ''
            d['favicon_url'] = ''
            d['company_logo_url'] = ''
            return main.env.get_template("database_manager.html").render(d)

class BinaryCustom(Binary):

    @http.route([
        '/web/binary/company_logo',
        '/logo',
        '/logo.png',
    ], type='http', auth="none")
    def company_logo(self, dbname=None, **kw):
        imgname = 'website-logo.png'
        default_logo_module = 'sync_uppercrust_debranding'
        if request.session.db:
            default_logo_module = request.env['ir.config_parameter'].sudo().get_param('sync_uppercrust_debranding.default_logo_module')
        placeholder = functools.partial(get_module_resource, default_logo_module, 'static', 'src', 'img')
        uid = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        elif dbname is None:
            dbname = db_monodb()

        if not uid:
            uid = odoo.SUPERUSER_ID

        if not dbname:
            response = http.send_file(placeholder(imgname))
        else:
            try:
                # create an empty registry
                registry = odoo.modules.registry.Registry(dbname)
                with registry.cursor() as cr:
                    cr.execute("""SELECT c.logo_web, c.write_date
                                    FROM res_users u
                               LEFT JOIN res_company c
                                      ON c.id = u.company_id
                                   WHERE u.id = %s
                               """, (uid,))
                    row = cr.fetchone()
                    if row and row[0]:
                        image_data = io.BytesIO(base64.b64decode(row[0]))
                        response = http.send_file(image_data, filename=imgname, mtime=row[1])
                    else:
                        response = http.send_file(placeholder('nologo.png'))
            except Exception:
                response = http.send_file(placeholder(imgname))
        return response
