# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
import uuid
import re
import hashlib
from functools import wraps
from ast import literal_eval
from base64 import b64decode
import json
from urllib.parse import urlparse
from odoo.tools import float_round
import xml.etree.ElementTree as ET
import werkzeug
from datetime import datetime
import requests
from odoo.http import request, Controller, route
from odoo import _
from odoo.http import request
from odoo.addons.mobikul.tool.help import _displayWithCurrency, _get_image_url, remove_htmltags
import logging
_logger = logging.getLogger(__name__)


class xml(object):

    @staticmethod
    def _encode_content(data):
        # .replace('&', '&amp;')
        return data.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    @classmethod
    def dumps(cls, apiName, obj):
        _logger.warning("%r : %r" % (apiName, obj))
        if isinstance(obj, dict):
            return "".join("<%s>%s</%s>" % (key, cls.dumps(apiName, obj[key]), key) for key in obj)
        elif isinstance(obj, list):
            return "".join("<%s>%s</%s>" % ("I%s" % index, cls.dumps(apiName, element), "I%s" % index) for index, element in enumerate(obj))
        else:
            return "%s" % (xml._encode_content(obj.__str__()))

    @staticmethod
    def loads(string):
        def _node_to_dict(node):
            if node.text:
                return node.text
            else:
                return {child.tag: _node_to_dict(child) for child in node}
        root = ET.fromstring(string)
        return {root.tag: _node_to_dict(root)}


