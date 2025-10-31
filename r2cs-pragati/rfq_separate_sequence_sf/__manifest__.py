# -*- coding: utf-8 -*-
##############################################################################
#
#    Shinefy Technologies Pvt. Ltd.
#    Copyright (C) 2022 Shinefy Technologies.
#    Author: Shinefy Technologies
#    
#    For Module Support : shinefytech@gmail.com  or Skype : shinefytech@gmail.com
#
##############################################################################

{
    "name": "RFQ Separate Sequence",
    "summary": "Add a separate sequence to your RFQs.",
    "version": "16.0.0.1",
    'author': 'ShinefyTech',
    'maintainer': 'ShinefyTech',
    "category": "Purchases",
    "depends": [
        "purchase", 'account'
    ],
    "data": [
        'data/ir_sequence_data.xml',
        'views/purchase_seq_view.xml',
    ],
    'license': 'LGPL-3',
    'live_test_url' :'https://youtu.be/Kma6XbWKmcY',
    'installable': True,
    'auto_install': False,
    'images':['static/description/Banner.gif'],
    'price': '8',
    'currency': "Eur",
}
