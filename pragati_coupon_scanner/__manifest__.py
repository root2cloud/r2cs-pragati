# -*- coding: utf-8 -*-
#############################################################################
# Author: Fasil
# Email: fasilwdr@hotmail.com
# WhatsApp: https://wa.me/966538952934
# Facebook: https://www.facebook.com/fasilwdr
# Instagram: https://www.instagram.com/fasilwdr
#############################################################################

{
    'name': 'Pragati Coupon Scanner',
    'version': '1.0.3',
    'sequence': 1,
    'summary': """Define warehouses to user for the operations""",
    'description': """"Define warehouses to user for the operations,
    Allocate warehouse for particular user
    """,
    'category': 'Sale',
    'author': 'Fasil',
    'company': 'Fasil',
    'website': "http://www.facebook.com/fasilwdr",
    'depends': ['base', 'loyalty', 'barcodes', 'sale', 'sale_loyalty'],
    'data': [
        'views/reward_template.xml',
        'views/loyalty_report.xml',
        'views/qrcode_scan.xml',
    ],
'assets': {
        'web.assets_backend': [
            'pragati_coupon_scanner/static/src/**/*.js',
            'pragati_coupon_scanner/static/src/**/*.xml',
            'pragati_coupon_scanner/static/src/**/*.scss',
        ]
    },
    'qweb': [],
    'images': [
        # 'static/description/banner.png'
    ],
    'license': 'OPL-1',
    'currency': 'USD',
    'price': '20',
    'installable': True,
    'auto_install': False,
    'application': True,
}

#############################################################################