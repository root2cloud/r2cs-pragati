{
    'name': 'MI & PR Requests',
    'license': 'LGPL-3',
    'summary': 'Material Indents and Purchase Requistions for Pragati Group',
    'depends': ['base','stock','product','approvals','purchase', 'account', 'purchase_requisition','base_accounting_kit','delivery'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'report/material_indent_report.xml',
        'report/purchase_request_report.xml',
        'data/data.xml',
        'views/material_indent_views.xml',
        'views/purchase_requisition_views.xml',
        'views/po_mrn_status.xml',
        ]
}
