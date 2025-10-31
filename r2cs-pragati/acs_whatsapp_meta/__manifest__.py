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
    'name' : 'WhatsApp Meta API Integration (Whatsapp official API) (BETA)',
    'summary': 'Odoo WhatsApp Integration to send Watsapp messages from Odoo using official Meta API',
    'category' : 'Extra-Addons',
    'version': '1.0.3',
    'license': 'OPL-1',
    'depends' : ['acs_whatsapp'],
    'author': 'Almighty Consulting Solutions Pvt. Ltd.',
    'website': 'www.almightycs.com',
    'live_test_url': 'https://www.youtube.com/watch?v=s0t0RkIAlYI',
    'description': """
        Odoo WhatsApp Integration to send Watsapp messages from Odoo. Notification WhatsApp to customer or users, Acs hms Whatsapp official API official whatsapp API.
    """,
    "data": [
        'security/ir.model.access.csv',
        "views/company_view.xml",
        "views/whatsapp_view.xml",
    ],
    'images': [
        'static/description/acs_odoo_whatsapp_almightycs_cover.jpg',
    ],
    'installable': True,
    'application': False,
    'sequence': 2,
    'price': 101,
    'currency': 'USD',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: