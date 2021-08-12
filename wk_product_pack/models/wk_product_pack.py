#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	def compute_discounted_pack_price(self):
		for product in self:
			product.has_discounted_amount = False
			product.pack_products_price = 0
			if product.is_pack:
				price = 0
				for prod in product.wk_product_pack:
					price = price + prod.product_id.lst_price * prod.product_quantity
				rem_price = price - product.lst_price
				product.pack_products_price = price
				if rem_price <= 0:
					product.has_discounted_amount = True

	is_pack = fields.Boolean(
		string='Is product pack')
	wk_product_pack = fields.One2many(
		comodel_name='product.pack', 
		inverse_name='wk_product_template', 
		string='Product pack', copy=True)
	pack_stock_management = fields.Selection(
		[('decrmnt_pack', 'Decrement Pack Only'),
		('decrmnt_products', 'Decrement Products Only'),
		('decrmnt_both', 'Decrement Both')], 
		string='Pack Stock Management', 
		default='decrmnt_both')

	has_discounted_amount = fields.Boolean(
		compute="compute_discounted_pack_price",
		string="Remaning price")
	pack_products_price = fields.Float(
		compute="compute_discounted_pack_price",
		string="Total Product Price")


	@api.model
	def create(self, vals):
		if vals.get('is_pack'):
			if not vals.get('wk_product_pack'):
				raise ValidationError(
					'No products in this pack. Select atleast one product.')
		return super(ProductTemplate, self).create(vals)
			
class ProductProduct(models.Model):
	_inherit = "product.product"
	
	@api.onchange('type')
	def select_default_pack_mgmnt_onchange_type(self):
		if self.is_pack:
			prd_type = self.type
			if prd_type == 'consu':
				self.pack_stock_management = 'decrmnt_pack'
			elif prd_type == 'product' or prd_type == 'service':
				self.pack_stock_management = 'decrmnt_products'


class ProductPack(models.Model):
	_name = 'product.pack'
	_description = 'Product Pack'

	product_id = fields.Many2one(
		comodel_name='product.product', string='Product', required=True)
	product_quantity = fields.Float(
		string='Quantity', required=True, default=1)
	wk_product_template = fields.Many2one(
		comodel_name='product.template', string='Product pack')
	wk_image = fields.Binary(
		related='product_id.image_512', string='Image', store=True)
	price = fields.Float(related='product_id.lst_price',
						 string='Product Price')
	uom_id = fields.Many2one(
		related='product_id.uom_id', string="Unit of Measure", readonly="1")
	name = fields.Char(related='product_id.name', readonly="1")


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	def _action_launch_stock_rule(self,previous_product_uom_qty=False):
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		errors = []
		ctx = dict(self._context or {})
		filteredObj = []

		if ctx.get('wk_skip'):
			filterIds = ctx.get('wk_skip')
			filteredObj = self.filtered(lambda obj : obj.id not in filterIds)
		else:
			filteredObj = self

		for line in filteredObj:
			if line.product_id.is_pack:
				qty = line._get_qty_procurement()
				if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
					continue
				
				group_id = line.order_id.procurement_group_id
				if not group_id:
					group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
					line.order_id.procurement_group_id = group_id
				else:
					# In case the procurement group is already created and the order was
					# cancelled, we need to update certain values of the group.
					updated_vals = {}
					if group_id.partner_id != line.order_id.partner_shipping_id:
						updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
					if group_id.move_type != line.order_id.picking_policy:
						updated_vals.update({'move_type': line.order_id.picking_policy})
					if updated_vals:
						group_id.write(updated_vals)

				values = line._prepare_procurement_values(group_id=group_id)
				product_qty = line.product_uom_qty - qty

				if line.product_id.pack_stock_management == 'decrmnt_both':
					product_qty = line.product_uom_qty - qty
					procurements = []

					try:
						procurements.append(self.env['procurement.group'].Procurement(
						line.product_id, line.product_uom_qty, line.product_id.uom_id,
						line.order_id.partner_shipping_id.property_stock_customer,
						line.name, line.order_id.name, line.order_id.company_id, values))
						if procurements:
							self.env['procurement.group'].run(procurements)

					except UserError as error:
						errors.append(error.name)
					
				if line.product_id.pack_stock_management != 'decrmnt_pack':
					for pack_obj in line.product_id.wk_product_pack:
						procurements=[]
						product_qty = pack_obj.product_quantity

						try:
							product_qty = line.product_uom_qty * pack_obj.product_quantity
							procurements.append(self.env['procurement.group'].Procurement(
							pack_obj.product_id, product_qty, pack_obj.product_id.uom_id,
							line.order_id.partner_shipping_id.property_stock_customer,
							line.name, line.order_id.name, line.order_id.company_id, values))
							if procurements:
								self.env['procurement.group'].run(procurements)
			
						except UserError as error:
							errors.append(error.name)
				if line.product_id.pack_stock_management == 'decrmnt_products':
					return

			if errors:
				raise UserError('\n'.join(errors))

		return super(SaleOrderLine, self)._action_launch_stock_rule()

	@api.onchange('product_uom_qty', 'product_uom', 'route_id')
	def _compute_is_mto(self):
		res = super(SaleOrderLine,self)._compute_is_mto()
		for product in self:
			product_obj = product.product_id
			if product.product_id.type == 'product':
				if product_obj.is_pack:
					warning_mess = {}
					for pack_product in product_obj.wk_product_pack:
						qty = product.product_uom_qty
						if qty * pack_product.product_quantity > pack_product.product_id.virtual_available:
							warning_mess = {
								'title': _('Not enough inventory!'),
								'message': ('You plan to sell %s quantities of the pack %s but you have only  %s quantities of the product %s available, and the total quantity to sell is  %s !!' % (qty, pack_product.product_id.name, pack_product.product_id.virtual_available, pack_product.product_id.name, qty * pack_product.product_quantity))
							}
							return {'warning': warning_mess}
		return res


