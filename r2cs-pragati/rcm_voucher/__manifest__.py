{
    'name': 'RCM Voucher',
    'version': '1.0',
    'summary': 'Manage RCM Vouchers with automated TDS calculations',
    'sequence': 10,
    'description': """
        A module to manage Reverse Charge Mechanism (RCM) vouchers with features like:
        - Automated TDS calculations
        - Vendor service order fetching
        - Custom fields for financial and logistical management
    """,
    'author': 'Your Company',
    'category': 'Accounting',
    'website': 'https://yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'mail', 'service','stock'],
    'data': [
        'security/ir.model.access.csv',
        'report/rcm_voucher_report.xml',
        'data/rcm_voucher_sequence.xml',
        'views/rcm_voucher_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
