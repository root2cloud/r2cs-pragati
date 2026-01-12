# -*- coding: utf-8 -*-
{
    'name': "pos_extension",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'license': 'LGPL-3',

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        # 'report/report_invoice_in_pos_extend.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_extension/static/src/js/OrderSummary.js',
            'pos_extension/static/src/js/Receipt.js',
            'pos_extension/static/src/xml/OrderSummary.xml',
            'pos_extension/static/src/xml/OrderLineExtendInPos.xml',
            'pos_extension/static/src/xml/OrderLineTax.xml',
            'pos_extension/static/src/js/PaymentScreen.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
