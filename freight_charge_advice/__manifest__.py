{
    'name': 'Freight Charge Advice',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Module for managing Freight Charge Advice with multi-level approvals',
    'depends': ['base', 'mail', 'account','stock','product','approvals','purchase', 'account', 'purchase_requisition','base_accounting_kit','delivery','web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/freight_charge_advice_view.xml',
        'wizard/open_freight_register_wizard_views.xml',
        'report/freight_report.xml',

    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
