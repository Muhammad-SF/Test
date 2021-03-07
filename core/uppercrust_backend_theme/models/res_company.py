# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
from odoo import _, api, fields, models,tools
from odoo.modules.module import get_module_resource
from odoo import tools

class ResCompany(models.Model):
    _inherit = "res.company"

    # @api.model
    # def call_my_me(self,*kw):
    #     print(self,"MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMm",self.env.context)
    #     menuobj = self.env['ir.ui.menu']
    #     if self.env.context.get('search_val'):
    #         search_val = self.env.context.get('search_val')
    #         menu_data = menuobj.search([('action', '!=', False),('name', 'ilike', search_val)])
    #         print ('JJJJJJJJJJJJJJJJJJjj',menu_data)
            # return menu_data
    
    @api.multi
    def write(self, vals):
        # for websote logo=================
        if not vals.get('theme_logo'):
            theme_logo_path = get_module_resource('uppercrust_backend_theme', 'static/src/img', 'theme-logo.png')
            with open(theme_logo_path, 'rb') as handler:            
                theme_logo_data = handler.read()
            vals.update({'theme_logo':tools.image_resize_image_big(theme_logo_data.encode('base64')),
                    })
        # for websote icon=================
        if not vals.get('theme_icon'):
            theme_icon_path = get_module_resource('uppercrust_backend_theme', 'static/src/img', 'theme-icon.png')
            with open(theme_icon_path, 'rb') as handler:            
                theme_icon_data = handler.read()

            vals.update({'theme_icon':tools.image_resize_image_big(theme_icon_data.encode('base64'))})
        res = super(ResCompany, self).write(vals)
        return res


    @api.depends('partner_id', 'partner_id.image')
    def _compute_logo_web(self):
        for company in self:
            if company.theme_logo:
                company.logo_web = tools.image_resize_image(company.theme_logo, (180, None))
            else:
                company.logo_web = tools.image_resize_image(company.partner_id.image, (180, None))

    logo_web = fields.Binary(compute='_compute_logo_web', store=True)
    theme_logo = fields.Binary(string='Theme Logo')
    theme_icon = fields.Binary(string='Theme Icon')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
