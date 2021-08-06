# -*- coding: utf-8 -*-
#################################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>:wink:
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
# If not, see <https://store.webkul.com/license.html/>;
#################################################################################
from odoo import api, fields, models, _
from odoo import tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    mobikul_cat_id = fields.Many2one('mobikul.category', 'Mobikul Category')


class MobikulCategory(models.Model):
    _inherit = 'mobikul.category'

    website_cat_id = fields.Many2one('product.public.category', 'Webiste Category')


class mobikul_cat_merge(models.TransientModel):
    _name = 'mobikul.cat.merge'
    _description = "Mobikul category merge"

    # @api.multi
    def linked_mobikul_cat_with_products(self, show_wizard=True):
        website_catg_ids = self.env['product.public.category'].search([])
        length = 0
        error_message = ''
        for cat_id in website_catg_ids:
            website_prods = self.env['product.template'].search(
                [('public_categ_ids', 'in', cat_id.id)])
            for product in website_prods:
                web_cat_ids = product.public_categ_ids
                arr = []
                for web_cat_id in web_cat_ids:
                    arr.append(web_cat_id.mobikul_cat_id.id)
                product.mobikul_categ_ids = [[6, 0, arr]]
                length += 1
        if not error_message:
            error_message = "%s Products(s) has been linked with mobikul category." % (length)
        if length == 0:
            error_message = "All products are already linked with correct Mobikul category."
        return show_wizard and self.show_msg_wizard(error_message) or error_message

    @api.model
    def sync_categories(self, categ):
        if not categ.mobikul_cat_id:
            if categ.parent_id.id:
                p_cat_id = self.sync_categories(categ.parent_id)
                return self.create_categories(categ, p_cat_id)
            else:
                return self.create_categories(categ, False)

        else:
            return categ.mobikul_cat_id.id

    @api.model
    def create_categories(self, obj_catg, id_parent):
        temp_dic = {
            'name': obj_catg.name,
            'parent_id': id_parent,
            'sequence': obj_catg.sequence,
            "website_cat_id": obj_catg.id
        }
        mobikul_cat_id = self.env['mobikul.category'].create(temp_dic)
        obj_catg.write({'mobikul_cat_id': mobikul_cat_id.id})
        return mobikul_cat_id.id

    # @api.multi
    def export_categories(self, show_wizard=True):
        error_message = ''
        website_catg = self.env['product.public.category'].search([('mobikul_cat_id', '=', False)])
        length = len(website_catg)
        for categ in website_catg:
            try:
                self.sync_categories(categ)
            except Exception as e:
                error_message = '\r\nError In Website Product`s Category ID:%s ,Error :%s' % (
                    str(categ.id), str(e))
        error_message = error_message.strip()
        if not error_message:
            error_message = "%s Category(s) has been merged with Mobikul." % (length)
        if length == 0:
            error_message = "No new category(s) Found."
        return show_wizard and self.show_msg_wizard(error_message) or error_message

    def show_msg_wizard(self, msg):
        partial_id = self.env['wk.wizard.message'].sudo().create({'text': msg})
        return {
            'name': "Message",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'wk.wizard.message',
            'res_id': partial_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    # @api.multi
    def sync_mobikul_cat_with_web_cat(self):
        message = self.export_categories(show_wizard=False)
        mobikul_catg_ids = self.env['mobikul.category'].search([])
        for mob_cat in mobikul_catg_ids:
            if self.sync_type and mob_cat.website_cat_id.id:
                if self.sync_type == "name":
                    mob_cat.name = mob_cat.website_cat_id.name
                elif self.sync_type == "name_parent":
                    mob_cat.name = mob_cat.website_cat_id.name
                    mob_cat.parent_id = mob_cat.website_cat_id.parent_id.mobikul_cat_id.id
                elif self.sync_type == "name_parent_seq":
                    mob_cat.name = mob_cat.website_cat_id.name
                    mob_cat.parent_id = mob_cat.website_cat_id.parent_id.mobikul_cat_id.id
                    mob_cat.sequence = mob_cat.website_cat_id.sequence
            else:
                return self.show_msg_wizard("Please select the Sync Type.")

        if self.sync_type == "name":
            message = "Sync all name of mobikul categories and " + message
        elif self.sync_type == "name_parent":
            message = "Sync all name and parent category of mobikul categories and " + message
        elif self.sync_type == "name_parent_seq":
            message = "Sync all name, sequence and parent category of mobikul categories and " + message
        return self.show_msg_wizard(message)

    sync_type = fields.Selection([
        ('name', 'Only Name'),
        ('name_parent', 'Name and Parent Category'),
        ('name_parent_seq', 'Name, Parent Category and Sequence'), ], 'Sync Type', default='name_parent_seq',
        help="Sync mobikul category on the basis of Selection")
