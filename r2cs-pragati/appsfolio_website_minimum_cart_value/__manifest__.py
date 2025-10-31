# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of appsfolio. (Website: www.appsfolio.in).                            #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

{
    'name': 'Website Minimum Cart Value',
    'version': '16.0.0.1',
    'summary': 'Website Minimum Cart Value',
    'description': '''The Odoo Shop application's "Website Minimum Sale Amount" feature enables the 
        establishment of a minimum order requirement within the online store. Both registered website customers and visitors must adhere to these predefined minimum amounts to proceed with their purchases on the Odoo shop platform.''',
    'depends': ['base', 'website_sale'],
    'category': 'Website',
    'author': 'AppsFolio',
    'website': 'www.appsfolio.in',
    'data': [
        'views/res_company.xml',
        'views/res_config_settings.xml',
        'views/template.xml',
    ],
    'price': 8.21,
    'currency': 'EUR',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto-install': False,
    'license': 'OPL-1',
    'assets': {
        'web.assets_frontend': [
            'website_minimum_cart_value/static/src/js/min_cart_value.js',
        ],
    },
}
