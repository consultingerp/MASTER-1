# -*- encoding: utf-8 -*-
##############################################################################
#    Module Writen to odoo
#
#    Copyright (C) 2016 - Today Icap Inc. <http://www.icapsystems.com>
#
#    @author Turkesh Patel
##############################################################################

{
    "name": "Google Merchant Center Integration", 
    "version": "1.0.2", 
    "author": "Icap Inc.", 
    "category": "Website", 
    "summary": """This module adds funtionality to syncronize product details on your Google merchant center account""",
    "description": """
 Google Merchant Center Integration
===================================

This module adds funtionality to syncronize product details on your Google merchant center account.
""", 
    "website": "http://www.icapsystems.com", 
    "depends": [
        "product"
    ], 
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        "views/product_view.xml",
        "views/template.xml",
        "views/res_config_view.xml",
        "data/product_data.xml"
    ],
    'images': [
        'static/description/integration.png',
    ],
    "installable": True, 
    "price": 150,
    "currency": "USD",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
