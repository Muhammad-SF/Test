# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

# from odoo import models
#
#
# class IrActionsActWindowDebranding(models.Model):
#     _inherit = 'ir.actions.act_window'
#
#     def read(self, fields=None, load='_classic_read'):
#         results = super(IrActionsActWindowDebranding, self).read(
#             fields=fields, load=load)
#         if not fields or 'help' in fields:
#             new_name = self.env['ir.values'].get_default('debrand.config.settings', "sync_app_system_name")
#             for res in results:
#                 if isinstance(res, dict) and res.get('help'):
#                     res['help'] = res['help'].replace('Odoo', new_name)
#         return results


# -*- coding: utf-8 -*-
from odoo import models


class IrActionsActWindowDebranding(models.Model):
    _inherit = 'ir.actions.act_window'

    def read(self, fields=None, load='_classic_read'):
        results = super(IrActionsActWindowDebranding, self).read(
            fields=fields, load=load)
        if not fields or 'help' in fields:
            # params = self.env['ir.config_parameter'].get_debranding_parameters()
            new_name = self.env['ir.config_parameter'].sudo().get_param('sync_app_system_title')
            
            # new_name = params.get('web_debranding.new_name')
            for res in results:
                if isinstance(res, dict) and res.get('help'):
                    res['help'] = res['help'].replace('Odoo', new_name)
        return results

