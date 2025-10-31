
{'name': "Contact Approval",
    'summary': """This module helps you manage contacts through the Approval manager's validation process""",
    'description': """The Odoo Contact Approval Module allows you to approve or cancel contacts through the Contacts
     Approval Manager. Only Approved contacts can be used in sales, purchasing, inventory, and invoice models.""",
    'depends': ['base', 'contacts', 'sale_management', 'purchase', 'stock', 'account'],
    'data': [
        'security/contact_approval_security.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
    ],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
