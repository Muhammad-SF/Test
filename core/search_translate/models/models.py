# -*- coding: utf-8 -*-

from odoo import models, fields, api
from googletrans import Translator
class search_translate(models.Model):
    _inherit = 'res.partner'

    en_name = fields.Char(string="En Name", compute='_compute_en_name',store=True)

    def _compute_en_name(self):
        translator = Translator()
        for record in self:
            tran = translator.translate(record.name, dest='en')
            record.en_name = str(tran.text)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        new_domain = []
        translator = Translator()
        if domain:
            for sub_domain in domain:
                if sub_domain[0] == 'en_name':
                    en_name =  str(translator.translate(sub_domain[2], dest='en').text)
                    sub_domain[2] = en_name
                new_domain.append(sub_domain)
        res = super(search_translate, self).search_read(domain=new_domain, fields=fields, offset=offset,
                                                      limit=limit, order=order)

        return res
