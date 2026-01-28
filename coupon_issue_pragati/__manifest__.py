{
    'name': 'Coupon Issue Management',
    'version': '1.0',
    'summary': 'Coupon Issue with 3-Level Approval Workflow',
    'category': 'Operations',
    'author': 'Pragati',
    'depends': [
        'base',
        'mail',
        'hr',
        'sale'

    ],
    'data': [

        'security/ir.model.access.csv',
        'reports/coupon_report.xml',
        'views/coupon_report_wizard.xml',
        'data/coupon_issue_sequence.xml',
        'views/coupon_issue_views.xml',
        'views/coupon_redeem_views.xml',

    ],
    'installable': True,
    'application': True,
}
