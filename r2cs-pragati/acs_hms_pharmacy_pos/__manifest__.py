# -*- coding: utf-8 -*-
#╔══════════════════════════════════════════════════════════════════════╗
#║                                                                      ║
#║                  ╔═══╦╗       ╔╗  ╔╗     ╔═══╦═══╗                   ║
#║                  ║╔═╗║║       ║║ ╔╝╚╗    ║╔═╗║╔═╗║                   ║
#║                  ║║ ║║║╔╗╔╦╦══╣╚═╬╗╔╬╗ ╔╗║║ ╚╣╚══╗                   ║
#║                  ║╚═╝║║║╚╝╠╣╔╗║╔╗║║║║║ ║║║║ ╔╬══╗║                   ║
#║                  ║╔═╗║╚╣║║║║╚╝║║║║║╚╣╚═╝║║╚═╝║╚═╝║                   ║
#║                  ╚╝ ╚╩═╩╩╩╩╩═╗╠╝╚╝╚═╩═╗╔╝╚═══╩═══╝                   ║
#║                            ╔═╝║     ╔═╝║                             ║
#║                            ╚══╝     ╚══╝                             ║
#║                  SOFTWARE DEVELOPED AND SUPPORTED BY                 ║
#║                ALMIGHTY CONSULTING SOLUTIONS PVT. LTD.               ║
#║                      COPYRIGHT (C) 2016 - TODAY                      ║
#║                      https://www.almightycs.com                      ║
#║                                                                      ║
#╚══════════════════════════════════════════════════════════════════════╝
{
    'name': 'Hospital Pharmacy Management - Point of Sale',
    'version': '1.0.2',
    'summary': 'Link module between Point of Sale and Hospital Pharmacy Management system',
    'description': """ Link module between Point of Sale and Hospital Pharmacy Management system. Posnt of prescription integration with Hospital management system.
""",
    'category': 'Industry',
    'author': 'Almighty Consulting Solutions Pvt. Ltd.',
    'website': 'https://www.almightycs.com',
    'license': 'OPL-1',
    'depends': ['acs_hms_pharmacy', 'point_of_sale'],
    'data': [
        'data/acs_hms_pharmacy_pos_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/prescription_order_views.xml',
        'views/pos_order_views.xml',
        'views/stock_template.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'acs_hms_pharmacy_pos/static/src/css/acs_hms_pharmacy_pos.css',
            'acs_hms_pharmacy_pos/static/src/js/models.js',
            'acs_hms_pharmacy_pos/static/src/js/SetPrescriptionOrderButton.js',
            'acs_hms_pharmacy_pos/static/src/js/OrderManagementScreen/MobilePrescriptionOrderManagementScreen.js',
            'acs_hms_pharmacy_pos/static/src/js/OrderManagementScreen/PrescriptionOrderFetcher.js',
            'acs_hms_pharmacy_pos/static/src/js/OrderManagementScreen/PrescriptionOrderList.js',
            'acs_hms_pharmacy_pos/static/src/js/OrderManagementScreen/PrescriptionOrderManagementControlPanel.js',
            'acs_hms_pharmacy_pos/static/src/js/OrderManagementScreen/PrescriptionOrderManagementScreen.js',
            'acs_hms_pharmacy_pos/static/src/js/OrderManagementScreen/PrescriptionOrderRow.js',
            'acs_hms_pharmacy_pos/static/src/xml/**/*',
        ],
    },
    'images': [
        'static/description/hms_pharmacy_pos_almightycs_odoo_cover.jpg',
    ],
    'sequence': 2,
    'price': 260,
    'currency': 'USD',
    'installable': True,
    'auto_install': False,

}
