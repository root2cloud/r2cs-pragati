{
    'name': 'Approvals - Purchase',
    'version': '1.0',
    'category': 'Human Resources/Approvals',
    'license': 'LGPL-3',
    'description': """
        This module adds to the approvals workflow the possibility to generate
        RFQ from an approval purchase request.
    """,
    'depends': ['approvals', 'purchase'],
    'data': [
        'data/approval_category_data.xml',
        'data/mail_templates.xml',
        'views/approval_category_views.xml',
        'views/approval_product_line_views.xml',
        'views/approval_request_views.xml',
    ],
    'demo': [
        'data/approval_demo.xml',
    ],
    'installable': True,
    'auto_install': True,
}
