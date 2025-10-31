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
    'name' : 'Laboratory WhatsApp Notification',
    'summary': 'Send WhatsApp notification to patient for Laboratory Request and Results.',
    'version': '1.0.2',
    'category': 'Industry',
    'license': 'OPL-1',
    'depends' : ['acs_whatsapp','acs_laboratory'],
    'author': 'Almighty Consulting Solutions Pvt. Ltd.',
    'website': 'www.almightycs.com',
    'live_test_url': 'https://www.youtube.com/watch?v=s0t0RkIAlYI',
    'description': """
        Laboratory WhatsApp Notification Message Notification, Hospital Management system acs hms medical notification
    """,
    "data": [
        "data/data.xml",
        "views/company_view.xml",
        "views/acs_hms_view.xml",
    ],
    'images': [
        'static/description/acs_hms_whatsapp_almightycs_cover.jpg',
    ],
    'installable': True,
    'application': False,
    'sequence': 2,
    'price': 16,
    'currency': 'USD',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
