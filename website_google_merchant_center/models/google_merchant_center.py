# -*- coding: utf-8 -*-

import time
import werkzeug.urls
import json
import httplib2
import json as simplejson
from oauth2client import client
from googleapiclient.discovery import build
from googleapiclient import errors
import tempfile

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

FILE_DATA = """{
  "installed": {
    "client_id": "%s",
    "client_secret": "%s",
    "redirect_uris": [],
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token"
  }
}"""

scriptFile = tempfile.NamedTemporaryFile(delete=True)
#Get uniqe id for product
unique_id_increment = 0

def get_unique_id():
    """Generates a unique ID.

    The ID is based on the current UNIX timestamp and a runtime increment.

    Returns:
      A unique string.
    """
    global unique_id_increment
    if unique_id_increment is None:
        unique_id_increment = 0
    unique_id_increment += 1
    return "%d%d" % (int(time.time()), unique_id_increment)

class GoogleMerchantCenterService(models.Model):
    _name = 'google.merchant.center.service'


    @api.multi
    def gmc_flow(self):
        web_base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        ir_config = self.env["ir.config_parameter"]
        fp = open(scriptFile.name, 'w')
        fp.seek(0)
        fp.truncate()
        fp = open(scriptFile.name, 'w')
        fp.write(FILE_DATA % (ir_config.sudo().get_param('google_content_client_id'), 
                              ir_config.sudo().get_param('google_content_client_secret')))
        fp.seek(0)
        flow = client.flow_from_clientsecrets(
              scriptFile.name,
              scope = 'https://www.googleapis.com/auth/content',
              redirect_uri = web_base_url + '/google_content/authentication',)
        auth_code = ir_config.get_param("google_content_tocken_id")

        try:
            credentials = flow.step2_exchange(auth_code)
        except:
            raise UserError(_("Your authorization code is already used. Please regenerate again."))
        http_auth = credentials.authorize(httplib2.Http())
        service = build('content', 'v2', http=http_auth)
        return service

    @api.multi
    def sync_product_with_gmc(self, products):
        """ Update products on Google merchant center
            Param: Products: browse list of records for product.product
        """
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        currency = self.env.user.company_id.currency_id.name

        service = self.gmc_flow()

        count = 1
        for product in products:
            if product.google_mcid:
                offerId = product.google_mcid
                product.write({'google_sync_date': fields.Date.today()})
            else:
                offerId = 'CM%s' % get_unique_id()
                product.write({'google_mcid': offerId, 'google_sync_date': fields.Date.today()})
            #Display ads id
            if product.google_display_ads_id:
                displayAdsId = product.google_display_ads_id
            else:
                displayAdsId = 'ADS%s' % get_unique_id()
                product.write({'google_display_ads_id': displayAdsId})
            product_data = {
                'offerId': offerId,
                'displayAdsId': displayAdsId,
                'title': product.name,
                'description': product.description_sale,
                #Use product template url as variants are not shown sepratly.
                'link': product.google_merchant_center_id.website + "/shop/product/%s" % (product.product_tmpl_id.id,),
                'imageLink': product.google_merchant_center_id.website + '/web/image/%s/%s/%s/image.jpg' % ('product.template', product.product_tmpl_id.id, 'image'),
                #Note: Instead of passing website url passsed backend URl because Store not accept image without type
                'contentLanguage': product.google_content_language,
                'targetCountry': product.google_target_country,
                'channel': product.google_channel,
                'availability': product.google_availability,
                'condition': product.google_condition,
                'googleProductCategory': " > ".join(reversed(get_names(product.google_product_category_id))),
                'productType': " > ".join(reversed(get_names(product.categ_id))),
                'brand': product.google_product_brand_id and product.google_product_brand_id.name or '',
                'price': {
                    'value': product.list_price,
                    'currency': currency},
                'shipping': [{
                    'country': product.google_target_country,
                    'service': product.google_shipping,
                    'price': {'value': product.google_shipping_amount,
                              'currency': currency}
                }],
                'taxes': [
                {
                    'rate': product.google_tax_rate,
                    'country': product.google_target_country,
                }],
                'shippingWeight': {
                   'value': product.weight * 1000, 
                   'unit': 'grams'
                },
            }

            #Check if identifierExists than only add mpn
            if product.google_identifier_exists:
                product_data.update({'mpn': product.default_code})
                if not product.google_barcode_as_gtin and product.google_gtin:
                    product_data.update({'gtin': product.google_gtin})
                elif product.google_barcode_as_gtin and product.barcode:
                    product_data.update({'gtin': product.barcode})
            else:
                product_data.update({'identifierExists': 'no'})

            #add some optional attributes
            if product.google_gender:
                product_data.update({'gender': product.google_gender})
            if product.google_age_group:
                product_data.update({'ageGroup': product.google_age_group})
            if product.google_product_size_id:
                product_data.update({'sizes': [product.google_product_size_id and product.google_product_size_id.name or '']})
            if product.google_product_color_id:
                product_data.update({'color': product.google_product_color_id and product.google_product_color_id.name or '',})
            if product.google_expiration_date:
                #pass date in perticular formate
                expiration_date = product.google_expiration_date.strftime('%Y-%m-%d')
                product_data.update({'expirationDate': expiration_date})

            #Optionla Attributes for Remarketing
            if product.google_display_ads_similar_ids:
                product_data.update({'displayAdsSimilarIds': [prod.google_display_ads_id for prod in product.google_display_ads_similar_ids]})
            if product.google_display_ads_title:
                product_data.update({'displayAdsTitle': product.google_display_ads_title})
            if product.google_display_ads_link:
                product_data.update({'displayAdsLink': product.google_display_ads_link})
            if product.google_display_ads_value:
                product_data.update({'displayAdsValue': product.google_display_ads_value})
            if product.google_excluded_destination:
                product_data.update({'destinations': {
                   'destinationName': 'DisplayAds', 
                   'intention': 'excluded'}
                })

            # Add product.
            request = service.products().insert(merchantId=product.google_merchant_center_id.name, body=product_data)

            try:
                result = request.execute()
                _logger.info('Count: %s------- Product: %s', count, product)
                count += 1
                self.env.cr.commit()
            except errors.HttpError as e:
                error = simplejson.loads(e.content.decode('utf-8'))
                raise UserError(_("%s when syncronizing %s.") % (error['error'].get('message'),product.name))

    @api.multi
    def sync_products_with_gmc(self) :
        """Sync New products which is still not synced on center"""
        products = self.env['product.product'].search([('sync_with_mc','=',True), ('website_published','=',True), ('google_product_brand_id','!=',False), ('google_merchant_center_id','!=',False),('google_mcid','=',False)])
        _logger.info('Total products to be synced------ %s', len(products))
        self.sync_product_with_gmc(products)

    @api.multi
    def re_sync_products_with_gmc(self) :
        """Re Sync all products"""
        products = self.env['product.product'].search([('sync_with_mc','=',True), ('google_mcid','!=',False)], order='google_sync_date asc')
        _logger.info('Total products to be synced------ %s', len(products))
        self.sync_product_with_gmc(products)

    @api.multi
    def delete_product_from_gmc(self, products):
        """ Delete products on Google merchant center
            Param: Products: browse list of records for product.product
        """
        service = self.gmc_flow()
        for product in products:
            if product.google_mcid:
                product_id = product.google_channel + ':' + product.google_content_language + ':' + product.google_target_country+ ':' + product.google_mcid
                request = service.products().delete(merchantId=product.google_merchant_center_id.name, productId=product_id)
                _logger.info('Product-------  %s',product)
                try:
                    result = request.execute()
                    product.google_mcid = ''
                    self.env.cr.commit()
                except errors.HttpError as e:
                    error = simplejson.loads(e.content.decode('utf-8'))
                    raise UserError(_("%s. when deleting %s") % (error['error'].get('message'), product.name))

    @api.multi
    def delete_products_from_gmc(self) :
        """Delete all products"""
        products = self.env['product.product'].search([('sync_with_mc','=',True), ('google_mcid','!=',False)])
        self.delete_product_from_gmc(products)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: