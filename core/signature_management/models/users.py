# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
import logging
import os
import re
from odoo.tools import config, human_size, ustr, html_escape
_logger = logging.getLogger(__name__)

class Users(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    signature = fields.Binary(string='Signature')
    datas_fname = fields.Char('File Name')
    file_size = fields.Integer('File Size', readonly=True)
    checksum = fields.Char("Checksum/SHA1", size=40, index=True, readonly=True)
    # the field 'datas' is computed and may use the other fields below
    db_datas = fields.Binary('Database Data')
    upload_datas = fields.Binary(string='Signature File')
    main_signature = fields.Selection([('upload_file','Uploaded File'),('draw_your_signature','Draw Your Signature')], default = 'upload_file')
