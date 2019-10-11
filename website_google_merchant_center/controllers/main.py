# -*- encoding: utf-8 -*-

import json
import urllib
import odoo
from odoo import http
from odoo.http import request
from werkzeug.exceptions import BadRequest
import werkzeug.utils

class google_content_auth(http.Controller):

    @http.route('/google_content/authentication', type='http', auth="none")
    def oauth2callback_content(self, **kw):
        """ This route/function is called by Google when user Accept/Refuse the consent of Google """
        icp = request.env['ir.config_parameter'].sudo()
        if kw and kw['code']:
            icp.set_param('google_content_tocken_id', kw['code'])
            return request.render("website_google_merchant_center.google_success")
        else:
            return request.render("website_google_merchant_center.google_fail")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: