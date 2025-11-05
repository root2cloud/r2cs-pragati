# -*- coding: utf-8 -*-
#╔══════════════════════════════════════════════════════════════════╗
#║                                                                  ║
#║                ╔═══╦╗       ╔╗  ╔╗     ╔═══╦═══╗                 ║
#║                ║╔═╗║║       ║║ ╔╝╚╗    ║╔═╗║╔═╗║                 ║
#║                ║║ ║║║╔╗╔╦╦══╣╚═╬╗╔╬╗ ╔╗║║ ╚╣╚══╗                 ║
#║                ║╚═╝║║║╚╝╠╣╔╗║╔╗║║║║║ ║║║║ ╔╬══╗║                 ║
#║                ║╔═╗║╚╣║║║║╚╝║║║║║╚╣╚═╝║║╚═╝║╚═╝║                 ║
#║                ╚╝ ╚╩═╩╩╩╩╩═╗╠╝╚╝╚═╩═╗╔╝╚═══╩═══╝                 ║
#║                          ╔═╝║     ╔═╝║                           ║
#║                          ╚══╝     ╚══╝                           ║
#║               SOFTWARE DEVELOPED AND SUPPORTED BY                ║
#║          ALMIGHTY CONSULTING SOLUTIONS PRIVATE LIMITED           ║
#║                   COPYRIGHT (C) 2016 - TODAY                     ║
#║                   https://www.almightycs.com                     ║
#║                                                                  ║
#╚══════════════════════════════════════════════════════════════════╝
{
    'name' : 'Invoice Summary Report By AlmightyCS',
    'summary': 'Invoice Summary Report By AlmightyCS',
    'version': '1.0.1',
    'category': 'Accounting',
    'depends' : ['account'],
    'author': 'Almighty Consulting Solutions Pvt. Ltd.',
    'website': 'http://www.almightycs.com',
    'license': 'OPL-1',
    'description': """Invoice Summary Report By AlmightyCS""",
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/account_payment_views.xml',
        'views/account_view.xml',
        'views/invoice_summary_view.xml',
        'views/payment_register_views.xml',
        'reports/report_invoice_summary.xml',
    ],
    'images': [
        'static/description/acs_hms_insurance_almightycs_cover.jpg',
    ],
    'installable': True,
    'application': False,
    'sequence': 2,
    'price': 51,
    'currency': 'USD',

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: