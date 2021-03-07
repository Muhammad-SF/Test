#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

import models
from odoo import api, SUPERUSER_ID

def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import Warning
    version_info = common.exp_version()
    server_serie =version_info.get('server_serie')
    if server_serie!='10.0':raise Warning('Module support Odoo series 10.0 found {}.'.format(server_serie))

def _auto_configuration(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_values_obj = env['ir.values']
    ir_values_obj.sudo().set_default('website.product.video.settings', 'youtube_api_key', 'AIzaSyD3TadJCd0Ww-QDpJfZqzMczPBiepFe-7E', True)
    ir_values_obj.sudo().set_default('website.product.video.settings', 'controls', '0', True)
    ir_values_obj.sudo().set_default('website.product.video.settings', 'showinfo', '1', True)
    ir_values_obj.sudo().set_default('website.product.video.settings', 'rel', '1', True)
    ir_values_obj.sudo().set_default('website.product.video.settings', 'iv_load_policy', '3', True)
    ir_values_obj.sudo().set_default('website.product.video.settings', 'video_height', '345', True)
    ir_values_obj.sudo().set_default('website.product.video.settings', 'video_width', '420', True)
    ir_values_obj.sudo().set_default('website.product.video.settings', 'disablekb', 'False', True)
    ir_values_obj.sudo().set_default('website.config.settings', 'group_website_multi_video', 'True', True)
