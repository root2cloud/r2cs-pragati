{
    'name': 'Vendor bills for tds reports',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'report/account_tds_report_views.xml',
        'views/tds_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
