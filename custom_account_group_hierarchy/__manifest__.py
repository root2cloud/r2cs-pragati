{
    'name': 'Account Group Manual Hierarchy',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Allow manual parent-child relationships in account groups',
    'description': '''
        This module removes the granularity constraint from account groups
        and allows manual parent selection for creating multi-level hierarchies.
    ''',
    'author': 'Root2cloud Solutions',
    'depends': ['account', 'ks_dynamic_financial_report'],
    'data': [
        'security/ir.model.access.csv',
        'data/report_data.xml',
        'views/account_group_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
