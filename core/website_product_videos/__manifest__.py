# -*- coding: utf-8 -*-
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
{
  "name"                 :  "Odoo Website Product Multi-Videos",
  "summary"              :  """Odoo Website Product Videos With Multi Images allows you to add product videos on the website to provide a deeper insight into the products.""",
  "category"             :  "Website",
  "version"              :  "1.1.1",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Website-Product-Videos-With-Multi-Images.html",
  "description"          :  """Odoo Website Product Videos With Multi Images
Website Product Videos With Multi Images
Product Videos
Product Videos With Multi Images
Odoo Website
Videos With Multi Images
Videos in Odoo Website
Odoo Website Product Videos
Product Videos With Multi Images in Odoo Website
Website Product Videos
Odoo
Website
Videos in Website
Show Videos in Odoo Website""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=website_product_videos",
  "depends"              :  [
                             'website_sale',
                             'website_webkul_addons',
                            ],
  "data"                 :  [
                             'views/templates.xml',
                             'security/product_video.xml',
                             'security/ir.model.access.csv',
                             'views/res_config_view.xml',
                             'views/product_views.xml',
                             'views/webkul_addons_config_inherit_view.xml',
                            ],
  "demo"                 :  ['data/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  45,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
  "post_init_hook"       :  "_auto_configuration",
}