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
  "name"                 :  "Product Pack",
  "summary"              :  """Combine two or more products together in order to create a bundle product.""",
  "category"             :  "Sales Management",
  "version"              :  "6.3.9",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Product-Pack.html",
  "description"          :  """http://webkul.com/blog/odoo-product-pack/
                              Pack  product allows you to create the packs or bundles of the products. 
                              You can sell the products in bundles.""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=wk_product_pack&version=14.0",
  "depends"              :  ['sale_stock','website_sale_stock'],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'wizard/product_pack_wizard.xml',
                             'views/template.xml',
                             'views/wk_product_pack.xml',
                            ],
  "demo"                 :  ['data/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  69,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
