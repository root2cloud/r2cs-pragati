{
    'name': "Sale enterprise",
    'version': "1.0",
    'license': 'LGPL-3',
    'category': "Sales/Sales",
    'summary': "Advanced Features for Sale Management",
    'description': """
Contains advanced features for sale management
    """,
    'depends': ['sale'],
    'data': [
        'report/sale_report_views.xml',
    ],
    'installable': True,
    'auto_install': ['sale'],

    'assets': {
        'web.assets_backend': [
            'sale_enterprise/static/**/*',
        ],
    }
}
