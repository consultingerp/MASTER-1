import time
from requests import request
import requests
from odoo import models, fields, api, _
import logging
import simplejson as json
from odoo.exceptions import ValidationError
from requests.auth import HTTPBasicAuth
import binascii
import base64
import requests

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("sendcloud", "Sendcloud")])

    sendcloud_service_id = fields.Many2one('sendcloud.shipping.services',string="Sendcloud Service")

    @api.multi
    def sendcloud_rate_shipment(self, order):
        return {'success': True, 'price': 0.0,
                'error_message': False, 'warning_message': False}

    @api.multi
    def sendcloud_order_request_data(self,picking):
        receipient_address = picking.partner_id
        picking_company_id = picking.picking_type_id.warehouse_id.partner_id
        sendcloud_request_data={
          "parcel": {
            "name":  "%s" % (receipient_address.name),
            "company_name": "%s" % (receipient_address.name),
            "address":"%s" % (receipient_address.street or ""),
            "house_number": "%s"%(receipient_address.street2),
            "city": "%s"% (receipient_address.city or ""),
            "postal_code": "%s" % (receipient_address.zip or ""),
            "telephone": "%s" % (receipient_address.phone or ""),
            "request_label": True,
            "email": "%s" % (receipient_address.email or ""),
            "data": [],
            "country": "%s" % (receipient_address.country_id and receipient_address.country_id.code or ""),
            "shipment": {
              "id": self.sendcloud_service_id and self.sendcloud_service_id.sendcloud_service_id or ""
            },
            "weight": "%s"%(picking.shipping_weight),
            "order_number": "%s"%(picking.id),
            "insured_value": 0.0
          }
        }
        return sendcloud_request_data

    @api.multi
    def sendcloud_api_calling_function(self, api_url, request_data):
        data = "%s:%s" % (self.company_id and self.company_id.sendcloud_api_key, self.company_id and self.company_id.sendcloud_api_secret)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization':authrization_data}
        data = json.dumps(request_data)
        try:
            _logger.info("Easyship URL : %s \n Sendcloud Request Data : %s" % (api_url, data))
            response_body = request(method='POST', url=api_url, data=data, headers=headers)
        except Exception as e:
            raise ValidationError(e)
        return response_body

    @api.model
    def sendcloud_send_shipping(self, pickings):
        for picking in pickings:
            try:
                request_data = self.sendcloud_order_request_data(picking)
                api_url = "%s/parcels"%(self.company_id and self.company_id.sendcloud_api_url)
                response_data = self.sendcloud_api_calling_function(api_url, request_data)
            except Exception as e:
                raise ValidationError(_("\n Response Data : %s") % (e))
            if response_data.status_code in [200, 201]:
                response_data = response_data.json()
                _logger.info("Easyship Response Data : %s" % (response_data))
                if response_data.get("parcel") and response_data.get("parcel").get("id"):
                    picking.sendcloud_parcel_id = response_data.get("parcel").get("id")
                    picking.sendcloud_label_url =response_data.get("parcel").get("label")
                    picking.sendcloud_tracking_page_url =response_data.get("parcel").get("tracking_url")
                    picking.sendcloud_shipment_uuid =response_data.get("parcel").get("shipment_uuid")
                    picking.sendcloud_external_order_id=response_data.get("parcel").get("external_order_id")
                    picking.sendcloud_external_shipment_id= response_data.get("parcel").get("external_shipment_id")
                    shipping_data = {
                        'exact_price': float(picking.sale_id and picking.sale_id.delivery_price or 0.0),
                        'tracking_number': response_data.get("parcel").get("tracking_number")}
                    shipping_data = [shipping_data]
                    return shipping_data
                else:
                    raise ValidationError(_("Response Data : %s ") % (response_data))
            else:
                raise ValidationError(
                    _("Response Code : %s Response Data : %s ") % (response_data.status_code, response_data.text))