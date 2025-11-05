

{
    'name': "Stock enterprise",
    'version': "1.0",
    'category': 'Inventory/Inventory',
    'summary': "Advanced features for Stock",
    'description': """
Contains the enterprise views for Stock management
    """,
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/stock_enterprise_security.xml',
        'views/stock_move_views.xml',
        'views/stock_picking_map_views.xml',
        'report/stock_report_views.xml',
    ],
    'installable': True,
    'auto_install': ['stock'],
}
