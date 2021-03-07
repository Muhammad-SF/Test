# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from openerp import api, fields, models, _


# Switch Lenguage
class BaseLanguageInstall(models.TransientModel):
    _inherit = "base.language.install"

    @api.multi
    def lang_install(self):
        self.ensure_one()
        self.env.cr.execute("""
            delete from ir_translation
            where (name='ir.module.module,shortdesc' 
                    or name='ir.module.module,description' 
                    or name='ir.module.module,summary')
                and lang=%s
            """, (self.lang,))
        return super(BaseLanguageInstall, self).lang_install()
