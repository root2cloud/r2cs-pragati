
{
    'name': 'MRP features for Quality Control',
    'version': '1.0',
    'category': 'Manufacturing/Quality',
    'sequence': 50,
    'summary': 'Quality Management with MRP',
    'depends': ['quality_control', 'mrp'],
    'description': """
    Adds workcenters to Quality Control
""",
    "data": [
        'security/quality_mrp.xml',
        'views/quality_views.xml',
        'views/mrp_production_views.xml',
        'report/worksheet_custom_report_templates.xml',
    ],
    'auto_install': True,
}
