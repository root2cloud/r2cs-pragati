# Part of Softhealer Technologies.
{
    "name": "POS Multi Warehouse",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "point of sale",
    "summary": "POS Multi Warehouse, POS warehouse location, Point Of Sale Multiple Warehouse, Point Of Sale Multiple warehouse, POS Multi Locations, POS Negative Selling, POS Sell Unreserved Product,POS Warehouse Management,point of sale Warehouse Management Odoo",
    "description": """By default in POS, only one warehouse can be selected. "POS Multi Warehouse" module helps to manage multiple warehouses within the POS (Point Of Sale) session.""",
    "version": "16.0.1",
    "license": "OPL-1",
    "depends": ["point_of_sale"],
    "application": True,
    "data": [
        "views/pos_config_views.xml",
        "views/res_config_settings_views.xml",
        "views/stock_warehouse_views.xml"
    ],
    'assets': {
        'point_of_sale.assets': [
            'sh_pos_multi_warehouse/static/src/scss/pos.scss',
            'sh_pos_multi_warehouse/static/src/js/**/*.js',
            'sh_pos_multi_warehouse/static/src/xml/**/*.xml',
        ],
    },
    "auto_install": False,
    "installable": True,
    "images": ['static/description/background.png', ],
    "price": "60",
    "currency": "EUR"
}
