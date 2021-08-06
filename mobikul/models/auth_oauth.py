# ##########################################################################
# #
# #    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# #
# ##########################################################################
from odoo import api, fields, models
# from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)

class InheritAuthOAuthProvider(models.Model):

    _inherit = 'auth.oauth.provider'

    mobikul_oauth_ref_code = fields.Char('Mobikul Reference Code',copy=False,
        help='Unique Code in order to integrate Social Login with Mobikul App')
