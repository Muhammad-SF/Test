# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools,SUPERUSER_ID, _
    

class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        hide_menu = [
            'std_pos_sync.menu_pos_sync',
        ]
        menu_ids = []
        pos_client = self.env.ref('std_pos_sync.pos_client').value
        if pos_client == 'False':
            for menu_item in hide_menu:
                menu = self.env.ref(menu_item)
                if menu and menu.id:
                    menu_ids.append(menu.id)
        if menu_ids and len(menu_ids) > 0:
            args.append('!')
            args.append(('id', 'child_of', menu_ids))
        return super(ir_ui_menu, self).search(args, offset, limit, order, count=count)

