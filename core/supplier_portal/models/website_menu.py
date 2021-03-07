from odoo import models, fields, api

# class website_menu(models.Model):
#     _inherit = 'website.menu'
#
#     @api.model
#     def search(self, args, offset=0, limit=0, order=None, count=False):
#         res = super(website_menu, self).search(args=args, offset=offset, limit=limit, order=order, count=count)
#         if self.env.user and self.env.user.has_group('base.group_portal'):
#             return res
#         else:
#             if 'My Account' in res.mapped('name'):
#                 return res.filtered(lambda record:record.name != 'My Account')
#             else:
#                 return res