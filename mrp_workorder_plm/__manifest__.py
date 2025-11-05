

{
    'name': 'PLM for workorder',
    'version': '1.0',
    'category': 'Manufacturing/Product Lifecycle Management (PLM)',
    'description': """
PLM for workorder.
=================================================
    """,
    'summary': 'PLM for workorder',
    'depends': [
        'mrp_workorder',
        'mrp_plm',
    ],
    'data': [
        'data/mrp_data.xml',
        'views/mrp_eco_views.xml',
    ],
    'installable': True,
    'auto_install': True,
}
