
{
    'name': 'Accounting - MRP Subcontracting',
    'version': '1.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Add Subcontracting information in Cost Analysis Reports and Production Analysis',
    'description': """
Add Subcontracting information in Cost Analysis Report and The Production Analysis
""",
    'website': 'https://www.odoo.com/app/manufacturing',
    'depends': ['mrp_account_enterprise', 'mrp_subcontracting'],
    'data': [
        'report/mrp_cost_structure_report.xml',
        'report/mrp_report_views.xml',
    ],
    'installable': True,
    'auto_install': True,
}
