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
  "name"                 :  "Mobikul Merge Category",
  "summary"              :  """Allows you to merge product categories in Mobikul on just a single click.""",
  "category"             :  "Sales",
  "version"              :  "1.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo.html",
  "description"          :  """Allows you to merge product categories in Mobikul on just a single click.""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=mobikul_cat_merge&version=12.0",
  "depends"              :  [
                             'product',
                             'mobikul',
                             'wk_wizard_messages',
                            ],
  "data"                 :  ['mobikul_cat_merge_view.xml','security/ir.model.access.csv'],
  "images"               :  ['static/description/banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
}
