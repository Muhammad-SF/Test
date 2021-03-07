# -*- coding: utf-8 -*-
# Part of Synconics. See LICENSE file for full copyright and licensing details.
import os
import zipfile
import StringIO
import functools
import json
import base64
import mimetypes
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition
from odoo.addons.web.controllers.main import _serialize_exception
import werkzeug
from odoo.tools.translate import _
from odoo.addons import mail
from odoo.addons import web
import logging

_logger = logging.getLogger(__name__)

try:
    import simplejson as simplejson
except ImportError:
    import json     # noqa
    
def serialize_exception(f):
    _logger = logging.getLogger(__name__)

    @functools.wraps(f)
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception, e:
            _logger.exception("An exception occured during an http request")
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return werkzeug.exceptions.InternalServerError(simplejson.dumps(error))
    return wrap

class Binary(web.controllers.main.Binary):

    @http.route('/web/binary/upload_attachment', type='http', auth="user", csrf=True)    
    def upload_attachment(self, callback, model, id, ufile, multi=False):
        if multi:            
            Model = request.env['ir.attachment']
            out = """<script language="javascript" type="text/javascript">
                        var win = window.top.window;
                        win.jQuery(win).trigger(%s, %s);
                    </script>"""
            try:
                attachment = Model.create({
                    'name': ufile.filename,
                    'datas': base64.encodestring(ufile.read()),
                    'datas_fname': ufile.filename,
                    'res_model': model,
                    'res_id': int(id)
                    })
                args = {
                    'filename': ufile.filename,
                    'mimetype': ufile.content_type,
                    'id':  attachment.id
                }
            except Exception:
                args = {'error': _("Something horrible happened")}
                _logger.exception("Fail to upload attachment %s" % ufile.filename)
                return out % (json.dumps(callback), json.dumps(args))
            return str(attachment.id)
        else:
            return super(Binary, self).upload_attachment(callback, model, id, ufile)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: