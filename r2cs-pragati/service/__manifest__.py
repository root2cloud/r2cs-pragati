{
    'name': 'Service Custom Module',
    'license': 'LGPL-3',
    'summary': 'Service Management for Pragati Group',
    'depends': ['base','stock','product','approvals','purchase', 'account', 'purchase_requisition','base_accounting_kit','delivery'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'report/service_order_completion_report.xml',
        'report/service_order_report.xml',
        'data/data.xml',
        'data/mail_template.xml',
        'views/service_order_views.xml',
        'views/service_completion_views.xml',
        ]
}
