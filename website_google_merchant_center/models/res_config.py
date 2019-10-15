# -*- coding: utf-8 -*-

from odoo import fields, models, api
import werkzeug.urls


class ResConfigSettings(models.TransientModel):
    """Adds the fields for options of the Google merchant center."""
    _inherit = 'res.config.settings'


    google_content_client_id = fields.Char(string='Google Client ID')
    google_content_client_secret = fields.Char(string='Google Client Secret')
    google_content_uri = fields.Char(string='Google Content Authorization', readonly=True)
    google_content_authorization_code = fields.Char(string='Google Content Authorization')


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter']

        res['google_content_client_id'] = ir_config.sudo().get_param('google_content_client_id')
        res['google_content_client_secret'] = ir_config.sudo().get_param('google_content_client_secret')
        res['google_content_authorization_code'] = ir_config.sudo().get_param('google_content_tocken_id')

        web_base_url = ir_config.sudo().get_param("web.base.url")
        params = {
            'scope': 'https://www.googleapis.com/auth/content',
            'redirect_uri': web_base_url + '/google_content/authentication',
            'client_id': ir_config.sudo().get_param('google_content_client_id'),
            'response_type': 'code',
            #'approval_prompt': 'force',
            'access_type': 'offline',
            #'grant_type': 'refresh_code',
        }
        uri = 'https://accounts.google.com/o/oauth2/auth?%s' % werkzeug.url_encode(params)
        res['google_content_uri'] = uri

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter']
        params.set_param('google_content_client_id', (self.google_content_client_id or ''))
        params.set_param('google_content_client_secret', (self.google_content_client_secret or ''))

    @api.multi
    def sync_gmc_products(self) :
        self.env['google.merchant.center.service'].sync_products_with_gmc()

    @api.multi
    def re_sync_gmc_products(self) :
        self.env['google.merchant.center.service'].re_sync_products_with_gmc()

    @api.multi
    def delete_products_from_gmc(self) :
        self.env['google.merchant.center.service'].delete_products_from_gmc()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: