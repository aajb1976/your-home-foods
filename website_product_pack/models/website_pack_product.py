#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)
class ProductTemplate(models.Model):
	_inherit = 'product.template'

	def get_discounted_pack_price(self, product_id):
		if product_id:
			product = self.sudo().browse(product_id)
			if product.is_pack:
				price = 0
				for prod in product.wk_product_pack:
					price = price + prod.product_id.price * prod.product_quantity
				return price - product.price

class ProductPack(models.Model):
	_inherit = 'product.pack'
	def get_product_id(self,product_id):
		if product_id:
			product = self.sudo().browse(product_id)
			return product

		
