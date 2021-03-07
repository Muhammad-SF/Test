# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
from odoo import _, api, fields, models,tools
from odoo.http import request

class Menu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def menu_data_proper(self, menu_data):
        menu_data = [record for record in menu_data if record.get('name') not in ['Discuss']]
        odd_list = False if len(menu_data) % 2 == 0 else True
        final_list = []
        empty_list = []
        for i in range(0, len(menu_data)):
            if i%2 == 0:
                empty_list = []
                empty_list.append(menu_data[i])
            else:
                empty_list.append(menu_data[i])
                final_list.append(empty_list)
            if odd_list and (len(menu_data) - i) == 1:
                final_list.append(empty_list)
        return final_list

    @api.model
    def get_discuss_menu(self):
        menu_id = self.env.ref('mail.mail_channel_menu_root_chat').id
        action_id = self.env.ref('mail.mail_channel_action_client_chat').id
        href = '/web#menu_id=%s&action=%s'%(menu_id, action_id)
        return href

    @api.model
    def get_top_menus(self):
        menu_data = self.load_menus(request.debug)
        child_data = menu_data.get('children')
        counter = 1
        final_data = []
        for record in child_data:
            if record.get('name') not in ['Discuss'] and counter <= 7:
                final_data.append(record)
                counter += 1
        return final_data

    @api.model
    def get_filter_top_menus(self):
        # search_keyword = self.env.context.get('search_keyword')
        # final_data = []
        # if search_keyword:
        menu_data = self.load_menus(request.debug)
        child_data = menu_data.get('children')
        filter_data = filter(lambda r: not r.get('parent_id'), child_data)
        for record in filter_data:
            src = '/web/content/?model=ir.ui.menu&id=%s&field=web_icon_data'%(record['id'])
            href = '/web#menu_id=%s&action=%s' % (record['id'], record['action'] and record['action'].split(',')[1] or '')
            record.update({'src': src, 'href': href})
        final_data = self.menu_data_proper(filter_data)
        return final_data