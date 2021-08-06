# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
from odoo import api, fields, models, _
import logging
from odoo import exceptions
_logger = logging.getLogger(__name__)

AR_FORMAT = ["usdz","glb","dae","obj","abc","scn","reality","rcproject","glTF","fbx","usda","usdc","usd","sfa","sfb"]

class ProductTemplate(models.Model):
	_inherit = "product.template"

	def mobikul_publish_button(self):
		self.ensure_one()
		self.is_mobikul_available = not self.is_mobikul_available
		return True


	mobikul_categ_ids = fields.Many2many('mobikul.category', string='Mobikul Product Category')
	mobikul_status = fields.Selection([
	    ('empty', 'Display Nothing'),
	    ('in_stock', 'In-Stock'),
	    ('out_stock', 'Out-of-Stock'),
	], "Product Availability", default='empty', help="Adds an availability status on the mobikul product page.")
	is_mobikul_available = fields.Boolean("Published on App", default=1, help="Allow the end user to choose this price list")
	
	ar_image_ios = fields.Binary("AR Image IOS", help = "Augmented Reality image for mobikul ios devices",attachment = True)
	ar_file_name_ios = fields.Char('File Name')
	ar_image_apk = fields.Binary("AR Image Android", help = "Augmented Reality image for mobikul android devices",attachment = True)
	ar_file_name_apk = fields.Char('File Name')

	@api.constrains('ar_image_ios')
	def _check_filename_ios(self):
		if self.ar_file_name_ios:
			tmp = self.ar_file_name_ios.split('.')
			ext = tmp[len(tmp)-1]
			if ext not in AR_FORMAT:
				raise exceptions.ValidationError((_("The file must be Augmented Reality supported extention file like "), AR_FORMAT))

	@api.constrains('ar_image_apk')
	def _check_filename_apk(self):
		if self.ar_file_name_apk:
			tmp = self.ar_file_name_apk.split('.')
			ext = tmp[len(tmp)-1]
			if ext not in AR_FORMAT:
				raise exceptions.ValidationError((_("The file must be Augmented Reality supported extention file like "), AR_FORMAT))

class ProductTemplate(models.Model):
	_inherit = "product.product"

	ar_image_ios = fields.Binary("AR Image IOS", help = "Augmented Reality image for mobikul",attachment = True)
	ar_file_name_ios = fields.Char('File Name')
	ar_image_apk = fields.Binary("AR Image Android", help = "Augmented Reality image for mobikul",attachment = True)
	ar_file_name_apk = fields.Char('File Name')

	@api.constrains('ar_image_ios')
	def _check_filename_ios(self):
		if self.ar_file_name_ios:
			tmp = self.ar_file_name_ios.split('.')
			ext = tmp[len(tmp)-1]
			if ext not in AR_FORMAT:
				raise exceptions.ValidationError((_("The file must be Augmented Reality supported extention file like "), AR_FORMAT))

	@api.constrains('ar_image_apk')
	def _check_filename_apk(self):
		if self.ar_file_name_apk:
			tmp = self.ar_file_name_apk.split('.')
			ext = tmp[len(tmp)-1]
			if ext not in AR_FORMAT:
				raise exceptions.ValidationError((_("The file must be Augmented Reality supported extention file like "), AR_FORMAT))

	

	def mobikul_publish_button(self):
		self.ensure_one()
		self.is_mobikul_available = not self.is_mobikul_available
		return True

class ProductPublicCategory(models.Model):
	_inherit = 'product.public.category'
	# this field is added for mobikul category merge
	mobikul_cat_id = fields.Many2one('mobikul.category', 'Mobikul Category')



class CrmTeam(models.Model):
	_inherit = "crm.team"

	mobikul_ids = fields.One2many('mobikul', 'salesteam_id', string='Mobikul', help="Mobikul is using these sales team.")
