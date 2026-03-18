{
    'name': 'POS Fixed Discount',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Add fixed amount discount functionality to POS using percentage conversion',
    'description': """
        This module adds a fixed discount feature to the Point of Sale screen.

        Features:
        - Fixed amount discount button in Product Screen
        - Converts fixed amount to global percentage discount
        - Uses native Odoo line.set_discount() mechanism
        - Prevents backend crashes with proper rounding
    """,
    'author': 'Your Company',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale.assets': [
            'pos_fixed_discount/static/src/js/FixedDiscountButton.js',
            'pos_fixed_discount/static/src/js/OrderPatch.js',
            'pos_fixed_discount/static/src/xml/FixedDiscountButton.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}