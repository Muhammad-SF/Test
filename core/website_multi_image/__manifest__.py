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
  "name"                 :  "Website Product Multi Images",
  "summary"              :  """The module allows you to set multiple images for the products available on odoo website.""",
  "category"             :  "Website",
  "version"              :  "1.1.1",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Product-Multi-Images.html",
  "description"          :  """Odoo Website Product Multi Images
Product page carousels
Odoo Multiple product images
Set multi product images
Multi images carousel""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=website_multi_image",
  "depends"              :  ['website_sale'],
  "data"                 :  [
                             'view/product_extra_images_view.xml',
                             'view/templates.xml',
                             'security/ir.model.access.csv',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  49,
  "currency"             :  "USD",
}