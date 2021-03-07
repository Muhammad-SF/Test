# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class LabelSize(models.Model):
    _name = 'label.size'
    _description = 'Label Size'

    height = fields.Char(string='Height', help='enter height in mm.')
    width = fields.Char(string='Width', help='enter width in mm.')


LabelSize()
