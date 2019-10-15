from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    sendcloud_parcel_id = fields.Char(string="Sendcloud Parcel ID", help="it's given in API response", copy=False)
    sendcloud_label_url = fields.Char(string="Sendcloud Label URL", help="sendcloud Label URL", copy=False)
    sendcloud_tracking_page_url = fields.Char(string="Sendcloud Tracking Page URL", help="Sendcloud Tracking Page URL",
                                              copy=False)
    sendcloud_shipment_uuid = fields.Char(string="Sendcloud Shipment UUID", help="", copy=False)
    sendcloud_external_order_id = fields.Char(string="Sendcloud External Order ID", help="", copy=False)
    sendcloud_external_shipment_id = fields.Char(string="Sendcloud External Shipment ID", help="", copy=False)