class WebServices(Controller):

    def __decorateMe(func):
        @wraps(func)
        def wrapped(inst, *args, **kwargs):
            inst._mData = request.httprequest.data and json.loads(
                request.httprequest.data.decode('utf-8')) or {}
            inst._mAuth = request.httprequest.authorization and (request.httprequest.authorization.get(
                'password') or request.httprequest.authorization.get("username")) or None
            inst.base_url = request.httprequest.host_url
            inst._lcred = {}
            inst._sLogin = False
            inst.auth = True
            inst._mLang = request.httprequest.headers.get("lang") or None
            inst._mPricelist = request.httprequest.headers.get("pricelist") or None
            if request.httprequest.headers.get("Login"):
                try:
                    inst._lcred = literal_eval(
                        b64decode(request.httprequest.headers["Login"]).decode('utf-8'))
                except:
                    inst._lcred = {"login": None, "pwd": None}
            elif request.httprequest.headers.get("SocialLogin"):
                inst._sLogin = True
                try:
                    inst._lcred = literal_eval(
                        b64decode(request.httprequest.headers["SocialLogin"]).decode('utf-8'))
                except:
                    inst._lcred = {"authProvider": 1, "authUserId": 1234567890}
            else:
                inst.auth = False
            return func(inst, *args, **kwargs)
        return wrapped

    def _available_api(self):
        API = {
            'homepage': {
                'description': 'HomePage API',
                'uri': '/mobikul/homepage'
            },
            'sliderProducts': {
                'description': 'Product(s) of given Product Slider Record',
                'uri': '/mobikul/sliderProducts/&lt;int:product_slider_id&gt;',
            },
            'login': {
                'description': 'Customer Login',
                'uri': '/mobikul/customer/login',
            },
            'signUp': {
                'description': 'Customer signUp',
                'uri': '/mobikul/customer/signUp',
            },
            'resetPassword': {
                'description': 'Customer Reset Password',
                'uri': '/mobikul/customer/resetPassword',
            },
            'splashPageData': {
                'description': 'Default data to saved at app end.',
                'uri': '/mobikul/splashPageData',
            },
        }
        return API

    def _wrap2xml(self, apiName, data):
        resp_xml = "<?xml version='1.0' encoding='UTF-8'?>"
        resp_xml += '<odoo xmlns:xlink="http://www.w3.org/1999/xlink">'
        resp_xml += "<%s>" % apiName
        resp_xml += xml.dumps(apiName, data)
        resp_xml += "</%s>" % apiName
        resp_xml += '</odoo>'
        return resp_xml

    def _response(self, apiName, response, ctype='json'):
        if response.get("context"):
            response.pop("context")
        if 'local' in response:
            response.pop("local")
        if ctype == 'json':
            mime = 'application/json; charset=utf-8'
            body = json.dumps(response)
        else:
            mime = 'text/xml'
            body = self._wrap2xml(apiName, response)
        headers = [
            ('Content-Type', mime),
            ('Content-Length', len(body))
        ]
        return werkzeug.wrappers.Response(body, headers=headers)

    @__decorateMe
    def _authenticate(self, auth, **kwargs):
        if 'api_key' in kwargs:
            api_key = kwargs.get('api_key')
        elif request.httprequest.authorization:
            api_key = request.httprequest.authorization.get(
                'password') or request.httprequest.authorization.get("username")
        else:
            api_key = False
        Mobikul = request.env['mobikul'].sudo().search([], limit=1)
        payload = {"lang": self._mLang, "base_url": self.base_url,
                   "pricelist": self._mPricelist, "mobikul_obj": Mobikul}
        response = Mobikul._validate(api_key, payload)
        if not response.get('success'):
            return response
        context = response.get("context")
        request.context = dict(context)
        # Inorder to get the context updated mobikul object
        Mobikul = context['mobikul_obj']
        if auth:
            result = Mobikul.authenticate(self._lcred, kwargs.get(
                'detailed', False), self._sLogin, context=context)
            response.update(result)
        return response

    @route('/mobikul/', csrf=False, type='http', auth="none")
    def index(self, **kwargs):
        """ HTTP METHOD : request.httprequest.method
        """
        response = self._authenticate(False, **kwargs)
        if response.get('success'):
            data = self._available_api()
            return self._response('mobikulApi', data, 'xml')
        else:
            headers = [
                ('WWW-Authenticate', 'Basic realm="Welcome to Odoo Webservice, please enter the authentication key as the login. No password required."')]
            return werkzeug.wrappers.Response('401 Unauthorized %r' % request.httprequest.authorization, status=401, headers=headers)

    def _languageData(self, mobikul):
        temp = {
            'defaultLanguage': (mobikul.default_lang.code, mobikul.default_lang.name),
            'allLanguages': [(id.code, id.name) for id in mobikul.language_ids],
            'TermsAndConditions': mobikul.enable_term_and_condition
        }
        return temp

    def mobikul_display_address(self, address, name=""):
        return (name or "") + (name and "\n" or "") + address

    def _checkFullAddress(self, Partner):
        mandatory_fields = ["street", "city", "state_id", "zip", "country_id"]
        val = [True if mf == "state_id" and not Partner.country_id.state_ids else getattr(
            Partner, mf) for mf in mandatory_fields]
        return all(val)

    def _getAquirerCredentials(self, order_name, Acquirer, response,txn):
        if Acquirer.mobikul_reference_code == 'COD':
            return {'status': True, 'code': 'COD', 'auth': False}
        elif Acquirer.mobikul_reference_code == 'STRIPE_W':
            Transaction = request.env['payment.transaction'].sudo()
            return {'status': True, 'paymentReference': txn.reference, 'code': 'STRIPE', 'auth': True, 'secret_key': Acquirer.stripe_checkout_client_secret_key, 'publishable_key': Acquirer.stripe_checkout_publishable_key}
        elif Acquirer.mobikul_reference_code == 'STRIPE_E':
            Transaction = request.env['payment.transaction'].sudo()
            return {'status': True, 'paymentReference': txn.reference, 'code': 'STRIPE', 'auth': True, 'secret_key': Acquirer.stripe_secret_key, 'publishable_key': Acquirer.stripe_publishable_key}
        else:
            return {'status': False, 'message': _('Payment Mode not Available.')}

    def _getAquirerState(self, Acquirer, status=False):
        if Acquirer.mobikul_reference_code in ['COD']:
            return "pending"
        elif Acquirer.mobikul_reference_code in ['STRIPE_W', 'STRIPE_E']:
            return STATUS_MAPPING['STRIPE'].get(status, 'pending')
        else:
            return "pending"

    def _orderReview(self, user, response, Acquirer):
        last_order = user.partner_id.last_mobikul_so_id.sudo()
        if last_order and len(last_order.order_line):
            local = response.get('context', {})
            addons = response.get('addons', {})
            if addons.get('website_sale_stock'):
                self._cart_update(last_order, response)
            if self._mData.get('shippingAddressId'):
                last_order.partner_shipping_id = int(self._mData.get('shippingAddressId'))
            if addons.get('website_sale_delivery') and self._mData.get("shippingId"):
                last_order.sudo()._check_carrier_quotation(force_carrier_id=int(self._mData.get("shippingId")))
            result = {
                "name": last_order.name,
                "billingAddress": self.mobikul_display_address(last_order.partner_invoice_id._display_address(), last_order.partner_invoice_id.name),
                "shippingAddress": self.mobikul_display_address(last_order.partner_shipping_id._display_address(), last_order.partner_shipping_id.name),
                "paymentAcquirer": Acquirer.name,
                "subtotal": {"title": _("Subtotal"),
                             "value": _displayWithCurrency(local.get('lang_obj'), last_order.amount_untaxed, local.get('currencySymbol'), local.get('currencyPosition')),
                             },
                "tax": {"title": _("Taxes"),
                        "value": _displayWithCurrency(local.get('lang_obj'), last_order.amount_tax, local.get('currencySymbol'), local.get('currencyPosition')),
                        },
                "grandtotal": {"title": _("Total"),
                               "value": _displayWithCurrency(local.get('lang_obj'), last_order.amount_total, local.get('currencySymbol'), local.get('currencyPosition')),
                               },
                "amount": last_order.amount_total,
                "currency": last_order.pricelist_id.currency_id.name or "",
                "items": [],
            }

            for item in last_order.order_line:
                if addons.get('website_sale_delivery') and item.is_delivery:
                    shippingMethod = {
                        "tax": [tax.name for tax in item.tax_id],
                        "name": item.order_id.carrier_id.name,
                        "description": item.order_id.carrier_id.website_description or "",
                        "shippingId": item.order_id.carrier_id.id,
                        "total": _displayWithCurrency(local.get('lang_obj'), item.price_subtotal,
                                                      local.get('currencySymbol'), local.get('currencyPosition')),
                    }
                    result.update({"delivery": shippingMethod})
                else:
                    product_id = item.product_id
                    comb_info = product_id.product_tmpl_id.with_context(local)._get_combination_info(combination=False, product_id=product_id.id,add_qty=1, pricelist=local.get("pricelist"), parent_combination=False, only_template=False)
                    temp = {
                        "lineId": item.id,
                        "templateId": product_id and product_id.product_tmpl_id.id or "",
                        "name": product_id and product_id.display_name or item.name,
                        "thumbNail": _get_image_url(self.base_url, 'product.product', product_id and product_id.id or "", 'image_512', product_id and product_id.write_date),
                        "priceReduce": comb_info['has_discounted_price'] and _displayWithCurrency(local.get('lang_obj'), comb_info['price'], local.get('currencySymbol'), local.get('currencyPosition')) or "",
                        "priceUnit": _displayWithCurrency(local.get('lang_obj'), comb_info['has_discounted_price'] and comb_info['list_price'] or comb_info['price'], local.get('currencySymbol'), local.get('currencyPosition')),
                        "qty": item.product_uom_qty,
                        "total": _displayWithCurrency(local.get('lang_obj'), item.price_subtotal, local.get('currencySymbol'), local.get('currencyPosition')),
                        "discount": item.discount and "(%d%% OFF)" % item.discount or "",
                    }
                    result['items'].append(temp)
            vals = {
                'acquirer_id': Acquirer.id,
                'return_url': ''
            }
            txn = last_order._create_payment_transaction(vals)
            result['paymentData'] = self._getAquirerCredentials(last_order.name, Acquirer, response,txn)
            result['paymentData'].update({'customer_email': last_order.partner_id.email})
            result['transaction_id'] = txn.id
        else:
            result = {'success': False, 'message': _('Add some products in order to proceed.')}
        return result

    def _tokenUpdate(self, customer_id=False):
        FcmRegister = request.env['fcm.registered.devices'].sudo()
        already_registered = FcmRegister.search(
            [('device_id', '=', self._mData.get("fcmDeviceId"))])
        if already_registered:
            already_registered.write(
                {'token': self._mData.get("fcmToken"), 'customer_id': customer_id})
        else:
            FcmRegister.create({
                'token': self._mData.get("fcmToken", ""),
                'device_id': self._mData.get("fcmDeviceId", ""),
                'description': "%r" % self._mData,
                'customer_id': customer_id,
            })
        return True

    def _pushNotification(self, token, condition='signup', customer_id=False):
        notifications = request.env['mobikul.push.notification.template'].sudo().search([
            ('condition', '=', condition)])
        for n in notifications:
            n._send({'to': token}, customer_id)
        return True

    def add2Ws(self, context, product_id):
        Partner = context.get("partner")
        wishlistObj = Partner.env['product.wishlist'].sudo()
        p = Partner.env['product.product'].browse(int(product_id)).sudo()
        partner_id = Partner.id
        try:
            wishlist = wishlistObj.search([("partner_id","=",partner_id),("product_id","=",p.id)])
            if wishlist:
                result = {'success':False,'message':"Item already in Wishlist"}
            else:
                wishlistObj._add_to_wishlist(
                    context.get("pricelist").id,
                    context.get("currency_id"),
                    context.get("website_id"),
                    p._get_combination_info_variant()['price'],
                    p.id,
                    partner_id
                )
                result = {'success': True,
                          'message': _("Item moved to Wishlist")
                          }
        except Exception as e:
            result = {
                'success': False,
                'message': _('Please try again later'),
                'detail': 'Error Details: %r' % e.args[0],
            }
        return result

    def _sendPaymentAcknowledge(self, last_order, Partner, txn, context):
        result = {}
        if txn.state not in ['error','cancel']:
            context.update({"send_email": True})
            Partner.last_mobikul_so_id = False
            self._pushNotification(self._mData.get("fcmToken", ""), condition='orderplaced',
                                   customer_id=Partner.id)
            result.update({
                'url': "/mobikul/my/order/%s" % last_order.id,
                'name': last_order.name,
                'cartCount': 0,
                'success': True,
                'message': _('Your order') + ' %s ' % (last_order.name) + _('has been placed successfully.'),
                'transaction_id': txn.id,
            })
            
            if txn.state in ['pending', 'draft']:
                last_order.write({'state': 'sent'})
                result.update({'txn_msg': remove_htmltags(txn.acquirer_id.pending_msg)})

            elif txn.state == 'done':
                last_order.with_context(context).action_confirm()
                txn._post_process_after_done()
                last_order._send_order_confirmation_mail()
                result.update({'txn_msg': remove_htmltags(txn.acquirer_id.done_msg)})
            else:
                result.update({'txn_msg': 'No transaction state found..'})
        else:
            result.update({
                    'transaction_id': txn.id,
                    'success': False,
                })
            if txn.state == 'error':
                result.update({
                    'message': "ERROR",
                    'txn_msg': txn.state_message or "ERROR"
                })
            else:
                result.update({
                    'txn_msg': remove_htmltags(txn.acquirer_id.cancel_msg),
                    "message":"CANCEL"
                })
        return result

    def create_stripe_charge(self, Partner,txn, token):
        vals = {}
        if token:
            INT_CURRENCIES = [u'BIF', u'XAF', u'XPF', u'CLP', u'KMF', u'DJF', u'GNF', u'JPY', u'MGA', u'PYG', u'RWF', u'KRW',u'VUV', u'VND', u'XOF']
            last_order = Partner.last_mobikul_so_id
            Address = last_order.partner_invoice_id
            payload = {
                'amount': int(txn.amount if txn.currency_id.name in INT_CURRENCIES else float_round(txn.amount * 100, 2)),
                'currency': txn.currency_id.name.lower(),
                'source': token,
            }
            api_key = txn.acquirer_id.stripe_secret_key
            url = 'https://api.stripe.com/v1/charges'
            resp = requests.post(url, data=payload, auth=(api_key, api_key))
            if 'error' in resp.json():
                stripe_error = resp.json().get('error', {}).get('message', '')
                error_msg = " " + (_("Stripe gave us the following info about the problem: '%s'") % stripe_error)
                self._mData['paymentStatus'] = 'failed'
                vals['state_message'] = error_msg
            else:
                resp = resp.json()
                self._mData['paymentStatus'] = resp.get('status',False)
                self._mData['acquirer_reference'] = resp.get('id','')
                vals['date'] = datetime.now()
        return vals

    def placeOrder(self, context):
        result = {}
        tx_values = {}
        Partner = context.get("partner").sudo()
        if Partner:
            last_order = Partner.last_mobikul_so_id
            if last_order:
                if int(self._mData.get('transaction_id')) in last_order.transaction_ids.mapped('id'):
                    txn = request.env['payment.transaction'].sudo().browse(
                        [int(self._mData.get('transaction_id'))])
                    tx_values = {
                        'type': 'form',
                        "state_message": 'MOBIKUL',
                    }
                    if txn.acquirer_id.mobikul_reference_code == "STRIPE_E":
                        if self._mData.get('token'):
                            tx_values.update(self.create_stripe_charge(Partner,txn, self._mData['token']))
                        # elif condition is used for the android aap previous compatibilty
                        elif set(self._mData.keys()) - {'paymentStatus','transaction_id'}:
                            return {'success': False, 'message': _('Required STPToken value is missing')}

                    tx_values.update({
                        'acquirer_reference': self._mData.get('acquirer_reference') or "acquirer_reference key is absent in payload data.",
                        'state': self._getAquirerState(txn.acquirer_id, self._mData.get('paymentStatus'))
                    })
                    txn.write(tx_values)
                    result.update(self._sendPaymentAcknowledge(last_order, Partner, txn, context))
                else:
                    result = {'success': False, 'message': _(
                        'Transaction Id not found in order.')}
            else:
                result = {'success': False, 'message': _(
                    'Add some products in order to proceed.')}
        else:
            result = {'success': False, 'message': ('Account not found !!!')}
        return result

    # Product Availability(website_sale_stock) START

    def _cart_update(self, order, response):
        """
        Double check cart quantities before
        placing the order
        """
        context = response.get('context', {})
        values = {}
        if order:
            for line in order.order_line:
                if line.product_id.type == 'product' and line.product_id.inventory_availability in ['always', 'threshold']:
                    cart_qty = sum(order.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                    # The quantity should be computed based on the warehouse of the website, not the
                    # warehouse of the SO.
                    website = context['websiteObj']
                    if cart_qty > line.product_id.with_context(warehouse=website.warehouse_id.id).virtual_available:
                        qty = line.product_id.with_context(warehouse=website.warehouse_id.id).virtual_available - cart_qty
                        new_val = order._cart_update(line.product_id.id, line.id, qty, 0)
                        values.update(new_val)

                        # Make sure line still exists, it may have been deleted in super()_cartupdate because qty can be <= 0
                        if line.exists() and new_val['quantity']:
                            line.warning_stock = _('You ask for %s products but only %s is available') % (cart_qty, new_val['quantity'])
                            values['warning'] = line.warning_stock
                        else:
                            order.warning_stock = _("Some products became unavailable and your cart has been updated. We're sorry for the inconvenience.")
                            values['warning'] = order.warning_stock
        return values

    def _get_cart_qty(self, product, context):
        Partner = context.get('partner')
        cart = Partner and Partner.last_mobikul_so_id
        qty = sum(cart.order_line.filtered(lambda p: p.product_id.id == product.id).mapped('product_uom_qty')) if cart else 0
        return qty

    def get_stock_info(self, comb_info, product, context):
        """
        Utility function to get the stock display message with add to cart button to enbale or disable
        """
        resp = {
        "add_to_cart": True,
        "stock_display_msg":"",
        # "stock_display_msg_type":"success"
        }
        product_type = comb_info['product_type']
        inventory_availability = comb_info['inventory_availability']
        virtual_available_formatted = comb_info['virtual_available_formatted']
        uom_name = comb_info['uom_name']
        available_threshold = comb_info['available_threshold']
        cart_qty = self._get_cart_qty(product, context)
        virtual_available = comb_info['virtual_available'] - cart_qty
        if virtual_available < 0:
            virtual_available = 0
        custom_message = comb_info['custom_message']
        if product_type == 'product' and inventory_availability in ['always', 'threshold']:
            if virtual_available > 0:
                if inventory_availability == 'always':
                    resp['stock_display_msg'] = _("%s %s available")%(virtual_available_formatted, uom_name)
                elif inventory_availability == 'threshold':
                    if virtual_available <= available_threshold:
                        resp['stock_display_msg'] = _("%s %s available")%(virtual_available_formatted, uom_name)
                        # resp['stock_display_msg_type'] = 'warning'
                    elif virtual_available > available_threshold:
                        resp['stock_display_msg'] = _("In stock")
            if cart_qty:
                if resp['stock_display_msg']:
                    resp['stock_display_msg'] += '\n'
                resp['stock_display_msg'] = resp['stock_display_msg'] + _("You already added%s %s %s in your cart.")%(not virtual_available and ' all' or '', cart_qty, uom_name)
                # resp['stock_display_msg_type'] = 'warning'
                if not virtual_available:
                    resp['add_to_cart'] = False
            elif not cart_qty and virtual_available <= 0:
                resp['stock_display_msg'] = resp['stock_display_msg'] + _("\n Temporarily out of stock")
                # resp['stock_display_msg_type'] = 'danger'
                resp['add_to_cart'] = False
        if product_type == 'product' and inventory_availability == 'custom':
            resp['stock_display_msg'] = custom_message
        return resp

    # Product Availability(website_sale_stock) END
