# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    is_mobikul_available = fields.Boolean(
        'Visible in Mobikul', copy=False,
        help="Make this payment acquirer available on App")
    mobikul_reference_code = fields.Char(
        'Mobikul Reference Code', copy=False,
        help="Unique Code in order to integrate it with Mobikul App.")
    mobikul_pre_msg = fields.Text('Message to Display', copy=False,
                                  translate=True, help="this field is depricated from mobikul")
    mobikul_extra_key = fields.Char('Extra Keys', copy=False)
