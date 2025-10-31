{
    'name': 'Bills For Approval',
    'license': 'LGPL-3',
    'summary': 'Bills For Approval and Payment advice screens for Pragati Group',
    'depends': ['base','stock','product','approvals','purchase', 'account', 'purchase_requisition','base_accounting_kit','delivery'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'report/bills_approval_report.xml',
        'report/payment_advice_report.xml',
        'views/bills_approval_views.xml',
        'views/payment_advice_views.xml',
        'wizard/open_register_wizard_views.xml',
        ],
    'assets':{
            'web.assets_backend':[
                'bfa_and_pa_requests/static/js/preview_bills.js',
            ],
            },
}
