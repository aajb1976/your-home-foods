# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_mobikul_so_id = fields.Many2one('sale.order', string='Last Order from Mobikul App')
    banner_image = fields.Binary('Banner Image', attachment=True)
    token_ids = fields.One2many('fcm.registered.devices', 'customer_id',
                                string='Registered Devices', readonly=True)
    default_shipping_address_id = fields.Many2one('res.partner',string="Default mobikul shipping address")
