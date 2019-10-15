from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError,Warning
import simplejson as json
import base64
from requests import request
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"
    sendcloud_api_key = fields.Char(string="Sendcloud API Key",
                                    help="Available under your Sendcloud Account. Go to Settings, Store and select it.",
                                    copy=False)
    sendcloud_api_secret = fields.Char(string="Sendcloud API Secret",
                                       help="Available under your Sendcloud Account. Go to Settings,  Store and select it.",
                                       copy=False)
    sendcloud_api_url = fields.Char(copy=False, string='Easyship API URL',
                                    help="API URL, Redirect to this URL when calling the API.",
                                    default="https://panel.sendcloud.sc/api/v2")
    use_sendcloud_shipping_provider = fields.Boolean(copy=False, string="Are You Use Sendcloud.?",
                                                     help="If use Sendcloud shipping Integration than value set TRUE.",
                                                     default=False)
    service_message = fields.Char(string="Message",
                                  help="If credentials are correct then by click on get services button, get all services from send cloud to odoo.",
                                  copy=False)


    @api.multi
    def weight_convertion(self, weight_unit, weight):
        pound_for_kg = 2.20462
        ounce_for_kg = 35.274
        if weight_unit in ["LB", "LBS"]:
            return round(weight * pound_for_kg, 3)
        elif weight_unit in ["OZ", "OZS"]:
            return round(weight * ounce_for_kg, 3)
        else:
            return round(weight, 3)

    @api.multi
    def get_shipping_services(self):
        data = "%s:%s" % (self.sendcloud_api_key, self.sendcloud_api_secret)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
        url="%s/shipping_methods"%(self.sendcloud_api_url)
        headers = {"Authorization": "%s" % authrization_data}
        sendcloud_shipping_service_obj = self.env["sendcloud.shipping.services"]
        try:
            response = request(method='GET', url=url, headers=headers)
            if response.status_code != 200:
                error = "Error Code : %s - %s" % (response.status_code, response.reason)
            response = response.json()
            delivery_methods=response.get("shipping_methods")
            if delivery_methods:
                for delivery_method in delivery_methods:
                    if not sendcloud_shipping_service_obj.search([('sendcloud_service_id','=',delivery_method.get("id"))]):
                        sendcloud_shipping_service_obj.create({'sendcloud_service_name':delivery_method.get("name"),
                                                           'sendcloud_carrier_name':delivery_method.get("carrier"),
                                                           'sendcloud_service_id':delivery_method.get("id"),
                                                           'min_weight':delivery_method.get("min_weight"),
                                                           'max_weight':delivery_method.get("max_weight")})
            else:
                raise ValidationError("Not found any shipping services in send cloud!")
        except Exception as e:
            raise ValidationError(e)