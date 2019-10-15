from odoo import models, fields

class Sendcloudshippingservices(models.Model):
    _name = "sendcloud.shipping.services"
    _rec_name = "sendcloud_service_name"

    sendcloud_service_name = fields.Char(string="Sendcloud Service Name", help="Sendcloud Service Name, It's getting from API response.")
    sendcloud_carrier_name = fields.Char(string="Sendcloud Carrier Name", help="Sendcloud Carrier Name, It's getting from API response.")
    sendcloud_service_id = fields.Char(string="Sendcloud Service ID", help="Sendcloud Service ID.")
    min_weight = fields.Float(string="Min Weight", help="")
    max_weight = fields.Float(string="Max Weight", help="")