# # -*- coding: utf-8 -*-
# import logging
# from odoo import models, api
#
# from .ir_translation import debrand
#
# _logger = logging.getLogger(__name__)
#
#
# class View(models.Model):
#     _inherit = 'ir.ui.view'
#
#     # all view
#     @api.multi
#     def read_combined(self, fields=None):
#         res = super(View, self).read_combined(fields=fields)
#         res['arch'] = debrand(self.env, res['arch'], is_code=True)
#         return res
#
#     @api.model
#     def render_template(self, template, values=None, engine='ir.qweb'):
#         if template in ['web.login', 'web.webclient_bootstrap']:
#             if not values:
#                 values = {}
#             values["title"] = self.env['ir.values'].get_default('base.config.settings', "sync_app_system_name")
#         return super(View, self).render_template(template, values=values, engine=engine)


# -*- coding: utf-8 -*-
import logging
from odoo import models, api

from .ir_translation import debrand

_logger = logging.getLogger(__name__)

MODULE = '_sync_uppercrust_debranding'


class View(models.Model):
    _inherit = 'ir.ui.view'

    @api.multi
    def read_combined(self, fields=None):
        res = super(View, self).read_combined(fields=fields)
        if isinstance(res['arch'], str) and not isinstance(res['arch'], unicode):
            res['arch'] = res['arch'].decode('utf-8')
        res['arch'] = debrand(self.env, res['arch'])
        return res

    # @api.model
    # def render_template(self, template, values=None, engine='ir.qweb'):
    #     if template in ['web.login', 'web.webclient_bootstrap']:
    #         if not values:
    #             values = {}
    #         values["title"] = self.env['ir.config_parameter'].sudo().get_param("app_system_name", "odooApp")
    #     return super(View, self).render_template(template, values=values, engine=engine)

    @api.model
    def render_template(self, template, values=None, engine='ir.qweb'):
        if template in ['web.login', 'web.webclient_bootstrap']:
            if not values:
                values = {}
            values["title"] = self.env['ir.config_parameter'].sudo().get_param("sync_app_system_name", "yourcompany")
        return super(View, self).render_template(template, values=values, engine=engine)
