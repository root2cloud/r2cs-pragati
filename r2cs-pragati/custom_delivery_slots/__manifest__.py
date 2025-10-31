# -*- coding: utf-8 -*-
{
    'name': 'Custom Delivery Slots',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'license': 'LGPL-3',
    'summary': "Time slot selection for deliveries",
    'description': """This module helps to choose a different delivery date 
    and time for each product in the order line. Multiple deliveries and 
    corresponding delivery slots are created for each line in the sale order,
    based on the chosen date and slot.""",
    'depends': ['sale_management', 'stock', 'account', 'website_sale', 'product'],
    'data': [
        
        'security/ir.model.access.csv',
        'views/delivery_slot.xml',
        'views/sale_order_delivery.xml',
        'views/website_sale_delivery.xml',

    ],
    
    # 'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
